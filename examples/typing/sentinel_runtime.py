import copy
import pickle

MISSING = sentinel("MISSING")

print(repr(MISSING), bool(MISSING))
print(copy.deepcopy(MISSING) is MISSING)
print(pickle.loads(pickle.dumps(MISSING)) is MISSING)

class Sub(type(MISSING)):
    pass
