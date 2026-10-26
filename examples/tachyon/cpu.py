import time

def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)

start = time.perf_counter()
fib(32)
print(f"fib(32) took {time.perf_counter() - start:.2f} s")
