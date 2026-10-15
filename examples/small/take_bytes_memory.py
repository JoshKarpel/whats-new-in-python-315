import tracemalloc

SIZE = 50 * 2**20

def copy():
    buffer = bytearray(SIZE)
    return bytes(buffer)

def take():
    buffer = bytearray(SIZE)
    return buffer.take_bytes()

for f in (copy, take):
    tracemalloc.start()
    f()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"{f.__name__:>4}: peak {peak / 2**20:.0f} MiB")
