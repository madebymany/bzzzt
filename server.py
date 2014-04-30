#!/usr/bin/env python

import tornado.ioloop
import tornado.web
import os
import functools
import datetime

from gpiocrust import Header, OutputPin
from tornado.options import define, options

define("pin", default=8, help="output pin", type=int)
define("press_duration", default=3.0, help="output pin", type=float)
define("port", default=80, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode", type=bool)


class Presses(object):
    def __init__(self):
        self._presses = set()
        self._watchers = set()

    def add(self, item):
        self._presses.add(item)
        self._invoke_watchers("add", item)

    def discard(self, item):
        self._presses.discard(item)
        self._invoke_watchers("discard", item)

    def add_watcher(self, method):
        self._watchers.add(method)

    def _invoke_watchers(self, method=None, changed=None):
        for watcher in self._watchers:
            watcher(method, changed)

    def __repr__(self):
        return repr(self._presses)

    def __len__(self):
        return len(self._presses)


class MainHandler(tornado.web.RequestHandler):
    @property
    def button_presses(self):
        return self.application.button_presses

    def get(self):
        self.render("index.html")

    def post(self):
        token = self.get_argument("token")
        is_pressed = self.get_argument("is_pressed", None)
        if is_pressed == "yes":
            self.button_presses.add(token)
        elif is_pressed == "no":
            self.button_presses.discard(token)
        else:
            self.button_presses.add(token)
            tornado.ioloop.IOLoop.instance().add_timeout(
                datetime.timedelta(seconds=options.press_duration),
                functools.partial(self.button_presses.discard, token))


tornado.options.parse_command_line()

app = tornado.web.Application([
    (r"/", MainHandler)
], debug=options.debug)

with Header() as header:
    finger = OutputPin(options.pin, value=False)
    app.button_presses = Presses()

    @app.button_presses.add_watcher
    def update_pin(method, changed):
        if options.debug:
            print app.button_presses
        finger.value = len(app.button_presses) > 0

    try:
        app.listen(options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        pass
