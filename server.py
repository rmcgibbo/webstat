# EXAMPLE TORNADO/WEBSOCKET CODE
# http://blog.kagesenshi.org/2011/10/simple-websocket-push-server-using.html

import tornado.ioloop
import tornado.web
from tornado import websocket
import random
import os

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

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
    "login_url": "/login",
    "xsrf_cookies": True,
}

application = tornado.web.Application([
    (r"/", MainHandler),
    (r'/static/(.*)', tornado.web.StaticFileHandler, dict(path=settings['static_path'])),
    (r"/socket", ClientSocket),
    (r"/push", Announcer),
], **settings)

def poll_daemons():
    for socket in GLOBALS['sockets']:
        r = random.random()
        socket.write_message("Here's some data that I'm getting: %s" % r)
        print 'pushed %s' % r


if __name__ == "__main__":
    application.listen(9010)
    tornado.ioloop.PeriodicCallback(poll_daemons, 1000).start()
    tornado.ioloop.IOLoop.instance().start()
