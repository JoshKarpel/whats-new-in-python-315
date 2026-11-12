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

source = Countdown(1_000_000)
with ThreadPoolExecutor(3) as pool:
    taken = sum(pool.map(list, [source, source, source]), [])
print(f"GIL={sys._is_gil_enabled()}")
print(f"{len(taken) - len(set(taken)):,} duplicates")
