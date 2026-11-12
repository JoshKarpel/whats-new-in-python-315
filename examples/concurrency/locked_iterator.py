import threading
from concurrent.futures import ThreadPoolExecutor

class LockedIterator:
    def __init__(self, items):
        self.iterator = iter(items)
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            return next(self.iterator)

it = LockedIterator(rows())
with ThreadPoolExecutor(3) as pool:
    pool.map(consume, [it, it, it])
