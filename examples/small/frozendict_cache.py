from functools import cache
from urllib.parse import parse_qsl

@cache
def search(filters):  # whatever keys the URL had
    print("cache miss...")
    return sorted(filters.items())

first = frozendict(parse_qsl("lang=python&sort=stars"))
again = frozendict(parse_qsl("sort=stars&lang=python"))
print(f"{search(first)=}")
print(f"{search(again)=}")  # same keys, another order
print(f"{search(dict(first))=}")
