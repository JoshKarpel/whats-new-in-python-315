import json
from functools import cache

config = json.loads(
    '{"name": "Ada", "tags": ["math", "poetry"]}',
    object_pairs_hook=frozendict,
    array_hook=tuple,
)
print(f"{config = }")
print(f"{json.dumps(config) = }")

@cache
def lookup(config, key):
    return config[key]

print(f"{lookup(config, 'tags') = }")
