# EXAMPLE TORNADO/WEBSOCKET CODE
# http://blog.kagesenshi.org/2011/10/simple-websocket-push-server-using.html

import tornado.ioloop
import tornado.web
from tornado.options import define, options
from tornado import websocket
from sqlalchemy.orm import scoped_session, sessionmaker
from models import *
import datetime
import os
import zmq
import random
import json
define("port", default=9010, help="run on the given port", type=int)

ctx = zmq.Context()
socket = ctx.socket(zmq.REQ)}
socket.connect('tcp://127.0.0.1:76215')
daemon = 'vsp-compute'
zmq_auth_key = ''.join([str(random.randint(0,9)) for i in range(20)])

GLOBALS={
    'sockets': []
}

class BaseHandler(tornado.web.RequestHandler):
   @property
   def db(self):
      return self.application.db
    
class MainHandler(BaseHandler):
    def get(self):
        self.render('client.html')

class ClientSocket(websocket.WebSocketHandler):
    def open(self):
        GLOBALS['sockets'].append(self)
        print "WebSocket opened"

    def on_close(self):
        print "WebSocket closed"
        GLOBALS['sockets'].remove(self)

class Announcer(BaseHandler):
    def get(self, *args, **kwargs):
        data = self.get_argument('data')
        for socket in GLOBALS['sockets']:
            print socket
            socket.write_message(data)
        self.write('Posted')

class DaemonPoller(BaseHandler):
   #@tornado.web.asynchronous
   def get(self, *args, **kwargs):
      pass

   @staticmethod
   def test(db):
      #sock.send(zmq_auth_key)
      #report = sock.recv_json()
      time = datetime.datetime.now()

      with open('dump.json') as f:
         report = json.load(f)

      for d in report['jobs'].itervalues():
         keys = ['status', 'priority', 'processors', 'nodes', 'user', 'error', 'name', 'job_id', 'n_nodes']
         sanitized = dict(((k, v) for k, v in d.iteritems() if k in keys))
         job = Job(**sanitized)
         job.time = time
         db.add(job)
         print d['queue']

      for d in report['nodes']:
         keys = ['name', 'state', 'load', 'n_procs', 'n_running']
         sanitized = dict(((k, v) for k, v in d.iteritems() if k in keys))
         node = Node(**sanitized)
         node.time = time

         # connect the node to the jobs
         for job_id in d['job_ids']:
            node.jobs.append(db.query(Job).filter_by(job_id=job_id, time=time).first())
         db.add(node)

      import IPython as ip
      ip.embed()
      db.flush()

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler),
                    (r'/static/(.*)', tornado.web.StaticFileHandler,
                     {'path': os.path.join(os.path.dirname(__file__), "static")}),
                    (r"/socket", ClientSocket),
                    (r"/push", Announcer)]
        settings = {
            "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            "login_url": "/login",
            "xsrf_cookies": True,
            }
        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = scoped_session(sessionmaker(bind=engine))
      

#def poll_daemons():
#    for socket in GLOBALS['sockets']:
#        r = random.random()
#        socket.write_message("Here's some data that I'm getting: %s" % r)
#        print 'pushed %s' % r


if __name__ == "__main__":
   #create the db
   create_all()

   tornado.options.parse_command_line()
   app = Application()
   app.listen(options.port)
   DaemonPoller.test(app.db)

   #tornado.ioloop.IOLoop.instance().start()
