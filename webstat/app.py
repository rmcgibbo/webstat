#!/usr/bin/env python
# -*- coding: utf-8 -*-
import daemon
import lockfile
import os
from zmq.eventloop import ioloop, zmqstream
import tornado.web
import tornado.options
import handlers
import utils
import models
import settings
import logging

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
    mylogger = logging.FileHandler('webstat.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    mylogger.setFormatter(formatter)

    default_logger = logging.getLogger('')

    # Add the handler
    default_logger.addHandler(mylogger)

    # # Remove the default stream handler
    # for handler in default_logger.handlers:
    #    if isinstance(handler, logging.StreamHandler):
    #        default_logger.removeHandler(handler)

    ioloop.install() # install zmq into the ioloop
    models.create_all()
    
    app = tornado.web.Application(routes, **config)
    # serve on port 8000, which is reverse proxied to port 80.
    app.listen(8000)

    # install the default daemon poller to trigger periodically
    tornado.ioloop.PeriodicCallback(handlers.poll_daemons,
        settings.daemon_poll_default_period_minutes * 60.0 * 1000.0,
        io_loop=tornado.ioloop.IOLoop.instance()).start()

    tornado.ioloop.IOLoop.instance().start()
