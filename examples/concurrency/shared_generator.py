import time
from concurrent.futures import ThreadPoolExecutor

def rows():
    for row in range(10_000):
        time.sleep(0)  # reading a file, a socket, ...
        yield row

def consume(source):
    count = 0
    try:
        for _ in source:
            count += 1
    except ValueError as error:
        return f"died after {count}: {error}"
    return f"took {count}"

source = rows()
with ThreadPoolExecutor(4) as pool:
    for result in pool.map(consume, [source] * 4):
        print(result)
