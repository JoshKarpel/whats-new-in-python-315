"""
One source, four threads, three ways, each played out item by item as it's revealed: a bare generator (three threads
die), `serialize_iterator` (each item to exactly one thread), and `concurrent_tee` (each item to every thread).
The last two are the ones people mix up, which is why the items move: dealt out, or copied to all four.
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
HEIGHT = 11
RISE = 13
"""The column of the `┴` in each panel's bar, which its title box sits on."""
THREADS = 4
DROPS = tuple(3 + thread * 7 for thread in range(THREADS))
"""The column each thread's line leaves the bar at, and its label and items sit under."""
ITEMS = 6
PER_ITEM = timedelta(seconds=2)

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
    """Panel `index` with `progress` of its items dealt: each rises from the source, then drops to its threads."""
    title, caption = PANELS[index]
    current, fraction = divmod(progress * ITEMS, 1)
    # Nothing moves before the panel plays, and nothing after: everything's been dealt.
    in_flight = None if not 0 < progress < 1 else int(current)
    delivered = 0 if progress <= 0 else ITEMS if in_flight is None else in_flight
    has_died = index == GENERATOR and delivered + (in_flight is not None) >= 2

    marks: list[Text | Div] = []
    if in_flight is not None:
        if fraction < 0.5:
            marks.append(ink(str(in_flight), RISE, 3, HIGHLIGHT))
        else:
            marks += [ink(str(in_flight), DROPS[thread], 3, HIGHLIGHT) for thread in destinations(index, in_flight)]
    if has_died:
        marks += [ink("✗", DROPS[thread], 3, CROSSED) for thread in range(1, THREADS)]

    parts: list[Text | Div] = [
        centered_node(title, RISE, 0),
        ink("┌──────┬──┴───┬──────┐", 3, 3),
        *marks,
        ink("T1     T2     T3     T4", 3, 4, NOTE),
    ]
    for thread in range(THREADS):
        x = DROPS[thread]
        if has_died and thread > 0:
            parts += [ink("✗", x, 5, CROSSED), ink("died", x, 6, CROSSED)]
            continue
        taken = [item for item in range(delivered) if thread in destinations(index, item)]
        for line in range(2):
            words = taken[line * 3 : line * 3 + 3]
            if words:
                parts.append(ink(" ".join(map(str, words)), x, 5 + line, HIGHLIGHT if index == GENERATOR else EDGE))
    if progress >= 1:
        parts += [ink(text, 0, 9 + line, CROSSED if index == GENERATOR else NOTE) for line, text in enumerate(caption)]
    return area(PANEL, HEIGHT, *parts)
