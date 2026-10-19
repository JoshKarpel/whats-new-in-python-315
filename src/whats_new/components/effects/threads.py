"""
Free threading: four threads, each its own color and tagged `T1` to `T4` at the head of its brush, take rows from a
shared queue, top to bottom, and race to repaint them with the arriving slide, brushing across from the side the
arriving slide comes from. Each takes the next row as soon as it's done with its last, and each row takes its own
time, so the threads drift apart and the rows finish out of order.

The queue isn't synchronized, so now and then it hands the same row to two threads at once, as an unsynchronized
iterator hands out duplicate items on a free-threaded build: the second thread paints the row with every glyph
doubled, on a red background, over the first one's work. Once the queue is empty, the threads take the duplicated
rows again and paint them properly, so the slide ends exactly as it should.

The whole schedule is worked out once, from a seeded random, so a frame only has to see how far each brush has got.
"""

import random
from dataclasses import dataclass
from enum import Enum
from math import floor

from counterweight.animation import between
from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color

from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.look import PYTHON_BLUE
from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.swipe import Direction

THREAD_COLORS = (PYTHON_BLUE, PYTHON_YELLOW, Color.from_hex("#4ade80"), Color.from_hex("#c084fc"))
"""Each thread's color, `T1` first; there are as many threads as colors."""

BLACK = Color.from_hex("#000000")
DUPLICATED = Color.from_hex("#5c1a1a")
"""The background of a row painted twice, so the duplicate reads as the bug it is."""

TRAIL = 3
"""How many cells behind its brush a thread's fresh paint shows the thread's color."""

DUPLICATES_PER_ROW = 1 / 8
"""Roughly what share of the rows with characters on the queue hands out twice; at least one row always is."""

SHORTEST, LONGEST = 0.6, 1.4
"""The range a row's painting time is drawn from, relative to the average row's."""


class Paint(Enum):
    """What a thread paints a row with: the arriving row, or the arriving row with every glyph doubled."""

    ARRIVING = "arriving"
    DOUBLED = "doubled"


@dataclass(frozen=True, slots=True)
class Job:
    """
    One thread painting one row with `paint`, from when the progress reaches `start` to when it reaches `end`.
    Jobs on the same row paint in the order they started, so the later one covers the earlier one where both have got.
    """

    thread: int
    row: int
    paint: Paint
    start: float
    end: float


def queued(arriving: Grid, chance: random.Random) -> list[tuple[int, Paint]]:
    """
    The rows in the order the queue hands them out: top to bottom, with a few handed out twice in a row, the second
    time to be painted doubled, and those few again at the end, to be painted properly. The rows handed out twice
    have characters on them where there are any, since a blank row painted twice looks no different.
    """
    if not arriving:
        return []
    written = [
        y for y, row in enumerate(arriving) if any(glyph is not None and glyph.grapheme.strip() for glyph in row)
    ]
    candidates = written or list(range(len(arriving)))
    twice = set(chance.sample(candidates, max(1, round(len(candidates) * DUPLICATES_PER_ROW))))
    handed: list[tuple[int, Paint]] = []
    for row in range(len(arriving)):
        handed.append((row, Paint.ARRIVING))
        if row in twice:
            handed.append((row, Paint.DOUBLED))
    return [*handed, *((row, Paint.ARRIVING) for row in sorted(twice))]


def schedule(arriving: Grid) -> tuple[Job, ...]:
    """
    Every job, in the order the queue handed them out: each row to whichever thread is free first, taking a random
    time to paint, all scaled so the last job ends exactly as the transition does.
    """
    chance = random.Random(315)
    free = [0.0] * len(THREAD_COLORS)
    timed: list[tuple[int, int, Paint, float, float]] = []
    for row, paint in queued(arriving, chance):
        thread = free.index(min(free))
        start = free[thread]
        free[thread] = start + chance.uniform(SHORTEST, LONGEST)
        timed.append((thread, row, paint, start, free[thread]))
    last = max(free)
    return tuple(
        Job(thread=thread, row=row, paint=paint, start=start / last, end=end / last)
        for thread, row, paint, start, end in timed
    )


def doubled(row: tuple[StyledGrapheme | None, ...]) -> tuple[StyledGrapheme | None, ...]:
    """
    `row` with every glyph from its first character on twice over, on the duplicate's background, cut to the row's
    width. The indentation stays as it is, so the doubled text starts where the real text does.
    """
    indent = next((x for x, glyph in enumerate(row) if glyph is not None and glyph.grapheme.strip()), len(row))
    painted: list[StyledGrapheme | None] = list(row[:indent])
    for glyph in row[indent:]:
        if glyph is None:
            continue
        twin = StyledGrapheme(grapheme=glyph.grapheme, style=glyph.style | CellStyle(background=DUPLICATED))
        for _ in range(2):
            painted.append(twin)
            if twin.width == 2:
                painted.append(None)
    return tuple(painted[: len(row)])


def tinted(glyph: StyledGrapheme | None, color: Color) -> StyledGrapheme | None:
    """`glyph` as fresh paint, on a background of the thread's `color`."""
    if glyph is None:
        return None
    return StyledGrapheme(grapheme=glyph.grapheme, style=glyph.style | CellStyle(background=color))


def threads(leaving: Grid, arriving: Grid, direction: Direction) -> Frames:
    """
    The race's frames. Each row starts as the leaving slide's, and each job that has started on it, in order, paints
    as far across it as its brush has got; then each brush still going draws its fresh paint in its thread's color
    and its tag just ahead of it.
    """
    width, height = dimensions(leaving)
    jobs = schedule(arriving)
    paints = {Paint.ARRIVING: arriving, Paint.DOUBLED: tuple(doubled(row) for row in arriving)}
    by_row: list[list[Job]] = [[] for _ in range(height)]
    for job in jobs:
        by_row[job.row].append(job)
    trails = tuple(color.blend(BLACK, 0.6) for color in THREAD_COLORS)
    tags = tuple(
        tuple(
            StyledGrapheme(grapheme=character, style=CellStyle(foreground=BLACK, background=color, bold=True))
            for character in f"T{thread + 1}"
        )
        for thread, color in enumerate(THREAD_COLORS)
    )

    def painted(t: float, job: Job) -> int:
        """How many cells of its row `job` has painted."""
        return floor(between(t, job.start, job.end) * width)

    def span(cells: int) -> range:
        """The columns the first `cells` painted cover, from the side the arriving slide comes from."""
        return range(width - cells, width) if direction is Direction.NEXT else range(cells)

    def frame(t: float) -> Grid:
        rows = [list(row) for row in leaving]
        brushes: list[tuple[Job, int]] = []
        for y, row in enumerate(rows):
            for job in by_row[y]:
                cells = painted(t, job)
                if cells <= 0:
                    continue
                columns = span(cells)
                row[columns.start : columns.stop] = paints[job.paint][y][columns.start : columns.stop]
                if cells < width:
                    brushes.append((job, cells))
        for job, cells in brushes:
            row = rows[job.row]
            fresh = span(cells)
            trail = fresh[:TRAIL] if direction is Direction.NEXT else fresh[-TRAIL:]
            for x in trail:
                row[x] = tinted(row[x], trails[job.thread])
            ahead = (fresh.start - 2, fresh.start - 1) if direction is Direction.NEXT else (fresh.stop, fresh.stop + 1)
            for x, character in zip(ahead, tags[job.thread], strict=True):
                if 0 <= x < width:
                    row[x] = character
        return tuple(tuple(row) for row in rows)

    return frame
