#!/usr/bin/env python

import tornado.ioloop
import tornado.web
import tornado.websocket

from gpiocrust import Header, OutputPin
from tornado.options import define, options

define("pin", default=8, help="output pin", type=int)
define("port", default=80, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode", type=bool)


class Button(object):
    def __init__(self):
        self._presses = set()
        self._watchers = set()

    @property
    def presses(self):
        return self._presses

    def add_press(self, press):
        self._presses.add(press)
        self._invoke_watchers("add", press)

    def discard_press(self, press):
        self._presses.discard(press)
        self._invoke_watchers("discard", press)

    def add_watcher(self, method):
        self._watchers.add(method)

    def _invoke_watchers(self, method=None, changed=None):
        for watcher in self._watchers:
            watcher(method, changed, self.presses)


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    connections = set()
    button = Button()

    def open(self):
        WebSocketHandler.connections.add(self)

    def on_message(self, is_pressed):
        button = WebSocketHandler.button
        if is_pressed == "yes":
            button.add_press(self)
        elif is_pressed == "no":
            button.discard_press(self)
        for connection in WebSocketHandler.connections:
            connection.write_message(str(len(button.presses)))

    def on_close(self):
        WebSocketHandler.button.discard_press(self)
        WebSocketHandler.connections.remove(self)


tornado.options.parse_command_line()

app = tornado.web.Application([
    (r"/", WebSocketHandler)
], debug=options.debug)

with Header() as header:
    finger = OutputPin(options.pin, value=False)

    @WebSocketHandler.button.add_watcher
    def update_pin(m, c, presses):
        if options.debug:
            print presses
        finger.value = len(presses) > 0

    try:
        app.listen(options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        pass
