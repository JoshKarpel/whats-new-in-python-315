"""
The cube: the two slides are neighbouring faces of a cube that turns a quarter of the way round, about an upright axis
through its middle. Moving to the next slide the cube turns to the left, so the leaving face squashes toward the left
edge as it turns away while the arriving face opens out from the right; moving back, the other way. Their shared edge
sweeps across the stage the way the slides travel.

Each frame projects the cube in perspective, a face's nearer side drawn larger than its farther, then stretches the
picture sideways so the cube's outline always spans the stage. Each column of the stage shows one column of whichever
face is in front of it, so a turning face drops columns as it squashes and repeats them as it opens out, and its far
side shrinks toward the middle row. A face darkens as it turns away from the viewer. A curve that overshoots turns the
cube past the arriving face, and a blank face (the cube's next side) peeks in before it turns back.
"""

from dataclasses import dataclass
from math import cos
from math import floor
from math import pi
from math import sin

from counterweight.elements import StyledGrapheme

from whats_new.components.crossing import SPACE
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.easing import Easing
from whats_new.components.effects.shading import BLACK
from whats_new.components.effects.shading import shaded
from whats_new.components.swipe import Direction

DISTANCE = 2.0
"""How far the viewer is from the cube's axis, in face widths: nearer exaggerates the perspective."""
TURNED_AWAY = 6
"""How many of `SHADES` a face darkens by when it's edge on, turned all the way from the viewer."""


@dataclass(frozen=True, slots=True)
class Face:
    """
    One face of the cube, turned `angle` radians from facing the viewer (positive to the right): where on screen
    its edges are, before the frame stretches the outline to fill the stage, given the viewer is `DISTANCE` away.
    Points on the face run across it from -1/2 at its left edge to 1/2 at its right, in face widths.
    """

    angle: float

    def depth(self, across: float) -> float:
        """How far from the viewer the point `across` the face is, from the cube's axis, toward the back."""
        return -cos(self.angle) / 2 + across * sin(self.angle)

    def screen(self, across: float) -> float:
        """Where on screen, sideways, the point `across` the face projects."""
        return (sin(self.angle) / 2 + across * cos(self.angle)) / (self.depth(across) + DISTANCE)

    @property
    def is_facing(self) -> bool:
        """
        Whether the viewer sees the face's front: whether its left edge projects left of its right, since seen from
        behind it projects back to front. Not the same as facing the viewer's direction, which a face nearly edge on,
        off to one side, can do while the viewer, a finite distance away, is behind it.
        """
        return self.screen(-0.5) < self.screen(0.5)

    def across(self, screen: float) -> float:
        """Which point across the face projects to `screen`: `screen`, inverted."""
        return (sin(self.angle) / 2 - screen * (DISTANCE - cos(self.angle) / 2)) / (
            screen * sin(self.angle) - cos(self.angle)
        )


@dataclass(frozen=True, slots=True)
class Column:
    """
    What a column of the stage shows in one frame: `cells`, one face's column top to bottom, already darkened,
    scaled `scale` times about the middle row (smaller toward the far side of a face).
    """

    cells: tuple[StyledGrapheme | None, ...]
    scale: float


def cube(leaving: Grid, arriving: Grid, direction: Direction, easing: Easing) -> Frames:
    """
    The cube's frames. Turned not at all, the leaving face fills the stage square on, each column its own and
    undarkened, so the first frame is the leaving picture; turned a quarter, the arriving face does, so the last is
    the arriving picture.
    """
    width, height = dimensions(leaving)
    blank: Grid = ((SPACE,) * width,) * height
    # The arriving face is the next one round from the leaving face, the way the cube turns.
    turn = direction.value
    pictures = {0: leaving, turn: arriving}
    # Each face's columns, darkened, as frames come to need them: a frame looks a whole column up rather than shading
    # each of its cells, which takes a third of a frame's time. Only a few shades of each column ever come up.
    darkened: dict[tuple[int, int, int], tuple[StyledGrapheme | None, ...]] = {}

    def face_column(index: int, source: int, darkness: int) -> tuple[StyledGrapheme | None, ...]:
        """Column `source` of face `index`'s picture, top to bottom, darkened `darkness` of `SHADES`."""
        key = (index, source, darkness)
        if (cells := darkened.get(key)) is None:
            cells = darkened[key] = tuple(shaded(row[source], BLACK, darkness) for row in pictures.get(index, blank))
        return cells

    def columns(t: float) -> tuple[Column, ...]:
        """What each column of the stage shows `t` of the way through the turn."""
        turned = easing(t) * pi / 2
        faces = {
            index: face for index in range(-2, 3) if (face := Face(angle=index * pi / 2 - turned * turn)).is_facing
        }
        # Left to right, each face starting where the one before it ends.
        in_order = sorted(faces.items(), key=lambda indexed: indexed[1].screen(-0.5))
        left, right = in_order[0][1].screen(-0.5), in_order[-1][1].screen(0.5)
        # How much wider the outline is than a face square on, which draws at its own size, row for row.
        stretch = (right - left) * (DISTANCE - 0.5)

        def column(x: int) -> Column:
            on_screen = left + (x + 0.5) / width * (right - left)
            # The last face starting left of the column, so rounding where two faces meet can't fall between them.
            index, face = next(
                (index, face)
                for index, face in reversed(in_order)
                if face.screen(-0.5) <= on_screen or index == in_order[0][0]
            )
            across = face.across(on_screen)
            return Column(
                cells=face_column(
                    index,
                    min(max(floor((across + 0.5) * width), 0), width - 1),
                    round((1 - cos(face.angle)) * TURNED_AWAY),
                ),
                scale=(DISTANCE - 0.5) / (face.depth(across) + DISTANCE) / stretch,
            )

        return tuple(column(x) for x in range(width))

    def frame(t: float) -> Grid:
        middle = height / 2
        drawn = [
            [
                column.cells[row] if 0 <= row < height else SPACE
                for row in (floor(middle + (y + 0.5 - middle) / column.scale) for y in range(height))
            ]
            for column in columns(t)
        ]
        return tuple(zip(*drawn, strict=True)) if drawn else tuple(() for _ in range(height))

    return frame
