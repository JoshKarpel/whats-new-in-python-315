"""
The garbage collector saga's diagrams: reference counting and what the cycle collector adds to it, generations,
the two schedules CPython has run the collector on, which release ran which, and what core developers said went
wrong with the incremental one.

Each animates on a reveal step: the step remounts the animated part, which plays it once.
"""

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from counterweight.components import Component
from counterweight.components import component
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles import CellStyle
from counterweight.styles import Style
from counterweight.styles.utilities import border_color
from counterweight.styles.utilities import default

from whats_new.components.animation import use_explanation
from whats_new.diagrams.draw import CROSSED
from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import HIGHLIGHT_NODE
from whats_new.diagrams.draw import NOTE
from whats_new.diagrams.draw import area
from whats_new.diagrams.draw import ink
from whats_new.diagrams.draw import middle
from whats_new.diagrams.draw import node
from whats_new.diagrams.timeline import Milestone
from whats_new.diagrams.timeline import timeline_through

GONE = CellStyle(foreground=EDGE.foreground, dim=True)
FREED_NODE = Style(text_style=CROSSED) | border_color("red", 400)

CYCLE_STEPS = 4
"""Everything held by a name; then `del z`, played; then `del x`; then a collection, played."""
RELEASE = timedelta(seconds=2)
COUNTED, RELEASED = 0.35, 0.7
"""How far through `del z` the count drops to 0, then reference counting frees the object."""
AT_ONCE = "most objects go this way, with no collector involved"
"""The end of the caption once `del z` has played."""
COLLECTION = timedelta(seconds=4)
SUBTRACTED, KEPT = 0.15, 0.5
"""How far through the collection it subtracts the references from inside, then keeps what's held from outside."""
FREED = "the rest is garbage: a and b are freed"
"""The end of the caption once the collection has played."""


@dataclass(frozen=True, slots=True)
class Cycle:
    """Two objects referring to each other, the name that refers to the first of them, and the row it's drawn from."""

    name: str
    first: str
    second: str
    y: int


LONE = Cycle(name="z", first="e", second="", y=1)
"""Not a cycle: one object, held by a name, which reference counting frees alone."""
DELETED = Cycle(name="x", first="a", second="b", y=5)
HELD = Cycle(name="y", first="c", second="d", y=11)
LABEL = len("a  2 - 1 = 1")
"""Every object's label is padded to the widest it gets, so the boxes don't move as the labels change."""
FIRST_X = 13
SECOND_X = FIRST_X + LABEL + 4 + 7
FATE_X = SECOND_X + LABEL + 6


def cycle_collection(step: int, is_live: bool) -> Div | Component:
    """
    An object held by a name, beside two cycles of two objects, each object labeled with its reference count,
    and a name holding each cycle. `del z` plays: `e`'s count drops to 0 and reference counting frees it at once.
    Then `del x` leaves `a` and `b` holding only each other. Then a collection plays: it subtracts the references
    from inside the heap, keeps what's still above 0 (and what that reaches), and frees the rest.
    """
    match step:
        case 0:
            return heap(released=0, is_deleted=False, progress=0)
        case 1:
            return releasing(is_live).with_key("releasing")
        case 2:
            return heap(released=1, is_deleted=True, progress=0)
        case _:
            return playing_collection(is_live).with_key("collecting")


def cycle_collection_ends_showing(step: int) -> str | None:
    return {1: AT_ONCE, 3: FREED}.get(step)


@component
def releasing(is_live: bool) -> Div:
    return heap(released=use_explanation(RELEASE, is_live), is_deleted=False, progress=0)


@component
def playing_collection(is_live: bool) -> Div:
    return heap(released=1, is_deleted=True, progress=use_explanation(COLLECTION, is_live))


def heap(released: float, is_deleted: bool, progress: float) -> Div:
    """
    The lone object `released` of the way through `del z` (0 before it, 1 once it's freed), the cycles,
    and `progress` of the way through a collection (0 before one starts).
    """
    return area(
        84,
        19,
        ink("names", 0, 0, NOTE),
        ink("objects, each counting the references to it", FIRST_X, 0, NOTE),
        *lone(released, is_deleted),
        *cycle(DELETED, is_held=not is_deleted, progress=progress),
        *cycle(HELD, is_held=True, progress=progress),
        *collection_caption(released, is_deleted, progress),
    )


def lone(released: float, is_deleted: bool) -> list[Text | Div]:
    """
    `z` and the object it holds: as `del z` plays, the arrow goes, the count drops to 0, and the object is freed.
    Once the cycles take over (`is_deleted`), all that's left of it is a line saying what happened.
    """
    y = LONE.y
    if is_deleted:
        return [ink("del z: e was freed the moment its count hit 0", 0, y + 1, GONE)]
    if released == 0:
        return [
            node(LONE.name, 0, y),
            ink("──────▶", 5, y + 1),
            node(f"{LONE.first}  refs 1".ljust(LABEL), FIRST_X, y),
        ]
    is_counted = released >= COUNTED
    is_freed = released >= RELEASED
    return [
        node(LONE.name, 0, y, style=Style(text_style=GONE)),
        ink("   ✗", 5, y + 1, CROSSED),
        node(
            f"{LONE.first}  refs {0 if is_counted else 1}".ljust(LABEL),
            FIRST_X,
            y,
            style=FREED_NODE if is_freed else HIGHLIGHT_NODE if is_counted else default,
        ),
        *((ink("freed at once, by reference counting", SECOND_X, y + 1, CROSSED),) if is_freed else ()),
    ]


def cycle(drawn: Cycle, is_held: bool, progress: float) -> list[Text | Div]:
    """
    One cycle: its name's box and the arrow to the first object (or, deleted, a dim box and no arrow),
    the two objects with the arrows between them, and once the collection is done, what happened to them.
    """
    y = drawn.y
    is_subtracted = progress >= SUBTRACTED
    is_done = progress >= 1
    inside = HIGHLIGHT if SUBTRACTED <= progress < KEPT else EDGE

    def label(name: str, refs: int) -> str:
        return (f"{name}  {refs} - 1 = {refs - 1}" if is_subtracted else f"{name}  refs {refs}").ljust(LABEL)

    fate = HIGHLIGHT_NODE if progress >= KEPT and is_held else FREED_NODE if is_done and not is_held else default
    first_middle = middle(FIRST_X, label(drawn.first, 0))
    second_middle = middle(SECOND_X, label(drawn.second, 0))
    parts: list[Text | Div] = [
        node(drawn.name, 0, y, style=default if is_held else Style(text_style=GONE)),
        ink("──────▶" if is_held else "   ✗", 5, y + 1, EDGE if is_held else CROSSED),
        node(label(drawn.first, 2 if is_held else 1), FIRST_X, y, style=fate),
        ink("──────▶", FIRST_X + LABEL + 4, y + 1, inside),
        node(label(drawn.second, 1), SECOND_X, y, style=fate),
        ink("▲", first_middle, y + 3, inside),
        ink("│", second_middle, y + 3, inside),
        ink("└" + "─" * (second_middle - first_middle - 1) + "┘", first_middle, y + 4, inside),
    ]
    if not is_held:
        parts.append(ink(f"del {drawn.name}", 0, y + 3, CROSSED))
    if is_done:
        if is_held:
            parts.append(ink(f"kept: {drawn.name} holds {drawn.first}", FATE_X, y + 1, HIGHLIGHT))
        else:
            parts.append(ink("freed", FATE_X, y + 1, CROSSED))
    return parts


def collection_caption(released: float, is_deleted: bool, progress: float) -> tuple[Text, Text]:
    first: str | tuple[Chunk, ...]
    second: str | tuple[Chunk, ...]
    if progress >= 1:
        first = "what's still above 0 is held from outside, and so is everything it reaches"
        second = (Chunk(content=FREED, style=CROSSED),)
    elif progress > 0:
        first, second = "a collection subtracts the references that come from inside the heap", ""
    elif is_deleted:
        first = "del x: a and b still hold each other, so neither count reaches 0"
        second = "reference counting never frees a cycle: that's the cycle collector's job"
    elif released > 0:
        first = "del z: e's count drops to 0, and reference counting frees it on the spot"
        second = AT_ONCE if released >= 1 else ""
    else:
        first = "every object counts the references to it"
        second = "the cycle collector runs every 2,000 new objects: it counts objects, not bytes"
    return ink(first, 0, 17, NOTE), ink(second, 0, 18, NOTE)


GENERATION_STEPS = 2
"""An empty heap; then two dozen objects allocated and collected, played."""
LIFETIMES = (1, 2, 50, 1, 6, 1, 50, 2, 1, 14, 2, 50, 1, 2, 9, 1, 50, 18, 1, 2, 50, 1, 3, 1, 2, 50, 1)
"""How many allocations each object lives for, in the order they're allocated: most die young, a few never do."""
YOUNG_LIMIT = 4
"""Allocations between gen 0 collections, standing for the real 2,000."""
OLDER_EVERY = 3
"""Gen 0 collections between gen 1 collections, standing for the real 10."""
PROMOTING = timedelta(seconds=12)
GENERATION_LABELS = ("every 2,000 new objects", "every 10th collection", "rarely: the whole heap")
GENERATION_CELLS = (10, 14, 22)
"""How many cells wide each generation's box is: two cells an object."""
WAITING = "garbage that dies after moving up waits for its generation's turn"
"""The catch, which appears once the objects have played."""


class Cell(Enum):
    """How one object in a generation is drawn."""

    LIVE = "●"
    DEAD = "○"
    """Garbage the collector hasn't reached yet."""
    FREEING = "✗"
    """Garbage the collection under way is freeing."""


@dataclass(frozen=True, slots=True)
class Snapshot:
    """The heap at one moment of the generations animation."""

    generations: tuple[tuple[Cell, ...], ...]
    collecting: int | None
    """The oldest generation the collection under way scans, which scans every younger one with it."""
    status: str


def promotions() -> tuple[Snapshot, ...]:
    """
    The heap after each moment of a model of the generational collector: objects are allocated into gen 0,
    and every `YOUNG_LIMIT` allocations a collection frees the garbage in gen 0 and moves the survivors to gen 1.
    Every `OLDER_EVERY`th collection scans gen 1 too, moving its survivors and gen 0's to gen 2.
    Each collection is two moments: its garbage marked as it's freed, then the survivors moved up.
    """
    born: list[list[int]] = [[], [], []]
    allocated = 0
    collections = 0

    def is_dead(index: int) -> bool:
        return allocated > index + LIFETIMES[index]

    def snapshot(collecting: int | None, is_freeing: bool, status: str) -> Snapshot:
        def cell(index: int, generation: int) -> Cell:
            if not is_dead(index):
                return Cell.LIVE
            if is_freeing and collecting is not None and generation <= collecting:
                return Cell.FREEING
            return Cell.DEAD

        return Snapshot(
            generations=tuple(tuple(cell(index, g) for index in objects) for g, objects in enumerate(born)),
            collecting=collecting,
            status=status,
        )

    moments = [snapshot(None, False, "")]
    for index in range(len(LIFETIMES)):
        born[0].append(index)
        allocated += 1
        moments.append(snapshot(None, False, "a new object starts in gen 0"))
        if len(born[0]) < YOUNG_LIMIT:
            continue
        collections += 1
        oldest = 1 if collections % OLDER_EVERY == 0 else 0
        scanned = [index for generation in born[: oldest + 1] for index in generation]
        survivors = [index for index in scanned if not is_dead(index)]
        freed = len(scanned) - len(survivors)
        names = "gen 0" if oldest == 0 else "gens 0 and 1"
        moments.append(snapshot(oldest, True, f"collecting {names}: {freed} garbage freed"))
        for generation in range(oldest + 1):
            born[generation] = []
        born[oldest + 1] += survivors
        moments.append(snapshot(oldest, False, f"{len(survivors)} survivors move up to gen {oldest + 1}"))
    return tuple(moments)


SNAPSHOTS = promotions()


def generations(step: int, is_live: bool) -> Div | Component:
    """The generational collector's three generations: empty, then the objects allocated and collected, played."""
    if step == 0:
        return generations_at(SNAPSHOTS[0], is_done=False)
    return promoting(is_live).with_key("promoting")


def generations_ends_showing(step: int) -> str | None:
    return WAITING if step == 1 else None


@component
def promoting(is_live: bool) -> Div:
    progress = use_explanation(PROMOTING, is_live)
    index = min(len(SNAPSHOTS) - 1, int(progress * len(SNAPSHOTS)))
    return generations_at(SNAPSHOTS[index], is_done=progress >= 1)


def generations_at(snapshot: Snapshot, is_done: bool) -> Div:
    parts: list[Text | Div] = [ink("new objects", 0, 1, NOTE), ink("──▶", 12, 1)]
    for generation, cells in enumerate(snapshot.generations):
        y = 1 + generation * 3
        is_collecting = snapshot.collecting is not None and generation <= snapshot.collecting
        width = GENERATION_CELLS[generation]
        parts += [
            ink(f"gen {generation} ▕", 16, y, HIGHLIGHT if is_collecting else NOTE),
            ink(tuple(cell_chunks(cells, width)), 23, y),
            ink("▏", 23 + width, y, HIGHLIGHT if is_collecting else NOTE),
            ink(GENERATION_LABELS[generation], 26 + max(GENERATION_CELLS), y, NOTE),
        ]
        if generation < len(snapshot.generations) - 1:
            parts.append(ink("│ survivors\n▼", 19, y + 1, EDGE))
    parts += [
        ink(snapshot.status, 16, 9, HIGHLIGHT),
        ink("● live   ○ garbage, not yet collected   (sped up: 4 new objects stand for 2,000)", 0, 11, GONE),
        ink("every new object starts in gen 0; a collection frees the garbage there", 0, 13, NOTE),
        ink("and moves the survivors up a generation, where they're scanned less often", 0, 14, NOTE),
        *((ink(WAITING, 0, 15, CROSSED),) if is_done else ()),
        ink("3.14.0 to 3.14.4 had two generations: young, and old for everything that survived it", 0, 17, NOTE),
    ]
    return area(26 + max(GENERATION_CELLS) + len(GENERATION_LABELS[2]), 18, *parts)


def cell_chunks(cells: tuple[Cell, ...], width: int) -> list[Chunk]:
    """A generation's objects, two cells each, colored by what they are, padded to `width`."""
    chunks = [Chunk(content=f"{cell.value} ", style=NOTE if cell is Cell.LIVE else CROSSED) for cell in cells]
    return [*chunks, Chunk(content=" " * (width - 2 * len(cells)))]


SCHEDULE_STEPS = 2
"""The two schedules, still; then twenty collections on each, played."""
TICKS = 20
SCHEDULE = timedelta(seconds=6)
GENERATIONS = (("gen 0", 6), ("gen 1", 10), ("gen 2", 40))
"""Each generation of the generational collector, by its name and how many cells of the heap it's drawn with."""
PAUSES = "▁▃█"
"""How long a generational collection pauses, by how many generations it scans."""
YOUNG = 6
SLICES, SLICE = 10, 5
"""The incremental collector's old generation, drawn as the slices it scans, one per collection."""
WAITS = "but garbage in the old generation waits for its slice to come round"
"""The incremental collector's catch, which appears once its collections have played."""
OBJECT, SCANNING = "▒", "█"


def schedules(step: int, is_live: bool) -> Div | Component:
    """
    Both collectors' heaps, one above the other, with the pauses each collection takes.
    At step 1, twenty collections play on each: the generational one scans generation 0 every time,
    generation 1 every tenth, and the whole heap now and then; the incremental one scans the young generation
    and the next slice of the old every time.
    """
    if step == 0:
        return schedule(0)
    return playing_schedule(is_live).with_key("playing")


def schedules_ends_showing(step: int) -> str | None:
    return WAITS if step == 1 else None


@component
def playing_schedule(is_live: bool) -> Div:
    return schedule(round(use_explanation(SCHEDULE, is_live) * TICKS))


def generations_scanned(tick: int) -> int:
    """How many generations, youngest first, the generational collector's collection number `tick` (from 1) scans."""
    if tick == TICKS:
        return 3
    if tick % 10 == 0:
        return 2
    return 1


def schedule(tick: int) -> Div:
    """The two schedules `tick` collections in (0 being before the first), the latest collection's scan lit up."""
    is_done = tick == TICKS
    return area(
        84,
        13,
        ink("generational: 3.13, 3.14.5 on, 3.15", 0, 0, HIGHLIGHT),
        ink(generational_heap(tick), 0, 1),
        ink("pauses", 0, 2, NOTE),
        ink("".join(PAUSES[generations_scanned(t) - 1] for t in range(1, tick + 1)), 8, 2, HIGHLIGHT),
        *((ink("mostly tiny, but now and then one scans the whole heap: 26 ms", 0, 3, NOTE),) if is_done else ()),
        ink("incremental: 3.14.0 to 3.14.4", 0, 6, HIGHLIGHT),
        ink(incremental_heap(tick), 0, 7),
        ink("pauses", 0, 8, NOTE),
        ink("▂" * tick, 8, 8, HIGHLIGHT),
        *(
            (
                ink("each scans the young and the next slice of the old: 1.3 ms at most", 0, 9, NOTE),
                ink(WAITS, 0, 10, CROSSED),
            )
            if is_done
            else ()
        ),
        ink("the longest pauses in a synthetic benchmark, from the discussion of the revert", 0, 12, GONE),
    )


def generational_heap(tick: int) -> tuple[Chunk, ...]:
    """The three generations, those collection `tick` scans lit up."""
    scanned = generations_scanned(tick) if tick else 0
    chunks: list[Chunk] = []
    for index, (name, cells) in enumerate(GENERATIONS):
        is_scanning = index < scanned
        chunks += [
            Chunk(content=f"{name} ▕", style=NOTE),
            Chunk(content=(SCANNING if is_scanning else OBJECT) * cells, style=HIGHLIGHT if is_scanning else EDGE),
            Chunk(content="▏ ", style=NOTE),
        ]
    return tuple(chunks)


def incremental_heap(tick: int) -> tuple[Chunk, ...]:
    """The young generation and the old one's slices: the slice collection `tick` scans lit, those before it in its lap visited."""
    scanning = (tick - 1) % SLICES if tick else None
    old = []
    for index in range(SLICES):
        if index == scanning:
            old.append(Chunk(content=SCANNING * SLICE, style=HIGHLIGHT))
        else:
            is_visited = scanning is not None and index < scanning
            old.append(Chunk(content=OBJECT * SLICE, style=NOTE if is_visited else EDGE))
    return (
        Chunk(content="young ▕", style=NOTE),
        Chunk(content=(SCANNING if tick else OBJECT) * YOUNG, style=HIGHLIGHT if tick else EDGE),
        Chunk(content="▏ old ▕", style=NOTE),
        *old,
        Chunk(content="▏", style=NOTE),
    )


RELEASES = (
    Milestone("3.13 betas", "tried, pulled", "generational", NOTE),
    Milestone("3.14.0", "ships it", "incremental", CROSSED),
    Milestone("3.14.1", "a speed fix", "incremental", CROSSED),
    Milestone("3.14.5", "reverted", "generational", NOTE),
    Milestone("3.15", "a PEP to return", "generational", NOTE),
)
"""Each release, what happened in it, and the collector it runs."""
TIMELINE_STEPS = len(RELEASES)
"""One release per step, the timeline drawing itself on to it."""
RELEASE_SPACING = 17


def timeline_ends_showing(step: int) -> str | None:
    """What happened in the release at `step`, which appears once the axis reaches it."""
    return RELEASES[step].event


def timeline(step: int, is_live: bool) -> Component:
    """The releases up to the one at `step`, the axis growing out to the newest, which appears when it arrives."""
    return timeline_through(RELEASES, RELEASE_SPACING, step, is_live)


WAITING_STEPS = 2
"""The early return and what core developers said about it, still; then Neil Schemenauer's measurements, played."""
OUTSTANDING = (
    ("3.13", 100, "under 100"),
    ("3.14.0", 2_000, "about 2,000"),
    ("after GH-140262", 10_000, "10,000"),
)
"""
The most garbage objects outstanding at once in Neil Schemenauer's test, by build, as GH-142001 reports them:
"With Python 3.13 (non-incremental GC), I get a max of less than 100 objects. With 3.14.0, I get approximately 2000
as the max. With the "main" branch (and 3.14 branch), I get 10,000 as the max."
"""
GROW = timedelta(seconds=2)
BAR = 50
LABEL_WIDTH = 17
TOY = "Tim Peters' toy program on 3.14.4: 90 to 100 dead cycles waiting for every live one"
"""What Tim Peters reported on the revert's discussion, which appears once the bars have grown."""
EIGHTHS = " ▏▎▍▌▋▊▉█"


def waiting(step: int, is_live: bool) -> Div | Component:
    """Neil Schemenauer's measurements of garbage left waiting, as bars: empty, then grown to their values."""
    if step == 0:
        return waiting_bars(0)
    return growing_bars(is_live).with_key("growing")


def waiting_ends_showing(step: int) -> str | None:
    return TOY if step == 1 else None


@component
def growing_bars(is_live: bool) -> Div:
    return waiting_bars(use_explanation(GROW, is_live))


def waiting_bars(progress: float) -> Div:
    """The bars `progress` of the way grown, each labeled with its value once it's fully grown."""
    largest = max(count for _, count, _ in OUTSTANDING)
    parts: list[Text | Div] = [
        ink("most garbage objects waiting at once, in Neil Schemenauer's test (GH-142001)", 0, 0, NOTE)
    ]
    for row, (build, count, said) in enumerate(OUTSTANDING, 1):
        parts += [
            ink(build, 0, row, HIGHLIGHT),
            ink(bar(progress * count / largest), LABEL_WIDTH, row, CROSSED if count == largest else NOTE),
        ]
        if progress >= 1:
            parts.append(ink(said, LABEL_WIDTH + BAR + 1, row, NOTE))
    if progress >= 1:
        parts.append(ink(TOY, 0, len(OUTSTANDING) + 2, CROSSED))
    return area(LABEL_WIDTH + BAR + 1 + len("about 2,000"), len(OUTSTANDING) + 3, *parts)


def bar(fraction: float) -> str:
    """A bar `fraction` of `BAR` cells long, drawn to the eighth of a cell, at least a sliver for anything above 0."""
    eighths = round(fraction * BAR * 8)
    if fraction > 0:
        eighths = max(1, eighths)
    return "█" * (eighths // 8) + EIGHTHS[eighths % 8].strip()
