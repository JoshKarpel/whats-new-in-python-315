"""
The flip: the stage is a card that turns over about an upright line down its middle, the slide being left on its
front and the one arriving on its back. It narrows to an edge as it turns, its nearer side drawn taller than its
farther in perspective, and darkens as it turns away from the viewer. Moving forward, its right side comes toward
the viewer; moving back, its left. The card eases into its turn and out of it, as something with weight does.
"""

from math import cos
from math import floor
from math import pi
from math import sin

from counterweight.elements import StyledGrapheme

from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.easing import ease_in_out
from whats_new.components.effects.cards import blank
from whats_new.components.effects.characters import backdrop_of
from whats_new.components.effects.shading import BLACK
from whats_new.components.effects.shading import shaded
from whats_new.components.swipe import Direction

DEPTH = 0.3
"""How much shorter the card's farther side draws than its nearer, edge on: more exaggerates the perspective."""
TURNED_AWAY = 5
"""How many of `SHADES` the card darkens by edge on, turned all the way from the viewer."""


def flip(leaving: Grid, arriving: Grid, direction: Direction) -> Frames:
    """
    The flip's frames. Turned not at all, the front fills the stage square on, so the first frame is the leaving
    picture; turned all the way over, the back does, so the last is the arriving picture.
    """
    width, height = dimensions(leaving)
    empty = blank(backdrop_of(leaving, arriving))
    middle_x, middle_y = width / 2, height / 2

    def frame(t: float) -> Grid:
        turned = ease_in_out(t) * pi
        is_front = turned < pi / 2
        face = leaving if is_front else arriving
        half = abs(cos(turned)) * middle_x
        # Which side is nearer: the one coming toward the viewer, which has crossed to the other side once past edge on.
        nearer = direction.value if is_front else -direction.value
        darkness = round(sin(turned) * TURNED_AWAY)

        def column(x: int) -> tuple[StyledGrapheme | None, ...]:
            across = (x + 0.5 - middle_x) / half if half > 0 else 2.0
            if abs(across) > 1:
                return (empty,) * height
            source = min(floor((across + 1) / 2 * width), width - 1)
            # The nearer side at full height, so nothing goes off the stage, and the farther shorter.
            scale = 1 - DEPTH * sin(turned) * (1 - across * nearer) / 2
            rows = (floor(middle_y + (y + 0.5 - middle_y) / scale) for y in range(height))
            return tuple(shaded(face[row][source], BLACK, darkness) if 0 <= row < height else empty for row in rows)

        return (
            tuple(zip(*(column(x) for x in range(width)), strict=True)) if width else tuple(() for _ in range(height))
        )

    return frame
