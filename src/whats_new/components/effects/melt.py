"""
The melt: the slide being left runs down the screen like wet paint, column by column, and slides off the bottom,
uncovering the arriving slide from the top down.

Each column sets off at its own moment and sags at its own pace, from noise that's smooth across neighbouring columns
with a little jitter of its own, so the leaving slide's top edge runs down in uneven drips rather than one line.
Those on the side the arriving slide comes from tend to go first, so the melt leans the way the slides travel.
As a column sags it stretches too, so each of its cells repeats down the screen, smeared, more the further it has run:
what's printed on it stays in order, but drawn out. Above the column's top edge the arriving slide shows, as it is.
Every column has run off the bottom by the end.
"""

import random
from dataclasses import dataclass
from math import floor

from counterweight.animation import between
from counterweight.elements import StyledGrapheme

from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.swipe import Direction

WAVELENGTH = 9
"""How many columns apart the noise's own values are, smoothed between: about how wide a drip is."""
STAGGER = 0.35
"""How much of the transition the columns' starts are spread over; each runs for the rest of it, or less."""
LEAN = 0.4
"""How much a column's start depends on how near it is to the side the arriving slide comes from, rather than noise."""
SMEAR = 1.5
"""How many times longer a column is drawn out by the time its top edge reaches the bottom."""


def noise(width: int, chance: random.Random) -> tuple[float, ...]:
    """
    A value from 0 to 1 for each of `width` columns: random values `WAVELENGTH` columns apart, eased into one
    another, so neighbouring columns are alike and drips are wider than a column.
    """
    knots = [chance.random() for _ in range(width // WAVELENGTH + 2)]

    def at(x: int) -> float:
        """Column `x`'s value, between the two knots either side of it."""
        knot, within = divmod(x / WAVELENGTH, 1)
        smooth = within * within * (3 - 2 * within)
        return knots[int(knot)] * (1 - smooth) + knots[int(knot) + 1] * smooth

    return tuple(at(x) for x in range(width))


@dataclass(frozen=True, slots=True)
class Drip:
    """When one column starts to run and when it has run off the bottom, as shares of the transition."""

    start: float
    end: float

    def run(self, progress: float) -> float:
        """How far down the stage the column's top edge has run, `progress` through: faster and faster, as paint runs."""
        return between(progress, self.start, self.end) ** 2


def drips(width: int, direction: Direction) -> tuple[Drip, ...]:
    """
    When each of `width` columns runs: starting within the first `STAGGER` of the transition, earlier on the side
    the arriving slide comes from and wherever the noise says, and done by the end, each at a pace of its own.
    """
    chance = random.Random(315)
    nearness = tuple((x if direction is Direction.NEXT else width - 1 - x) / max(width - 1, 1) for x in range(width))
    starts = tuple(
        STAGGER * ((1 - LEAN) * value + LEAN * (1 - near))
        for value, near in zip(noise(width, chance), nearness, strict=True)
    )
    return tuple(
        Drip(start=start, end=start + (1 - start) * (0.7 + 0.3 * value))
        for start, value in zip(starts, noise(width, chance), strict=True)
    )


def melt(leaving: Grid, arriving: Grid, direction: Direction) -> Frames:
    """
    The melt's frames. Until a column starts to run it's the leaving column as it is, and once it has run off the
    bottom it's the arriving one, which every column has by the end. Each column runs faster and faster on its own,
    as paint does, so the progress needs no easing.
    """
    width, height = dimensions(leaving)
    schedule = drips(width, direction)
    columns_before = tuple(zip(*leaving, strict=True)) if leaving else ()
    columns_after = tuple(zip(*arriving, strict=True)) if arriving else ()

    def column(x: int, progress: float) -> tuple[StyledGrapheme | None, ...]:
        """Column `x`, `progress` of the way through the transition: as much of it as has sagged, and drawn out."""
        run = schedule[x].run(progress)
        top = run * height
        stretch = 1 + SMEAR * run
        before, after = columns_before[x], columns_after[x]
        return tuple(after[y] if y < top else before[floor((y - top) / stretch)] for y in range(height))

    def frame(t: float) -> Grid:
        return tuple(zip(*(column(x, t) for x in range(width)), strict=True)) if width else leaving

    return frame
