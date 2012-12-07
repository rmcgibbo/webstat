#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
from july.web import run_server
from july.app import JulyApplication
from zmq.eventloop import ioloop, zmqstream
import tornado.web
import handlers
import utils

ROOT = os.path.abspath(os.path.dirname(__file__))

settings = dict(
    cookie_secret='secret',
    xsrf_cookies='secret',
    template_path=os.path.join(ROOT, 'templates'),
    static_path=os.path.join(ROOT, 'static'),
    static_url_prefix='/static/',
)

coffeefactory = utils.command_line_renderer_factory('coffee -cs')

class CoffeeHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        self.write(coffeefactory(open(os.path.join(ROOT, 'assets', args[0] + '.coffee'))))
        self.set_header("Content-Type", "text/javascript")

application = JulyApplication(debug=True, **settings)
application.add_handler(('/', handlers.MainHandler))
application.add_handler(('/socket', handlers.ClientSocket))
application.add_handler((r'/refresh', handlers.DaemonPoller))
application.add_handler((r'/static2/(.*).js', CoffeeHandler))

#: register an app
#: from myapp.handlers import myapp
#: application.register_app(myapp, url_prefix='/app')


if __name__ == '__main__':
    ioloop.install()
    run_server(application)
