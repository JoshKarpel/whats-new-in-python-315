"""
One source, three threads, three ways, each played out item by item as it's revealed: a bare generator (two threads
die), `serialize_iterator` (each item to exactly one thread), and `concurrent_tee` (each item to every thread).
The generator is drawn alone, after the slide that breaks it, and the other two side by side, after the slide that
introduces them: they're the ones people mix up, which is why the items move, a cell at a time along the lines:
dealt out, or copied to all three.
"""

from datetime import timedelta

from counterweight.components import Component
from counterweight.components import component
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles.utilities import *

from whats_new.components.animation import use_explanation
from whats_new.diagrams.draw import CROSSED
from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import NOTE
from whats_new.diagrams.draw import area
from whats_new.diagrams.draw import centered_node
from whats_new.diagrams.draw import ink

PANEL = 26
THREADS = 3
DROPS = tuple(4 + thread * 7 for thread in range(THREADS))
"""The column each thread's line leaves the bar at, and its label and items sit under."""
RISE = DROPS[1]
"""
The column of the `┼` in each panel's bar, which its title box sits on: over the middle thread, so the panel is
symmetric and the middle thread's items fall straight down. Far enough in that the widest title box starts at 0.
"""
STEM = 3
"""The row of the line from the title box down to the bar."""
BAR = STEM + 1
DROP = 6
"""How many rows each thread's line falls from the bar: the longer it is, the longer an item is seen travelling."""
LABELS = BAR + DROP + 1
TAKEN = LABELS + 1
"""The first of the two rows each thread's items are listed on, three to a row, once they arrive."""
CAPTION = TAKEN + 3
HEIGHT = CAPTION + 2
ITEMS = 6
PER_CELL = timedelta(milliseconds=100)
"""How long an item in flight takes to move a cell: two frames, so it glides rather than jumps."""
BAR_LINE = "┌──────┼──────┐"

PANELS = (
    ("rows()", ("ValueError: generator", "already executing")),
    ("serialize_iterator", ("each item to exactly", "one thread")),
    ("concurrent_tee", ("each item to every", "thread")),
)
GENERATOR, SERIALIZE, TEE = range(3)
BROKEN = (GENERATOR,)
"""The panels of the diagram that follows the generator breaking."""
SHARED = (SERIALIZE, TEE)
"""The panels of the diagram that follows `serialize_iterator`, which sets `concurrent_tee` beside it."""


def destinations(panel: int, item: int) -> tuple[int, ...]:
    """Which threads `item` goes to: the generator's survivor, one thread in turn, or all three."""
    match panel:
        case 0:
            return (0,)
        case 1:
            return (item % THREADS,)
        case _:
            return tuple(range(THREADS))


def route(thread: int) -> tuple[tuple[int, int], ...]:
    """The cells, as (column, row), an item passes through to `thread`: down from the source, along the bar, down its line."""
    drop = DROPS[thread]
    toward = 1 if drop > RISE else -1
    along = tuple((x, BAR) for x in range(RISE + toward, drop + toward, toward))
    return ((RISE, STEM), (RISE, BAR), *along, *((drop, y) for y in range(BAR + 1, LABELS)))


LONGEST = max(len(route(thread)) for thread in range(THREADS))
"""How many cells the route to the farthest thread has, which sets how long every item's flight takes."""
SPAN = LONGEST + 3
"""
How many cells' worth of time each item gets: long enough to reach the farthest thread, and a beat after.
Every copy lands after the same time, `LONGEST` ticks of this, so `concurrent_tee`'s copies reach all three threads
together: a copy on a shorter route moves slower once it's split off, and still never more than a cell a tick.
"""
SHARED_CELLS = 2
"""The cells every route starts with, the stem and the bar's junction, which `concurrent_tee`'s copies cross as one."""
PER_ITEM = PER_CELL * SPAN


def flight(thread: int, fraction: float) -> tuple[int, int] | None:
    """
    The cell an item `fraction` of the way through its time is in on its way to `thread`, or `None` once it's landed.
    Every copy moves a cell a tick down the stem, where they're one item, then covers the rest of its own route
    in the same time as the farthest thread's, so every copy lands at once.
    """
    path = route(thread)
    ticks = fraction * SPAN
    if ticks < SHARED_CELLS:
        return path[int(ticks)]
    rest = (ticks - SHARED_CELLS) * (len(path) - SHARED_CELLS) / (LONGEST - SHARED_CELLS)
    cell = SHARED_CELLS + int(rest)
    return path[cell] if cell < len(path) else None


def steps(shown: tuple[int, ...]) -> int:
    """How many reveal steps a diagram of the `shown` panels takes: all of them still, then each played in turn."""
    return len(shown) + 1


def ends_showing(shown: tuple[int, ...], step: int) -> str | None:
    """The caption of the panel `step` plays, which appears once all its items are dealt; step 0 plays nothing."""
    return None if step == 0 else PANELS[shown[step - 1]][1][0]


def fan_out(shown: tuple[int, ...], step: int, is_live: bool) -> Div:
    """The `shown` panels side by side, still at step 0, then each played as its step is revealed."""
    panels: list[Div | Component] = []
    for position, index in enumerate(shown):
        playing = position + 1
        if step < playing:
            panels.append(panel(index, 0.0))
        elif step == playing:
            panels.append(playing_panel(index, is_live).with_key(f"panel-{index}"))
        else:
            panels.append(panel(index, 1.0))
    return Div(style=row | shrink(0), children=tuple(panels))


@component
def playing_panel(index: int, is_live: bool) -> Div:
    return panel(index, use_explanation(PER_ITEM * ITEMS, is_live))


def panel(index: int, progress: float) -> Div:
    """
    Panel `index` with `progress` of its items dealt: each travels down from the source and along the bar,
    splitting there for `concurrent_tee`, then down to its threads, where it joins their lists.
    """
    title, caption = PANELS[index]
    current, fraction = divmod(progress * ITEMS, 1)
    # Nothing moves before the panel plays, and nothing after: everything's been dealt.
    in_flight = None if not 0 < progress < 1 else int(current)
    delivered = 0 if progress <= 0 else ITEMS if in_flight is None else in_flight
    has_died = index == GENERATOR and delivered + (in_flight is not None) >= 2

    def has_arrived(thread: int) -> bool:
        return flight(thread, fraction) is None

    flying = () if in_flight is None else destinations(index, in_flight)
    is_dead = [has_died and thread > 0 for thread in range(THREADS)]
    parts: list[Text | Div] = [
        centered_node(title, RISE, 0),
        ink("│", RISE, STEM),
        ink(BAR_LINE, DROPS[0], BAR),
        *(ink("│\n" * DROP, DROPS[thread], BAR + 1) for thread in range(THREADS) if not is_dead[thread]),
        # Under the bar, not on it, so the middle thread's cross doesn't cut the source off from the survivor.
        *(ink("✗", DROPS[thread], BAR + 1, CROSSED) for thread in range(THREADS) if is_dead[thread]),
        # After the lines, so an item in flight paints over them.
        *(ink(str(in_flight), *cell, HIGHLIGHT) for thread in flying if (cell := flight(thread, fraction)) is not None),
        ink("T1     T2     T3", DROPS[0], LABELS, NOTE),
    ]
    for thread in range(THREADS):
        x = DROPS[thread]
        if is_dead[thread]:
            parts += [ink("✗", x, TAKEN, CROSSED), ink("died", x, TAKEN + 1, CROSSED)]
            continue
        taken = [item for item in range(delivered) if thread in destinations(index, item)]
        if in_flight is not None and thread in flying and has_arrived(thread):
            taken.append(in_flight)
        for line in range(2):
            words = taken[line * 3 : line * 3 + 3]
            if words:
                parts.append(ink(" ".join(map(str, words)), x, TAKEN + line, HIGHLIGHT if index == GENERATOR else EDGE))
    if progress >= 1:
        parts += [
            ink(text, 0, CAPTION + line, CROSSED if index == GENERATOR else NOTE) for line, text in enumerate(caption)
        ]
    return area(PANEL, HEIGHT, *parts)
