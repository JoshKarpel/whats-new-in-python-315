import copy
import pickle

MISSING = sentinel("MISSING")

print(f"{MISSING=} {bool(MISSING)=}")
print(f"{copy.deepcopy(MISSING) is MISSING=}")
print(f"{pickle.loads(pickle.dumps(MISSING)) is MISSING=}")

class Sub(type(MISSING)):
    pass
