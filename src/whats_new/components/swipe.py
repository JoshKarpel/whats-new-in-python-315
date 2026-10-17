"""
The slide transition: the slide being left and the one arriving, side by side, sliding across together, as spiel's
`Swipe` does, along whichever easing curve F3 picked.

Both slides are mounted for the length of the swipe. The one being left keeps its state (its run output, its edits),
since it continues under its own key, but stops being live, which moves focus to the arriving slide at once:
counterweight auto-focuses only on the render a component mounts, so waiting for the old slide to unmount would leave
nothing focused. It unmounts when the swipe ends.
"""

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

import waxy
from counterweight.components import Component
from counterweight.components import component
from counterweight.elements import Div
from counterweight.hooks import use_rects
from counterweight.styles import Style
from counterweight.styles.utilities import *

from whats_new.components.animation import use_progress_since
from whats_new.components.easing import EASINGS
from whats_new.components.easing import Easing

OFF = "off"
TRANSITIONS = (OFF, *EASINGS)
"""What F3 offers: no transition, then each easing curve, by name."""
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


def offsets(direction: Direction, eased: float, width: int) -> tuple[int, int]:
    """
    How many columns from the stage's left edge the leaving and arriving slides sit, `eased` of the way across
    a stage `width` wide. They're always exactly a width apart, so they never overlap or leave a gap between them,
    and an `eased` past 1 carries both past the end.
    """
    leaving = -round(direction.value * eased * width)
    return leaving, leaving + direction.value * width


@component
def stage(live: Component, swipe: Swipe | None) -> Div:
    """
    The `live` slide, and while `swipe` plays, the slide it replaced beside it. Each is keyed by its caller,
    which has to give every mounting of a slide a key of its own, or a slide returned to mid-swipe would continue
    the copy still leaving.
    """
    width = use_rects().content.width
    progress = use_progress_since(swipe, SWIPE)
    if swipe is None or progress >= 1.0:
        return Div(style=fill(1) | position_relative, children=(placed_at(0, live),))
    leaving, arriving = offsets(swipe.direction, swipe.easing(progress), width)
    return Div(
        style=fill(1) | position_relative | overflow_hidden,
        children=(placed_at(leaving, swipe.leaving), placed_at(arriving, live)),
    )


def placed_at(left: int, slide: Component) -> Component:
    """
    `placed`, keyed as `slide` is: siblings are matched by key or else by position, and the live slide moves
    from second to first as the swipe ends, so by position it would remount.
    """
    if slide.key is None:
        raise ValueError(f"a slide on the stage needs a key, so it continues across a swipe, but got {slide!r}")
    return placed(left, slide).with_key(slide.key)


STAGE_SIZE = Style(layout=waxy.Style(size_width=waxy.Percent(1.0), size_height=waxy.Percent(1.0)))
"""
The stage's whole size. Not `full`, which stretches a positioned box to fit between its insets, so a slide
partly off the stage would be squeezed into the part still on it, and its content would reflow.
"""


@component
def placed(left: int, slide: Component) -> Div:
    """`slide`, `left` columns from the stage's left edge, the stage's size wherever it sits."""
    return Div(style=position_absolute | inset_top(0) | inset_left(left) | STAGE_SIZE | col, children=(slide,))
