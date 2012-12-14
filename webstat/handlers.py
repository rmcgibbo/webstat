import os
import time
import zmq
import logging
from datetime import timedelta
import simplejson as json
from zmq.eventloop import zmqstream
import tornado.web
import tornado.ioloop
from tornado.web import RequestHandler
from tornado import websocket

import utils
import settings
from models import *
import analytics
import memcached
from sqlalchemy.sql.expression import desc
from sqlalchemy.orm import scoped_session, sessionmaker


class IndexHandler(RequestHandler):
    def get(self):
        # serve public/index.html
        path = os.path.join(settings.public_path, 'index.html')
        with open(path) as f:
            self.write(f.read())
            

class Clusters(RequestHandler):
    def get(self, *args, **kwargs):
        response = []
        for daemon in settings.daemons:
            response.append({'name': daemon['name'], 'id': daemon['id'], 
                             'active': daemon['default']})

        self.write({'clusters': response})


class Procs(RequestHandler):
    def get(self, *args, **kwargs):
        cluster = db.query(Cluster).get(int(args[0]))
        if cluster is None:
            self.send_error(404)
        else:
            procs, time = analytics.procs_per_user(cluster)
            self.write({'procs': procs, 'time': time})


class Nodes(RequestHandler):
    def get(self, *args, **kwargs):
        cluster = db.query(Cluster).get(int(args[0]))
        if cluster is None:
            self.send_error(404)
        else:
            nodes, time = analytics.nodes_by_status(cluster)
            self.write({'nodes': nodes, 'time': time})


class FreeNodes(RequestHandler):
    def get(self, *args, **kwargs):
        cluster = db.query(Cluster).get(int(args[0]))
        if cluster is None:
            self.send_error(404)
        else:
            nodes = analytics.free_nodes(cluster)
            self.write({'data': nodes})


class History(RequestHandler):
    def get(self, *args, **kwargs):
        cluster = db.query(Cluster).get(int(args[0]))
        if cluster is None:
            self.send_error(404)
        else:
            timeseries = analytics.procs_per_user(cluster,
                        time_delta=timedelta(hours=int(args[1])))
            table, headings = analytics.tableify(timeseries)
            self.write({'table': table, 'headings': headings})
            


class AnnounceSocket(websocket.WebSocketHandler):
    """Handle the websocket connection with the browsers.
    All of the communication over the socket is JSON.
    
    The websocket is used for
    - A heartbeat, initialized by the browsers, that sends ping/pong messages.
    - Announcing a message to every client. This is used to tell them when
    we have new data.
    - Receiving requests from the clients to poll the daemons for new data.
    
    A lot of this class -- most of the classmethods -- could be refactored
    into a baseclass that might make our application specific logic cleaner
    and more obvious.
    """
    # keep track of all instances of this class. each instance corresponds to
    # a different browser
    __instances__ = []

    # this dict maps names that come in from the browser on the websocket
    # to the methods that get called.
    dispatch = {'ping': 'ping',
                'refresh': 'refresh'}

    @classmethod
    def _register(cls, instance):
        "Register a websocket -- Call me when a new instance is opened"
        cls.__instances__.append(instance)
        logging.info('N websocket clients: %d', len(cls.__instances__))

    @classmethod
    def _unregister(cls, instance):
        "Unregister a websocket -- call me when an instance is closed "
        cls.__instances__.remove(instance)

    def write_message(self, message):
        "override write_message to only take JSON"
        if not (isinstance(message, dict) and 'name' in message.keys()):
            raise ValueError("Websocket (%s) (type=%s) is not a dict or doesnt "
                "have the key 'name'" % (message, type(message)))

        super(AnnounceSocket, self).write_message(json.dumps(message))

    def open(self, *args, **kwargs):
        "Called by Tornado when a new socket is opened"
        logging.info("WebSocket opened")
        AnnounceSocket._register(self)

    def on_close(self):
        "Called by Tornado when a new socket is closed"
        logging.info("WebSocket closed")
        AnnounceSocket._unregister(self)

    @classmethod
    def announce(cls, message):
        """Send a message to every registered listener on the socket"""
        #json encode everything except strings
        logging.info("Annnouncing: %s", message)
        for socket in cls.__instances__:
            socket.write_message(message)

    def on_message(self, message):
        message = json.loads(message)
        name = message['name']
        method = getattr(self, self.__class__.dispatch[name])
        method(message)

    def ping(self, message):
        self.write_message({'name': 'pong'})

    def refresh(self, message):
        status = poll_daemons()
        self.write_message({'name': 'response', 'payload': 'Poll? %s' % status})
        logging.info('Q: Polled Daemons? A: %s', status)


# ########### ########### ########### ########### ########### ###########
#    Stuff for dealing with the interface to the cluster daemons
# ########### ########### ########### ########### ########### ###########
# this will get filled in with the zmq streams
DAEMON_STREAMS = []

# this is called both by a PeriodicCallback and by the user, via the websocket.
@utils.maxfrequency(timeout=settings.daemon_poll_min_period)
def poll_daemons():
    """Poll the daemons over zeromq. Guard against doing this too frequently
    with the decorator"""
    for sock in DAEMON_STREAMS:
        sock.send(settings.zmq_auth_keys)
    return True


def recv_from_daemon(stream, messages):
    "ZMQ callback when data is recieved from the daemons"
    
    logging.info('recieved data from daemon')
    for msg in messages:
        report = json.loads(msg)
        snapshot = Snapshot()
        cluster, _ = get_or_create(db, Cluster, name=stream.daemon['name'], id=stream.daemon['id'])
        add_jobs_from_dict(db, report['jobs'], snapshot, cluster)
        add_nodes_from_dict(db, report['nodes'], snapshot, cluster)
    db.commit()
    memcached.flush_all()

    AnnounceSocket.announce({'name': 'annoucement',
        'payload': 'refresh'})


# connect to the daemons over zmq
for i, daemon in enumerate(settings.daemons):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect('tcp://%s:%d' % (daemon['host'], daemon['port']))
    stream = zmqstream.ZMQStream(socket)
    stream.on_recv_stream(recv_from_daemon)
    stream.daemon = daemon
    DAEMON_STREAMS.append(stream)
