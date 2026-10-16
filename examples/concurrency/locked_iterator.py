import threading

class LockedIterator:
    def __init__(self, items):
        self.iterator = iter(items)
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            return next(self.iterator)
