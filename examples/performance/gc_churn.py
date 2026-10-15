import gc
import resource
import sys


class Node:
    __slots__ = ("other", "payload")

    def __init__(self):
        self.payload = bytearray(512)
        self.other = None


live = [[i] * 4 for i in range(400_000)]  # a long-lived heap
for _ in range(1_500_000):
    a, b = Node(), Node()
    a.other, b.other = b, a  # a cycle, garbage as soon as the loop moves on

peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
print(f"{sys.version.split()[0]:>7}: peak {peak:.0f} MiB, threshold {gc.get_threshold()}")
