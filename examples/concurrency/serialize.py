import threading
import time
from concurrent.futures import ThreadPoolExecutor

def rows():
    for row in range(10_000):
        time.sleep(0)
        yield row

def consume(source):
    return sum(1 for _ in source)

with ThreadPoolExecutor(4) as pool:
    shared = threading.serialize_iterator(rows())
    print("serialize_iterator:", list(pool.map(consume, [shared] * 4)))

    copies = threading.concurrent_tee(rows(), 4)
    print("concurrent_tee:    ", list(pool.map(consume, copies)))
