#!/usr/bin/env python

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.escape

from gpiocrust import Header, OutputPin
from tornado.options import define, options

define("pin", default=8, help="output pin", type=int)
define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode", type=bool)


class Button(object):
    def __init__(self):
        self.presses = set()
        self._watchers = set()

    @property
    def is_pressed(self):
        return len(self.presses) > 0

    def has_changed_state(self):
        try:
            return self.is_pressed != self.latest_is_pressed
        except AttributeError:
            return True
        finally:
            self.latest_is_pressed = self.is_pressed

    def add_press(self, press):
        self.presses.add(press)
        self._invoke_watchers("add", press)

    def discard_press(self, press):
        self.presses.discard(press)
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
        self.id = self.get_argument("id")
        WebSocketHandler.connections.add(self)

    def on_message(self, is_pressing):
        cls = WebSocketHandler

        if int(is_pressing) == 1:
            cls.button.add_press(self)
        else:
            cls.button.discard_press(self)

        if cls.button.has_changed_state():
            is_unlocked = cls.button.is_pressed
            data = {
                "is_unlocked": is_unlocked
            }
            if is_unlocked:
                data["id"] = self.id
            for connection in cls.connections:
                connection.write_message(tornado.escape.json_encode(data))

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
