import tracemalloc

SIZE = 50 * 2**20

results = []
for f in (bytes, bytearray.take_bytes):
    tracemalloc.start()
    buffer = bytearray(SIZE)
    print(f"{f.__name__}: before, {len(buffer)=}")
    results.append(f(buffer))
    print(f"{f.__name__}: after,  {len(buffer)=}")
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"{f.__name__}: peak {peak // 2**20} MiB")
assert results[0] == results[1]
