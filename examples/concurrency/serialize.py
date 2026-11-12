import threading
import time
from concurrent.futures import ThreadPoolExecutor

def rows():
    for row in range(10_000):
        time.sleep(0)
        yield row

def consume(source):
    return sum(1 for _ in source)

shared = threading.serialize_iterator(rows())
with ThreadPoolExecutor(3) as pool:
    counts = list(pool.map(consume, [shared, shared, shared]))
print(f"{counts=}")
print(f"{sum(counts)=}")
