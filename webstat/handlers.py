import zmq, json
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
   daemons = [{'host': 'vsp-compute'}],
   zmq_context = zmq.Context(),
   zmq_auth_key = '0'
)

db = scoped_session(sessionmaker(bind=engine))

# connect to the daemons over zmq
for d in GLOBALS['daemons']:
    socket = GLOBALS['zmq_context'].socket(zmq.REQ)
    socket.connect('tcp://%s:76215' % d['host'])
    d['socket'] = socket



class MainHandler(RequestHandler):
    def get(self):
        self.render('client.html')


class ClientSocket(websocket.WebSocketHandler):
    def open(self):
        GLOBALS['sockets'].append(self)
        print "WebSocket opened"
        push_data()

    def on_close(self):
        print "WebSocket closed"
        GLOBALS['sockets'].remove(self)


class DaemonPoller(RequestHandler):
    @tornado.web.asynchronous
    def get(self, *args, **kwargs):
        def poll():
            poll_daemons()
            push_data()
            self.finish()
        tornado.ioloop.IOLoop.instance().add_callback(poll)


def poll_daemons():
    print 'polling'
    for daemon in GLOBALS['daemons']:
        daemon['socket'].send(GLOBALS['zmq_auth_key'])
        report = daemon['socket'].recv_json()

        snapshot = Snapshot(time=datetime.datetime.now())
        cluster, _ = get_or_create(db, Cluster, name=daemon['host'])
        add_jobs_from_dict(db, report['jobs'], snapshot, cluster)
        add_nodes_from_dict(db, report['nodes'], snapshot, cluster)
    db.commit()

all = object() # sentinel
def push_data(socket=all):
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
