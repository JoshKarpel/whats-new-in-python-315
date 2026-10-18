"""
The sampling profiler: a dashed playhead sweeps across the stage from the side the arriving slide comes from, and at
each of a fixed number of evenly spaced ticks it takes a sample: a few rows, picked at random, flip to the arriving
slide all at once, lit up until the next tick, with a `●` where the playhead was when it sampled them. The markers
fade over the next few ticks, leaving a scatter of recent samples behind the playhead. Every row is in exactly one
sample, so by the last tick the whole arriving slide is showing, but it gets there in jumps, a snapshot at a time,
rather than as a smooth wipe.
"""

import random
from dataclasses import dataclass
from math import floor

from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color

from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.easing import Easing
from whats_new.components.effects.characters import backgrounds
from whats_new.components.look import PYTHON_BLUE
from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.swipe import Direction

TICKS = 12
"""How many samples the profiler takes, evenly spaced through the eased progress."""

LIT = Color.from_hex("#1e3a5f")
"""The background a freshly sampled row is lit with until the next tick."""

MARKER = "●"
FADING = (PYTHON_YELLOW, Color.from_hex("#b8952a"), Color.from_hex("#6b5a22"))
"""A sample marker's color on the tick it's taken and on each tick after, until it's gone."""

PLAYHEAD = "┊"
PLAYHEAD_COLOR = PYTHON_BLUE


@dataclass(frozen=True, slots=True)
class Sample:
    """One tick's sample: taken when the eased progress reaches `at`, of `rows`, by the playhead at `column`."""

    at: float
    rows: tuple[int, ...]
    column: int


def tick_at(tick: int) -> float:
    """When the eased progress reaches `tick`, counting from 0: strictly inside the transition, so none is at either end."""
    return (tick + 1) / (TICKS + 1)


def playhead_at(eased: float, width: int, direction: Direction) -> int:
    """
    Which column the playhead is over, `eased` of the way through, coming from the side the arriving slide comes
    from: just off the stage at either end. On a stage narrower than about `TICKS` columns, the first and last ticks
    come while it's off the stage, and their markers with it.
    """
    travelled = floor(eased * (width + 1)) - 1
    return width - 1 - travelled if direction is Direction.NEXT else travelled


def samples(width: int, height: int, direction: Direction) -> tuple[Sample, ...]:
    """
    Every tick's sample. The rows are shuffled, the same way each run, and dealt out one tick at a time,
    so each row is sampled exactly once and every tick but (on a short stage) the last few samples some.
    """
    rows = list(range(height))
    random.Random(315).shuffle(rows)
    return tuple(
        Sample(
            at=tick_at(tick), rows=tuple(sorted(rows[tick::TICKS])), column=playhead_at(tick_at(tick), width, direction)
        )
        for tick in range(TICKS)
    )


def lit(glyph: StyledGrapheme | None) -> StyledGrapheme | None:
    """`glyph` on a freshly sampled row: the same, on the lit background."""
    if glyph is None:
        return None
    return StyledGrapheme(grapheme=glyph.grapheme, style=glyph.style | CellStyle(background=LIT))


def sampling(leaving: Grid, arriving: Grid, direction: Direction, easing: Easing) -> Frames:
    """
    The sampling profiler's frames. Each row is the leaving slide's until its sample, lit until the next tick,
    then the arriving slide's; the markers and playhead go over the top.
    """
    width, height = dimensions(leaving)
    taken = samples(width, height, direction)
    sampled_at = [1.0] * height
    lit_until = [1.0] * height
    for tick, sample in enumerate(taken):
        for y in sample.rows:
            sampled_at[y] = sample.at
            lit_until[y] = tick_at(tick + 1) if tick + 1 < TICKS else 1.0
    lit_rows = tuple(tuple(lit(glyph) for glyph in row) for row in arriving)
    under, over = backgrounds(leaving), backgrounds(arriving)

    def row_at(y: int, eased: float) -> list[StyledGrapheme | None]:
        if eased < sampled_at[y]:
            return list(leaving[y])
        if eased < lit_until[y]:
            return list(lit_rows[y])
        return list(arriving[y])

    def frame(t: float) -> Grid:
        eased = easing(t)
        # The last ticks' markers would still be fading, but the run is over, so they go with the playhead.
        if eased >= 1:
            return arriving
        rows = [row_at(y, eased) for y in range(height)]
        playhead = playhead_at(eased, width, direction)
        if 0 <= playhead < width:
            for y, row in enumerate(rows):
                if eased < sampled_at[y]:
                    back = under[y][playhead].style.background
                else:
                    back = LIT if eased < lit_until[y] else over[y][playhead].style.background
                row[playhead] = StyledGrapheme(
                    grapheme=PLAYHEAD, style=CellStyle(foreground=PLAYHEAD_COLOR, background=back)
                )
        for sample in taken:
            age = floor((eased - sample.at) * (TICKS + 1))
            if not (0 <= age < len(FADING) and 0 <= sample.column < width):
                continue
            for y in sample.rows:
                back = LIT if eased < lit_until[y] else over[y][sample.column].style.background
                rows[y][sample.column] = StyledGrapheme(
                    grapheme=MARKER, style=CellStyle(foreground=FADING[age], background=back, bold=True)
                )
        return tuple(tuple(row) for row in rows)

    return frame
