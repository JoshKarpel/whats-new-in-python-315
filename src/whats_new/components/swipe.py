"""
The swipe: the slide being left and the one arriving, side by side, sliding across together, as spiel's `Swipe` does,
along whichever easing curve F7 picked. `stage` plays it.

Both slides are mounted for the length of the swipe. The one being left keeps its state (its run output, its edits),
since it continues under its own key, but stops being live, which moves focus to the arriving slide at once:
counterweight auto-focuses only on the render a component mounts, so waiting for the old slide to unmount would leave
nothing focused. It unmounts when the swipe ends.
"""

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from counterweight.components import Component

from whats_new.components.easing import Easing

SWIPE = timedelta(seconds=0.75)
"""How long a swipe takes, and the grid's zoom, as long as spiel's swipe: long enough to see a curve's shape, short enough not to wait on."""


class Direction(Enum):
    """Which way the presenter moved, which is the way the slides travel: the next slide arrives from the right."""

    NEXT = 1
    PREVIOUS = -1


@dataclass(frozen=True, slots=True, eq=False)
class Swipe:
    """
    One transition: the slide being left, already keyed as it was while it was live, so it continues rather than
    remounting. Compared by identity, so each navigation starts a swipe of its own, even one that looks the same.
    """

    leaving: Component
    direction: Direction
    easing: Easing
    duration: timedelta


def offsets(direction: Direction, eased: float, width: int) -> tuple[int, int]:
    """
    How many columns from the stage's left edge the leaving and arriving slides sit, `eased` of the way across
    a stage `width` wide. They're always exactly a width apart, so they never overlap or leave a gap between them,
    and an `eased` past 1 carries both past the end.
    """
    leaving = -round(direction.value * eased * width)
    return leaving, leaving + direction.value * width
