import tornado.ioloop
import tornado.web
from tornado import websocket
import random

GLOBALS={
    'sockets': []
}

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

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

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/socket", ClientSocket),
    (r"/push", Announcer),
])

def poll_daemons():
    for socket in GLOBALS['sockets']:
        socket.write_message("Here's some data that I'm getting: %s" % random.random())
        print 'pushed'


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.PeriodicCallback(poll_daemons, 1000).start()
    tornado.ioloop.IOLoop.instance().start()
