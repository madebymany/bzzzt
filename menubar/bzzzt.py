#!/usr/bin/env python

import sys
import rumps
import requests
import datetime
import time
import functools


if len(sys.argv) > 1:
    server_url = sys.argv[1]
else:
    server_url = "http://raspberrypi.local:8888/"


class SimpleEventLoop(object):
    def __init__(self, interval=1):
        self._loop = rumps.Timer(self._execute_jobs, interval)
        self._jobs = set()

    @staticmethod
    def instance():
        if not hasattr(SimpleEventLoop, "_instance"):
            SimpleEventLoop._instance = SimpleEventLoop()
        return SimpleEventLoop._instance

    def start(self):
        self._loop.start()

    def stop(self):
        self._loop.stop()

    def add_timeout(self, deadline, callback):
        self._jobs.add((deadline, callback, datetime.datetime.now()))

    def _execute_jobs(self, sender):
        cleanup = []
        for j in self._jobs:
            deadline, callback, start = j
            elapsed = datetime.datetime.now() - start
            if elapsed > deadline:
                callback()
                cleanup.append(j)
        for j in cleanup:
            self._jobs.remove(j)


class BzzztApp(rumps.App):
    def __init__(self):
        super(BzzztApp, self).__init__("bzzzt")
        self.menu = ["Unlock door"]
        self.waiting = False

    @rumps.clicked("Unlock door")
    def open_door(self, sender):
        if self.waiting:
            return

        sender.title = "Unlocking..."
        self.waiting = True

        requests.post(server_url, params={
            "token": int(time.time())
        })
        SimpleEventLoop.instance().add_timeout(
            datetime.timedelta(seconds=3.0),
            functools.partial(self._end_wait, sender))

    def _end_wait(self, sender):
        sender.title = "Unlock door"
        self.waiting = False


if __name__ == "__main__":
    SimpleEventLoop.instance().start()
    BzzztApp().run()
