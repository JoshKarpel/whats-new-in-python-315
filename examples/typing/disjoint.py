class Point:
    __slots__ = ("x", "y")

class Color:
    __slots__ = ("hex",)

def draw(p: Point) -> None:
    if isinstance(p, Color):
        print("a colored point!")

class ColoredPoint(Point, Color): ...
