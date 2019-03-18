import logging
import threading
import time

log = logging.getLogger(__name__)
no_op = lambda: time.time()

class BackgroundWorker(threading.Thread):
    def __init__(self, interval=60, func=no_op):
        threading.Thread.__init__(self)
        self.interval = interval
        self.running = True
        self.func = func

    def stop(self):
        self.running = False

    def run(self):
        while self.running:
            ret = self.func()
            log.info('Worker function returns: %s', ret)
            time.sleep(self.interval)
