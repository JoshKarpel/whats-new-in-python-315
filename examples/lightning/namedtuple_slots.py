from collections import namedtuple


class Point(namedtuple("Point", "x y")):
    __slots__ = ("label",)


point = Point(1, 2)
point.label = "origin-ish"
print(point, point.label)
