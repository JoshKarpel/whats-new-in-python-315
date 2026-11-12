import queue
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

DONE = object()

def feed(items, q):
    for item in items:
        q.put(item)
    q.put(DONE)

def worker(q):
    for item in iter(q.get, DONE):
        handle(item)
    q.put(DONE)  # for the next worker

q = queue.Queue(maxsize=100)
Thread(target=feed, args=(rows(), q)).start()
with ThreadPoolExecutor(3) as pool:
    pool.map(worker, [q, q, q])
