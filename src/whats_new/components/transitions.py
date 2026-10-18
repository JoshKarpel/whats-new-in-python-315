"""
What F6 offers: no transition, a different one at random on every move, or one of the effects, by name.
What F7 offers the grid the same way: none, one at random each time it opens or closes, or one by name,
in two groups, each of which can be picked to play one of it at random: the grid's own transitions, and F6's effects
drawn from pictures.
Every one plays at whichever speed F8 picked, following the curve that suits it (see `easing`).
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from whats_new.components.crossing import Effect
from whats_new.components.crossing import GridEffect
from whats_new.components.effects.crash import crash
from whats_new.components.effects.cube import cube
from whats_new.components.effects.curl import curl
from whats_new.components.effects.deal import deal
from whats_new.components.effects.decay import decay
from whats_new.components.effects.expose import expose
from whats_new.components.effects.flip import flip
from whats_new.components.effects.fold import fold
from whats_new.components.effects.garbage import garbage
from whats_new.components.effects.gravity import gravity
from whats_new.components.effects.lazy_import import lazy_import
from whats_new.components.effects.masks import blinds
from whats_new.components.effects.masks import dissolve
from whats_new.components.effects.masks import iris
from whats_new.components.effects.masks import wipe
from whats_new.components.effects.melt import melt
from whats_new.components.effects.morph import morph
from whats_new.components.effects.rain import rain
from whats_new.components.effects.ripples import ripples
from whats_new.components.effects.scale import scale
from whats_new.components.effects.shatter import shatter
from whats_new.components.effects.slice import sliced
from whats_new.components.effects.slots import slots
from whats_new.components.effects.swap import swap
from whats_new.components.effects.threads import threads
from whats_new.components.effects.typewriter import typewriter
from whats_new.components.effects.unpack import unpack
from whats_new.components.effects.vortex import vortex
from whats_new.components.swipe import SWIPE

OFF = "off"
RANDOM = "random"
AHEAD: frozendict[str, str] = frozendict(
    {OFF: "no transition: cut straight to it", RANDOM: "a different one each time"}
)
"""The names F6 and F7 list ahead of their transitions, and what their pickers say about each."""


@dataclass(frozen=True, slots=True)
class Swiped:
    """The two slides, both live, sliding across together (see `swipe`). `description` is what F6's picker says."""

    description: str


@dataclass(frozen=True, slots=True)
class Crossed:
    """
    An effect drawn from pictures of the two slides (see `crossing`), lasting `duration`.
    `description` is what F6's picker says.
    """

    effect: Effect
    duration: timedelta
    description: str


type Transition = Swiped | Crossed

TRANSITIONS: frozendict[str, Transition] = frozendict(
    {
        "swipe": Swiped("both slides slide across together"),
        # Each lasts as long as it takes to follow: those that move every character, or play out in phases,
        # take two to six times as long as a swipe.
        "dissolve": Crossed(dissolve, SWIPE, "cell by cell, at random"),
        "wipe": Crossed(wipe, SWIPE, "column by column, across"),
        "iris": Crossed(iris, SWIPE, "a circle opening from the middle"),
        "blinds": Crossed(blinds, SWIPE, "a wipe across every slat at once"),
        "morph": Crossed(morph, SWIPE * 2, "each character flies to its match"),
        "gravity": Crossed(gravity, SWIPE * 2, "falls away, then stacks up from the floor"),
        "vortex": Crossed(vortex, SWIPE * 2, "down a plughole, and back out"),
        "swap": Crossed(swap, SWIPE * 2, "shared characters hop, the rest decay"),
        "typewriter": Crossed(typewriter, SWIPE * 3, "backspaced away, then typed in"),
        "crash": Crossed(crash, SWIPE * 4, "glitches, segfaults and reboots"),
        "lazy": Crossed(lazy_import, SWIPE * 6, "PEP 810: proxies resolve as they're used"),
        "rain": Crossed(rain, SWIPE * 4, "digital rain, as in The Matrix"),
        "decay": Crossed(decay, SWIPE * 2, "crumbles to dust, then builds back up"),
        "slots": Crossed(slots, SWIPE * 2, "a split-flap departure board"),
        "curl": Crossed(curl, SWIPE * 2, "peels away like a turned page"),
        "cube": Crossed(cube, SWIPE, "a quarter turn of a cube"),
        "shatter": Crossed(shatter, SWIPE * 2, "cracks like glass and falls away"),
        "melt": Crossed(melt, SWIPE * 2, "runs down the screen like wet paint"),
        "gc": Crossed(garbage, SWIPE * 3, "marks what's reachable, sweeps the rest"),
        "threads": Crossed(threads, SWIPE * 3, "free threads race to repaint the rows"),
        "ripples": Crossed(ripples, SWIPE * 2, "drops whose ripples run together"),
    }
)

DESCRIBED: frozendict[str, str] = AHEAD | {name: transition.description for name, transition in TRANSITIONS.items()}
"""Every name F6 offers, in the order it lists them, and what its picker says about each."""
OFFERED = tuple(DESCRIBED)

type Choose = Callable[[tuple[Transition, ...]], Transition]
"""How `random` picks one of the transitions, such as `random.choice`."""


def transition_for(name: str, choose: Choose) -> Transition | None:
    """The transition a move plays with `name` picked, or `None` for `off`: for `random`, what `choose` picks."""
    if name == RANDOM:
        return choose(tuple(TRANSITIONS.values()))
    return TRANSITIONS.get(name)


@dataclass(frozen=True, slots=True)
class Zoomed:
    """
    The grid zooming (see `grid`): out from the selected slide as it opens, and back in to it as it closes.
    `description` is what F7's picker says.
    """

    description: str


@dataclass(frozen=True, slots=True)
class Tiled:
    """
    A grid effect drawn from pictures of the slide and the grid, knowing where each thumbnail is (see `crossing`),
    lasting `duration`. `description` is what F7's picker says.
    """

    effect: GridEffect
    duration: timedelta
    description: str


type GridTransition = Zoomed | Tiled | Crossed
"""
How the grid opens and closes: zooming, a grid effect, or any of F6's effects drawn from pictures,
played from the slide to the grid as moving to the next slide and back as moving to the previous one.
"""


@dataclass(frozen=True, slots=True)
class Group:
    """
    A run of F7's transitions, which its picker lists under a bar naming it with `title`.
    Picking the bar plays one of them, at random, each time the grid opens or closes, as `random` does from all.
    """

    title: str
    transitions: frozendict[str, GridTransition]


GRID_GROUPS = (
    Group(
        "grid effects",
        frozendict(
            {
                "zoom": Zoomed("the slide shrinks into its thumbnail"),
                # Like F6's, each lasts as long as it takes to follow.
                "scale": Tiled(scale, SWIPE, "the slide is scaled down whole into place"),
                "expose": Tiled(expose, SWIPE * 2, "the others slide in from the edges"),
                "deal": Tiled(deal, SWIPE * 3, "the rest of the deck is dealt around it"),
                "unpack": Tiled(unpack, SWIPE * 2, "*section: the others burst out from under it"),
                "fold": Tiled(fold, SWIPE * 3, "folds up like paper, and unfolds as the grid"),
                "flip": Crossed(flip, SWIPE * 2, "turns over like a card, the grid on its back"),
                "slice": Tiled(sliced, SWIPE * 2, "cut into rows that slide past each other"),
            }
        ),
    ),
    Group(
        "slide effects",
        frozendict({name: transition for name, transition in TRANSITIONS.items() if isinstance(transition, Crossed)}),
    ),
)
"""The grid's own transitions first, then F6's effects drawn from pictures, in the order F7 lists them."""
GROUPED: frozendict[str, Group] = frozendict({group.title: group for group in GRID_GROUPS})
GROUP_ABOUT = "one at random"
"""What F7's picker says on each group's bar."""

GRID_TRANSITIONS: frozendict[str, GridTransition] = frozendict(
    {name: transition for group in GRID_GROUPS for name, transition in group.transitions.items()}
)
GRID_OFFERED = (*AHEAD, *(name for group in GRID_GROUPS for name in (group.title, *group.transitions)))
"""Every name F7 offers, in the order it lists them: each group's title ahead of its transitions."""

type ChooseGrid = Callable[[tuple[GridTransition, ...]], GridTransition]
"""How `random`, or a group's title, picks one of the grid's transitions, such as `random.choice`."""


def grid_transition_for(name: str, choose: ChooseGrid) -> GridTransition | None:
    """
    The transition the grid plays opening or closing with `name` picked, or `None` for `off`:
    for `random`, what `choose` picks from all of them, and for a group's title, what it picks from that group.
    """
    if name == RANDOM:
        return choose(tuple(GRID_TRANSITIONS.values()))
    if (group := GROUPED.get(name)) is not None:
        return choose(tuple(group.transitions.values()))
    return GRID_TRANSITIONS.get(name)


SPEEDS: frozendict[str, float] = frozendict({"0.25x": 0.25, "0.5x": 0.5, "1x": 1.0, "1.5x": 1.5, "2x": 2.0})
"""What F8 offers: how many times faster than its own duration a transition plays, the grid's included."""
SPEED = "1x"
