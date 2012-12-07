# EXAMPLE TORNADO/WEBSOCKET CODE
# http://blog.kagesenshi.org/2011/10/simple-websocket-push-server-using.html

import tornado.ioloop
import tornado.web
from tornado.options import define, options
from tornado import websocket
from sqlalchemy.orm import scoped_session, sessionmaker
from models import *
import analytics
import datetime
import os, json
import zmq
import random
define("port", default=9010, help="run on the given port", type=int)
ctx = zmq.Context()

# set up the sockets to connect to
# the daemons
daemons = [{'host': 'vsp-compute'}]
for d in daemons:
   socket = ctx.socket(zmq.REQ)
   socket.connect('tcp://%s:76215' % d['host'])
   d['socket'] = socket

#zmq_auth_key = ''.join([str(random.randint(0,9)) for i in range(20)])
zmq_auth_key = '0'
db = scoped_session(sessionmaker(bind=engine))

GLOBALS={
    'sockets': []
}
    
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('client.html')

class ClientSocket(websocket.WebSocketHandler):
    def open(self):
        GLOBALS['sockets'].append(self)
        print "WebSocket opened"

    def on_close(self):
        print "WebSocket closed"
        GLOBALS['sockets'].remove(self)

class Announcer(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        data = self.get_argument('data')
        for socket in GLOBALS['sockets']:
            print socket
            socket.write_message(data)
        self.write('Posted')

class DaemonPoller(tornado.web.RequestHandler):
   @tornado.web.asynchronous
   def get(self, *args, **kwargs):
      def poll():
         poll_daemons()
         push()
         self.finish()

      tornado.ioloop.IOLoop.instance().add_callback(poll)
      

def poll_daemons():
   for daemon in daemons:
      daemon['socket'].send(zmq_auth_key)
      report = daemon['socket'].recv_json()

      snapshot = Snapshot(time=datetime.datetime.now())
      cluster, _ = get_or_create(db, Cluster, name=daemon['host'])      
      add_jobs_from_dict(db, report['jobs'], snapshot, cluster)
      add_nodes_from_dict(db, report['nodes'], snapshot, cluster)

   db.commit()

def push():
   cluster = db.query(Cluster).first()
   procs_by_user = analytics.procs_by_user(db, cluster)
   for socket in GLOBALS['sockets']:
      socket.write_message(json.dumps(procs_by_user))


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler),
                    (r'/static/(.*)', tornado.web.StaticFileHandler,
                                      {'path': os.path.join(os.path.dirname(__file__), "static")}),
                    (r"/socket", ClientSocket),
                    (r"/refresh", DaemonPoller)]
        settings = {
            "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            "login_url": "/login",
            "xsrf_cookies": True,
            }
        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
   create_all()

   tornado.options.parse_command_line()
   app = Application()
   app.listen(options.port)
   tornado.ioloop.IOLoop.instance().start()
