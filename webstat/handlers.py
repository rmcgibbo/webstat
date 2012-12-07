import json
import zmq
from zmq.eventloop import zmqstream
import tornado.web
import tornado.ioloop
from tornado.web import RequestHandler
from tornado import websocket
import datetime

from models import *
import analytics
from sqlalchemy.orm import scoped_session, sessionmaker


GLOBALS = dict(
    sockets = [],
    daemon_hosts = ['vsp-compute'],
    daemon_streams = [], # will get filled in
    zmq_context = zmq.Context(),
    zmq_auth_key = '0'
)


db = scoped_session(sessionmaker(bind=engine))

class MainHandler(RequestHandler):
    def get(self):
        self.render('client.html')


class ClientSocket(websocket.WebSocketHandler):
    def open(self):
        GLOBALS['sockets'].append(self)
        print "WebSocket opened"
        push_data_to_clients()

    def on_close(self):
        print "WebSocket closed"
        GLOBALS['sockets'].remove(self)


class DaemonPoller(RequestHandler):
    def get(self, *args, **kwargs):
        poll_daemons()


def poll_daemons():
    print 'polling daemons'
    for sock in GLOBALS['daemon_streams']:
        sock.send(GLOBALS['zmq_auth_key'])


def recv_from_daemon(stream, messages):
    print 'recieved data from daemon'
    for msg in messages:
        report = json.loads(msg)
        snapshot = Snapshot(time=datetime.datetime.now())
        cluster, _ = get_or_create(db, Cluster, name=stream.host)
        add_jobs_from_dict(db, report['jobs'], snapshot, cluster)
        add_nodes_from_dict(db, report['nodes'], snapshot, cluster)
    db.commit()

    push_data_to_clients()


all = object() # sentinel
def push_data_to_clients(socket=all):
    cluster = db.query(Cluster).first()
    procs_by_user = analytics.procs_by_user(db, cluster)
    message = json.dumps({'name': 'procs_by_user',
                          'contents': {'cluster': cluster.name,
                                    'data': procs_by_user}})
    if socket == all:
        for socket in GLOBALS['sockets']:
            socket.write_message(message)
    else:
        socket.write_message(message)


# connect to the daemons over zmq
for i, host in enumerate(GLOBALS['daemon_hosts']):
    socket = GLOBALS['zmq_context'].socket(zmq.REQ)
    socket.connect('tcp://%s:76215' % host)
    stream = zmqstream.ZMQStream(socket)
    stream.on_recv_stream(recv_from_daemon)
    stream.host = host
    GLOBALS['daemon_streams'].append(stream)
