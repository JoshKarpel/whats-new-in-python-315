import sys

lazy import json
lazy from pathlib import Path

print(f"{"json" in sys.lazy_modules=}")
print(f"{globals()["json"]=}")
print(f"{"json" in sys.modules=}")

json.dumps({})
print(f"{"json" in sys.modules=}")
