import base64
import os
import sys
import timeit

blob = os.urandom(5 * 2**20)  # a 5 MB PDF, say
encoded = base64.b64encode(blob)

def ms(statement, number=10):
    return min(timeit.repeat(statement, number=number, repeat=5)) / number * 1000

print(sys.version.split()[0])
print(f"b64encode 5 MB: {ms(lambda: base64.b64encode(blob)):5.1f} ms")
print(f"b64decode 5 MB: {ms(lambda: base64.b64decode(encoded)):5.1f} ms")
print(f"b85encode 1 MB: {ms(lambda: base64.b85encode(blob[: 2**20]), 1):5.1f} ms")
