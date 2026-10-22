"""
The vortex: the slide being left drains into the middle of the stage, every character spiralling inward,
turning faster the closer it gets, as water does down a plughole, and vanishing at the center.
The arriving slide's characters then pour out of the center the same way, still turning the same way round,
and unwind onto their places.

Each character's path is a logarithmic spiral around the middle, in polar coordinates taken as the stage looks
on screen (cells being taller than wide), so the swirl is round rather than squashed. Its radius eases over
the character's own part of the transition: going in, speeding up toward the plughole, and coming out, slowing
onto its place. A shaded cell, such as the inside of a code box, spirals too, carrying its color, so a box drains
away and pours back out with its text; only the backdrop stays put.
"""

import random
from dataclasses import dataclass
from math import atan2
from math import cos
from math import hypot
from math import log
from math import sin

from counterweight.animation import between
from counterweight.elements import StyledGrapheme
from counterweight.styles import UNSET
from counterweight.styles import AnyColor

from whats_new.components.crossing import CELL_ASPECT
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.easing import ease_in
from whats_new.components.easing import ease_out
from whats_new.components.effects.characters import backdrop_of
from whats_new.components.effects.characters import characters
from whats_new.components.effects.characters import drawn_over
from whats_new.components.effects.characters import emptied
from whats_new.components.swipe import Direction

SPIRAL = 0.42
"""How much of the transition each character takes to spiral between its place and the center."""
STAGGER = 0.08
"""How much of each half of the transition the characters' departures are spread over."""
OUTWARD = 0.48
"""How far through the transition the first arriving character leaves the center."""
TWIST = 1.6
"""How far a character turns, in radians, each time its distance from the center shrinks by a factor of e."""
CORE = 2.0
"""How close to the center, in columns, the turning stops speeding up, so a character there doesn't spin wildly."""


@dataclass(frozen=True, slots=True)
class Spiral:
    """
    One character's path between its place and the center `center` of the stage: `radius` out from it at `angle`,
    as the stage looks on screen. Inward, it leaves its place `begin` of the way through the transition
    and is gone once it reaches the center; outward, it appears there at `begin` and ends in its place.
    `twist` is how far it turns per factor of e its radius shrinks, its sign the way round it turns.
    """

    center: tuple[float, float]
    radius: float
    angle: float
    glyph: StyledGrapheme
    begin: float
    twist: float
    is_inward: bool

    def at(self, t: float) -> tuple[int, int, StyledGrapheme] | None:
        """Which cell the character is in `t` of the way through the transition, or `None` while it isn't showing."""
        spun = between(t, self.begin, self.begin + SPIRAL)
        is_hidden = spun >= 1.0 if self.is_inward else spun <= 0.0
        if is_hidden:
            return None
        out = (1 - ease_in(spun) if self.is_inward else ease_out(spun)) * self.radius
        angle = self.angle + self.twist * log((self.radius + CORE) / (out + CORE))
        x = self.center[0] + out * cos(angle) - 0.5
        y = self.center[1] + out * sin(angle) / CELL_ASPECT - 0.5
        return round(x), round(y), self.glyph


def spirals(
    grid: Grid, direction: Direction, is_inward: bool, start: float, seed: int, backdrop: AnyColor | UNSET
) -> tuple[Spiral, ...]:
    """
    Every cell of `grid` that moves on its spiral, each setting off at its own moment from `start`. Clockwise on screen
    moving to the next slide and anticlockwise moving back, the same way round in and out, so the arriving slide
    unwinds as the leaving one wound up.
    """
    width, height = dimensions(grid)
    center = width / 2, height / 2
    chance = random.Random(seed)
    turning = TWIST if direction is Direction.NEXT else -TWIST
    placed: list[Spiral] = []
    for found in characters(grid, backdrop).values():
        for (x, y), glyph in found:
            across, down = x + 0.5 - center[0], (y + 0.5 - center[1]) * CELL_ASPECT
            placed.append(
                Spiral(
                    center=center,
                    radius=hypot(across, down),
                    angle=atan2(down, across),
                    glyph=glyph,
                    begin=start + chance.random() * STAGGER,
                    twist=turning if is_inward else -turning,
                    is_inward=is_inward,
                )
            )
    return tuple(placed)


def vortex(leaving: Grid, arriving: Grid, direction: Direction) -> Frames:
    """
    The vortex's frames. Each draws the backdrop, then everything that moves showing where its spiral has reached,
    those arriving over those leaving, so a cell back in its place looks exactly as its slide draws it.
    """
    backdrop = backdrop_of(leaving, arriving)
    paths = (
        *spirals(leaving, direction, is_inward=True, start=0.0, seed=315, backdrop=backdrop),
        *spirals(arriving, direction, is_inward=False, start=OUTWARD, seed=316, backdrop=backdrop),
    )
    under, over = emptied(leaving, backdrop), emptied(arriving, backdrop)

    def frame(t: float) -> Grid:
        # The two backdrops look the same, so they change over only at the end, where the last frame has to be exact.
        behind = over if t >= 1 else under
        return drawn_over(behind, (place for path in paths if (place := path.at(t)) is not None), backdrop)

    return frame
