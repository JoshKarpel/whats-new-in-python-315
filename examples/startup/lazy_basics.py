import sys

lazy import json
lazy from pathlib import Path

print(f"{globals()["json"]=}")
print(f"{"json" in sys.modules=}")
print(json.dumps({"json": "imported"}))
print(f"{"json" in sys.modules=}")

print(f"{"pathlib" in sys.modules=}")
print(Path("pathlib") / "imported")
print(f"{"pathlib" in sys.modules=}")
