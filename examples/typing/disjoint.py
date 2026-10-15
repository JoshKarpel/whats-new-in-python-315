from dataclasses import dataclass

@dataclass(slots=True)
class Point:
    x: float
    y: float

@dataclass(slots=True)
class Color:
    r: int
    g: int
    b: int

def draw(p: Point) -> None:
    if isinstance(p, Color):
        print("a colored point!")

class ColoredPoint(Point, Color):
    pass
