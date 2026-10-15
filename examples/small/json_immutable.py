import json
from functools import cache

def loads_immutable(s):
    return json.loads(s, object_pairs_hook=frozendict, array_hook=tuple)

config = loads_immutable('{"name": "Ada", "tags": ["math", "poetry"]}')
print(config)

@cache
def lookup(config, key):
    return config[key]

print(lookup(config, "tags"))
