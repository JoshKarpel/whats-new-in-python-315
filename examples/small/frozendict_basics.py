point = frozendict(x=1, y=2)

print(point == {"x": 1, "y": 2})  # like frozenset({1}) == {1}
print(isinstance(point, dict))
print(hash(point) == hash(frozendict(y=2, x=1)))
print(point | {"z": 3})

point["x"] = 5
