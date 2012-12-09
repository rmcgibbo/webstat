import os
import time
import zmq
import logging
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


class CoffeeHandler(tornado.web.RequestHandler):
    """Handler to compile coffeescript on the fly into JS and then serve it
    This is slow, but good for development.

    With some caching it could be faster?
    """
    def get(self, *args, **kwargs):
        with open(os.path.join(settings.assets_path, args[0] + '.coffee')) as f:
            self.write(utils.coffeefactory(f))

        self.set_header("Content-Type", "text/javascript")
        self.finish()


class MainHandler(RequestHandler):
    def get(self):
        self.render('client.html')


class Client2Handler(RequestHandler):
    def get(self):
        with open('webstat/assets/client2.html') as f:
            self.write(f.read())
        

class ProcsPerUserHandler(RequestHandler):
    def get(self, *args, **kwargs):
        cluster = db.query(Cluster).first()
        procs_per_user, time = analytics.procs_per_user(cluster)
        self.write({'cluster': cluster.name, 'data': procs_per_user,
                    'time': time.isoformat()})


class NodesByStatusHandler(RequestHandler):
    def get(self, *args, **kwargs):
        cluster = db.query(Cluster).first()
        nodes_by_status, time = analytics.nodes_by_status(cluster)
        self.write({'cluster': cluster.name, 'data': nodes_by_status,
                    'time': time.isoformat()})


class AnnounceSocket(websocket.WebSocketHandler):
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
        cluster, _ = get_or_create(db, Cluster, name=stream.host)
        add_jobs_from_dict(db, report['jobs'], snapshot, cluster)
        add_nodes_from_dict(db, report['nodes'], snapshot, cluster)
    db.commit()
    memcached.flush_all()

    AnnounceSocket.announce({'name': 'annoucement',
        'payload': 'refresh'})


# connect to the daemons over zmq
for i, host in enumerate(settings.daemon_hosts):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect('tcp://%s:%d' % (host, settings.zeromq_port))
    stream = zmqstream.ZMQStream(socket)
    stream.on_recv_stream(recv_from_daemon)
    stream.host = host
    DAEMON_STREAMS.append(stream)
