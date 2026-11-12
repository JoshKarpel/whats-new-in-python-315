point = frozendict(x=1, y=2)

print(f"{point == {"x": 1, "y": 2}=}")  # like frozenset({1}) == {1}
print(f"{isinstance(point, dict)=}")
print(f"{hash(point) == hash(frozendict(y=2, x=1))=}")
print(f"{point | {"z": 3}=}")

point["x"] = 5
