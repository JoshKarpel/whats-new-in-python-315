import sys
from concurrent.futures import ThreadPoolExecutor

class Countdown:
    def __init__(self, n):
        self.i, self.n = 0, n

    def __iter__(self):
        return self

    def __next__(self):
        i = self.i
        if i >= self.n:
            raise StopIteration
        self.i = i + 1
        return i

def consume(source):
    return list(source)

source = Countdown(1_000_000)
with ThreadPoolExecutor(4) as pool:
    items = [item for taken in pool.map(consume, [source] * 4) for item in taken]

print("free-threaded" if not sys._is_gil_enabled() else "GIL")
print(f"{len(items):,} items, {len(items) - len(set(items)):,} duplicates")
