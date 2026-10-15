import threading

class LockedIterator:
    def __init__(self, iterable):
        self.iterator = iter(iterable)
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            return next(self.iterator)
