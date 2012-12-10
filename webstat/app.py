#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
from zmq.eventloop import ioloop, zmqstream
import tornado.web
import tornado.options
import handlers
import utils
import models
import settings

ROOT = os.path.abspath(os.path.dirname(__file__))

config = dict(
    cookie_secret='secret',
    xsrf_cookies='secret',
    debug=True,
)

routes = [
    (r'/(favicon\.ico)', tornado.web.StaticFileHandler, {'path': settings.public_path}),
    (r'/(application\.css)', tornado.web.StaticFileHandler, {'path': settings.public_path}),
    (r'/(application\.js)', tornado.web.StaticFileHandler, {'path': settings.public_path}),
    (r'/', handlers.IndexHandler),
    (r'/announce', handlers.AnnounceSocket),
    (r'/clusters', handlers.Clusters),
    (r'/cluster/(\d+)/procs', handlers.Procs),
    (r'/cluster/(\d+)/nodes', handlers.Nodes),
    (r'/cluster/(\d+)/history/(\d+)', handlers.History),
    (r'/cluster/(\d+)/freenodes', handlers.FreeNodes),
]

if __name__ == '__main__':
    tornado.options.parse_command_line()
    ioloop.install() # install zmq into the ioloop
    models.create_all()
    
    app = tornado.web.Application(routes, **config)
    app.listen(8000)

    # install the default daemon poller
    tornado.ioloop.PeriodicCallback(handlers.poll_daemons,
        settings.daemon_poll_default_period_minutes * 60.0 * 1000.0,
        io_loop = tornado.ioloop.IOLoop.instance()).start()

    tornado.ioloop.IOLoop.instance().start()
