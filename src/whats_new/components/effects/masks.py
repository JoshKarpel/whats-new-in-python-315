"""
Effects that uncover the arriving picture cell by cell, each cell at its own threshold of the eased progress,
and the thresholds that make `dissolve`, `wipe`, `iris` and `blinds`.
"""

import random
from collections.abc import Callable
from math import hypot

from whats_new.components.crossing import CELL_ASPECT
from whats_new.components.crossing import Effect
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.easing import Easing
from whats_new.components.swipe import Direction

type Thresholds = tuple[tuple[float, ...], ...]
"""For each cell, how far along the eased progress has to get, from 0 up to (not including) 1, to uncover it."""


def masked(thresholds: Callable[[int, int, Direction], Thresholds]) -> Effect:
    """
    An effect that uncovers the arriving picture cell by cell, each cell once the eased progress passes its threshold.
    A curve that goes past the end uncovers everything, and as it comes back covers the last cells again.
    """

    def prepare(leaving: Grid, arriving: Grid, direction: Direction, easing: Easing) -> Frames:
        width, height = dimensions(leaving)
        when = thresholds(width, height, direction)

        def frame(t: float) -> Grid:
            eased = easing(t)
            return tuple(
                tuple(a if w < eased else b for b, a, w in zip(before, after, at, strict=True))
                for before, after, at in zip(leaving, arriving, when, strict=True)
            )

        return frame

    return prepare


def scattered(width: int, height: int, direction: Direction) -> Thresholds:
    """Each cell at random, the same random on every run, so a dissolve plays the same way each time."""
    chance = random.Random(315)
    return tuple(tuple(chance.random() for _ in range(width)) for _ in range(height))


def across(width: int, height: int, direction: Direction) -> Thresholds:
    """Column by column, from the side the arriving slide comes from: the right, moving to the next slide."""
    columns = tuple((width - 1 - x if direction is Direction.NEXT else x) / width for x in range(width))
    return (columns,) * height


def circular(width: int, height: int, direction: Direction) -> Thresholds:
    """
    By distance from the center, as a circle on screen: opening out from the middle moving to the next slide,
    and closing in from the corners moving back.
    """
    center_x, center_y = width / 2, height / 2
    farthest = hypot(center_x, center_y * CELL_ASPECT) + 1

    def at(x: int, y: int) -> float:
        out = hypot(x + 0.5 - center_x, (y + 0.5 - center_y) * CELL_ASPECT) / farthest
        return out if direction is Direction.NEXT else 1 - out - 1 / farthest

    return tuple(tuple(at(x, y) for x in range(width)) for y in range(height))


SLAT = 8
"""How many columns wide each slat of `blinds` is."""


def slatted(width: int, height: int, direction: Direction) -> Thresholds:
    """`across`, within each slat at once."""
    columns = tuple((SLAT - 1 - x % SLAT if direction is Direction.NEXT else x % SLAT) / SLAT for x in range(width))
    return (columns,) * height


dissolve = masked(scattered)
wipe = masked(across)
iris = masked(circular)
blinds = masked(slatted)
