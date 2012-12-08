import json
import zmq
from zmq.eventloop import zmqstream
import tornado.web
import tornado.ioloop
from tornado.web import RequestHandler
from tornado import websocket

import settings
from models import *
import analytics
from sqlalchemy.orm import scoped_session, sessionmaker

# this will get filled in with the zmq streams
DAEMON_STREAMS = []


class MainHandler(RequestHandler):
    def get(self):
        self.render('client.html')


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

class DaemonPoller(RequestHandler):
    def get(self, *args, **kwargs):
        poll_daemons()


def poll_daemons():
    print 'polling daemons'
    for sock in DAEMON_STREAMS:
        sock.send(settings.zmq_auth_keys)


def recv_from_daemon(stream, messages):
    print 'recieved data from daemon'
    for msg in messages:
        print 'message recieved'
        report = json.loads(msg)  
        snapshot = Snapshot()
        print snapshot
        cluster, _ = get_or_create(db, Cluster, name=stream.host)
        add_jobs_from_dict(db, report['jobs'], snapshot, cluster)
        add_nodes_from_dict(db, report['nodes'], snapshot, cluster)
    db.commit()


# connect to the daemons over zmq
for i, host in enumerate(settings.daemon_hosts):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect('tcp://%s:76215' % host)
    stream = zmqstream.ZMQStream(socket)
    stream.on_recv_stream(recv_from_daemon)
    stream.host = host
    DAEMON_STREAMS.append(stream)


