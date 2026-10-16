from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

@dataclass
class Color:
    hex: str

def draw(p: Point) -> None:
    if isinstance(p, Color):
        print("a colored point!")

class ColoredPoint(Point, Color): ...
