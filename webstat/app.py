#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
from zmq.eventloop import ioloop, zmqstream
import tornado.web
import tornado.options
import handlers
import utils
import models

ROOT = os.path.abspath(os.path.dirname(__file__))

settings = dict(
    cookie_secret='secret',
    xsrf_cookies='secret',
    template_path=os.path.join(ROOT, 'templates'),
    static_path=os.path.join(ROOT, 'static'),
    static_url_prefix='/static/',
)

handlers = [
    (r'/', handlers.MainHandler),
    ('/announce', handlers.AnnounceSocket),
    (r'/procs', handlers.ProcsPerUserHandler),
    (r'/nodes', handlers.NodesByStatusHandler),
    (r'/assets/(.*).js', handlers.CoffeeHandler),
    (r'/client2.html', handlers.Client2Handler),

]

if __name__ == '__main__':
    tornado.options.parse_command_line()
    ioloop.install() # install zmq into the ioloop
    models.create_all()
    
    app = tornado.web.Application(handlers, **settings)
    app.listen(8000)
    tornado.ioloop.IOLoop.instance().start()
