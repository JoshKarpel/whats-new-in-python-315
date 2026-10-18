"""
What F6 offers: no transition, one of the effects, by name, or a different one at random on every move.
Every effect follows whichever easing curve F7 picked, at whichever speed F8 picked.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from whats_new.components.crossing import Effect
from whats_new.components.effects.crash import crash
from whats_new.components.effects.cube import cube
from whats_new.components.effects.curl import curl
from whats_new.components.effects.decay import decay
from whats_new.components.effects.diff import diff
from whats_new.components.effects.garbage import garbage
from whats_new.components.effects.gravity import gravity
from whats_new.components.effects.lazy_import import lazy_import
from whats_new.components.effects.masks import blinds
from whats_new.components.effects.masks import dissolve
from whats_new.components.effects.masks import iris
from whats_new.components.effects.masks import wipe
from whats_new.components.effects.melt import melt
from whats_new.components.effects.morph import morph
from whats_new.components.effects.pixelate import pixelate
from whats_new.components.effects.rain import rain
from whats_new.components.effects.raindrops import raindrops
from whats_new.components.effects.ripple import ripple
from whats_new.components.effects.sampling import sampling
from whats_new.components.effects.shatter import shatter
from whats_new.components.effects.slots import slots
from whats_new.components.effects.snake import snake
from whats_new.components.effects.sort import sort
from whats_new.components.effects.swap import swap
from whats_new.components.effects.threads import threads
from whats_new.components.effects.typewriter import typewriter
from whats_new.components.effects.vortex import vortex
from whats_new.components.swipe import SWIPE

OFF = "off"
RANDOM = "random"


@dataclass(frozen=True, slots=True)
class Swiped:
    """The two slides, both live, sliding across together (see `swipe`)."""


@dataclass(frozen=True, slots=True)
class Crossed:
    """An effect drawn from pictures of the two slides (see `crossing`), lasting `duration`."""

    effect: Effect
    duration: timedelta


type Transition = Swiped | Crossed

TRANSITIONS: frozendict[str, Transition] = frozendict(
    {
        "swipe": Swiped(),
        # Each lasts as long as it takes to follow: those that move every character, or play out in phases,
        # take two to four times as long as a swipe.
        "dissolve": Crossed(effect=dissolve, duration=SWIPE),
        "wipe": Crossed(effect=wipe, duration=SWIPE),
        "iris": Crossed(effect=iris, duration=SWIPE),
        "blinds": Crossed(effect=blinds, duration=SWIPE),
        "morph": Crossed(effect=morph, duration=SWIPE * 2),
        "gravity": Crossed(effect=gravity, duration=SWIPE * 2),
        "sort": Crossed(effect=sort, duration=SWIPE * 3),
        "vortex": Crossed(effect=vortex, duration=SWIPE * 2),
        "swap": Crossed(effect=swap, duration=SWIPE * 2),
        "typewriter": Crossed(effect=typewriter, duration=SWIPE * 3),
        "diff": Crossed(effect=diff, duration=SWIPE * 3),
        "crash": Crossed(effect=crash, duration=SWIPE * 4),
        "lazy": Crossed(effect=lazy_import, duration=SWIPE * 3),
        "rain": Crossed(effect=rain, duration=SWIPE * 2),
        "decay": Crossed(effect=decay, duration=SWIPE * 2),
        "slots": Crossed(effect=slots, duration=SWIPE * 2),
        "pixelate": Crossed(effect=pixelate, duration=SWIPE * 3),
        "curl": Crossed(effect=curl, duration=SWIPE * 2),
        "cube": Crossed(effect=cube, duration=SWIPE),
        "shatter": Crossed(effect=shatter, duration=SWIPE * 2),
        "melt": Crossed(effect=melt, duration=SWIPE * 2),
        "gc": Crossed(effect=garbage, duration=SWIPE * 3),
        "sampling": Crossed(effect=sampling, duration=SWIPE * 2),
        "threads": Crossed(effect=threads, duration=SWIPE * 3),
        "ripple": Crossed(effect=ripple, duration=SWIPE * 2),
        "raindrops": Crossed(effect=raindrops, duration=SWIPE * 2),
        "snake": Crossed(effect=snake, duration=SWIPE * 3),
    }
)

OFFERED = (OFF, *TRANSITIONS, RANDOM)
"""Every name F6 offers, in the order it lists them."""

type Choose = Callable[[tuple[Transition, ...]], Transition]
"""How `random` picks one of the transitions, such as `random.choice`."""


def transition_for(name: str, choose: Choose) -> Transition | None:
    """The transition a move plays with `name` picked, or `None` for `off`: for `random`, what `choose` picks."""
    if name == RANDOM:
        return choose(tuple(TRANSITIONS.values()))
    return TRANSITIONS.get(name)


SPEEDS: frozendict[str, float] = frozendict({"0.25x": 0.25, "0.5x": 0.5, "1x": 1.0, "1.5x": 1.5, "2x": 2.0})
"""What F8 offers: how many times faster than its own duration a transition plays, and the grid's zoom with it."""
SPEED = "1x"
