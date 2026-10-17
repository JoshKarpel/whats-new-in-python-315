"""
One source, four threads, three ways, each played out item by item as it's revealed: a bare generator (three threads
die), `serialize_iterator` (each item to exactly one thread), and `concurrent_tee` (each item to every thread).
The last two are the ones people mix up, which is why the items move, a cell at a time along the lines:
dealt out, or copied to all four.
"""

from datetime import timedelta

from counterweight.components import Component
from counterweight.components import component
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles.utilities import *

from whats_new.components.animation import use_progress
from whats_new.diagrams.draw import CROSSED
from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import NOTE
from whats_new.diagrams.draw import area
from whats_new.diagrams.draw import centered_node
from whats_new.diagrams.draw import ink

STEPS = 4
"""The generator's panel, still; then playing; then each of the other two, revealed playing."""
PANEL = 29
RISE = 13
"""The column of the `┴` in each panel's bar, which its title box sits on."""
THREADS = 4
DROPS = tuple(3 + thread * 7 for thread in range(THREADS))
"""The column each thread's line leaves the bar at, and its label and items sit under."""
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
BAR_LINE = "┌──────┬──┴───┬──────┐"

PANELS = (
    ("rows()", ("ValueError: generator", "already executing")),
    ("serialize_iterator", ("each item to exactly", "one thread")),
    ("concurrent_tee", ("each item to every", "thread")),
)
GENERATOR, SERIALIZE, TEE = range(3)


def destinations(panel: int, item: int) -> tuple[int, ...]:
    """Which threads `item` goes to: the generator's survivor, one thread in turn, or all four."""
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


SPAN = max(len(route(thread)) for thread in range(THREADS)) + 3
"""
How many cells' worth of time each item gets: long enough to reach the farthest thread, and a beat after.
Every copy moves a cell per tick of this, so copies to nearer threads arrive first, as they would.
"""
PER_ITEM = PER_CELL * SPAN


def ends_showing(step: int) -> str | None:
    """The caption of the panel `step` plays, which appears once all its items are dealt; step 0 plays nothing."""
    return None if step == 0 else PANELS[step - 1][1][0]


def fan_out(step: int, is_live: bool) -> Div:
    panels: list[Div | Component] = []
    for index in range(len(PANELS)):
        # Panel 0 shows still before it plays; the others are blank until they play, which keeps the row's width.
        playing = index + 1
        if step < playing:
            panels.append(panel(index, 0.0) if index == 0 else area(PANEL, HEIGHT))
        elif step == playing:
            panels.append(playing_panel(index, is_live).with_key(f"panel-{index}"))
        else:
            panels.append(panel(index, 1.0))
    return Div(style=row | shrink(0), children=tuple(panels))


@component
def playing_panel(index: int, is_live: bool) -> Div:
    return panel(index, use_progress(PER_ITEM * ITEMS, is_live))


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
    cell = int(fraction * SPAN)

    def has_arrived(thread: int) -> bool:
        return cell >= len(route(thread))

    flying = () if in_flight is None else destinations(index, in_flight)
    is_dead = [has_died and thread > 0 for thread in range(THREADS)]
    parts: list[Text | Div] = [
        centered_node(title, RISE, 0),
        ink("│", RISE, STEM),
        ink(BAR_LINE, DROPS[0], BAR),
        *(ink("│\n" * DROP, DROPS[thread], BAR + 1) for thread in range(THREADS) if not is_dead[thread]),
        *(ink("✗", DROPS[thread], BAR, CROSSED) for thread in range(THREADS) if is_dead[thread]),
        # After the lines, so an item in flight paints over them.
        *(ink(str(in_flight), *route(thread)[cell], HIGHLIGHT) for thread in flying if not has_arrived(thread)),
        ink("T1     T2     T3     T4", DROPS[0], LABELS, NOTE),
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
