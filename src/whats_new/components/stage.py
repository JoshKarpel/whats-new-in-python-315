"""
Where the live slide shows, and the transition into it plays: a `Swipe` moves the slide being left and the live one
across together, and a `Crossing` draws its frames over the live slide, which shows as itself once it ends.
"""

from typing import assert_never

import waxy
from counterweight.components import Component
from counterweight.components import component
from counterweight.elements import Canvas
from counterweight.elements import Div
from counterweight.hooks import use_rects
from counterweight.styles import Style
from counterweight.styles.utilities import *

from whats_new.components.animation import use_progress_since
from whats_new.components.crossing import Crossing
from whats_new.components.crossing import Drawing
from whats_new.components.swipe import SWIPE
from whats_new.components.swipe import Swipe
from whats_new.components.swipe import offsets

type Playing = Swipe | Crossing


@component
def stage(live: Component, playing: Playing | None) -> Div:
    """
    The `live` slide, and while `playing` plays, the transition into it. The live slide is keyed by its caller,
    which has to give every mounting of a slide a key of its own, or a slide returned to mid-swipe would continue
    the copy still leaving.
    """
    width = use_rects().content.width
    progress = use_progress_since(playing, SWIPE if playing is None else playing.duration)
    if playing is None or progress >= 1.0:
        return Div(style=fill(1) | position_relative, children=(placed_at(0, live),))
    match playing:
        case Swipe(leaving=leaving, direction=direction, easing=easing):
            left, right = offsets(direction, easing(progress), width)
            return Div(
                style=fill(1) | position_relative | overflow_hidden,
                children=(placed_at(left, leaving), placed_at(right, live)),
            )
        case Crossing():
            return Div(
                style=fill(1) | position_relative | overflow_hidden,
                children=(
                    placed_at(0, live),
                    # Last, so it's drawn over the live slide.
                    Canvas(painter=Drawing(playing, progress), style=position_absolute | inset_top(0) | STAGE_SIZE),
                ),
            )
        case _ as unreachable:
            assert_never(unreachable)


def placed_at(left: int, slide: Component) -> Component:
    """
    `placed`, keyed as `slide` is: siblings are matched by key or else by position, and the live slide moves
    from second to first as a swipe ends, so by position it would remount.
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
