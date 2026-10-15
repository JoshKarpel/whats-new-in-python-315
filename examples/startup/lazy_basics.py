import sys

lazy import json
lazy from pathlib import Path

print("json" in sys.lazy_modules)
print(repr(globals()["json"]))
print("json" in sys.modules)

json.dumps({})
print("json" in sys.modules)
