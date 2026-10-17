from contextlib import contextmanager

@contextmanager
def tag(name):
    print(f"<{name}>")
    yield
    print(f"</{name}>")

@tag("numbers")
def numbers():
    print("  yielding 1")
    yield 1
    print("  yielding 2")
    yield 2

print(list(numbers()))
