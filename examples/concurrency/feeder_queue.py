import queue

DONE = object()

def feed(items, q):
    for item in items:
        q.put(item)
    q.put(DONE)

def worker(q):
    for item in iter(q.get, DONE):
        handle(item)
    q.put(DONE)  # for the next worker
