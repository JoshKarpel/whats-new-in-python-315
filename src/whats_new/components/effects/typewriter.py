"""
The typewriter: the slide being left backspaces away, its rows erasing right to left from the bottom row up,
then the arriving slide types itself in, left to right from the top row down, a block cursor at every row's
typing position.

A slide has far more characters than a typist could manage in a second or two, so the rows type at once,
each setting off a little after the one above it (and erasing a little after the one below), and a keystroke
only ever lands on a character: the cursor skips runs of blanks the way a tab would. Every row keys at the same
speed, the fastest that lets the last to start finish in time, so short rows finish early and long ones run on.
Cells not yet typed show the arriving slide's backgrounds, so a code block's dark box is there to type into.
The direction plays no part: typing reads left to right either way.
"""

from dataclasses import dataclass
from math import floor

from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle

from whats_new.components.animation import between
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.easing import Easing
from whats_new.components.effects.characters import Backgrounds
from whats_new.components.effects.characters import backgrounds
from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.swipe import Direction

ERASING = 0.35
"""How much of the eased progress the backspacing takes; the typing takes the rest."""
STAGGER = 0.4
"""How much of each phase the rows' starts are spread over, top to bottom typing and bottom to top erasing."""
CURSOR = "█"

type Row = tuple[StyledGrapheme | None, ...]


@dataclass(frozen=True, slots=True)
class Keying:
    """
    How one row is typed or erased: `stops[k]` is where the typed part of the row ends once `k` of its characters
    are in, so `stops[0]` is its first character's column and the last stop is just past its last character.
    Its keystrokes are spread evenly from `start` to `stop` of the phase.
    """

    stops: tuple[int, ...]
    start: float
    stop: float

    def typed(self, progress: float) -> float:
        """How far through its own keystrokes the row is, `progress` of the way through the phase."""
        return between(progress, self.start, self.stop)

    def end(self, typed: float) -> int:
        """Where the typed part of the row ends, `typed` of the way through its keystrokes."""
        return self.stops[floor(typed * (len(self.stops) - 1))]


def stops_of(row: Row) -> tuple[int, ...]:
    """
    Where a row's typed part ends after each keystroke, starting at its first character, one keystroke per
    character and none for blanks. Each stop is just past a whole grapheme, so a two-cell-wide one is never split.
    """
    ends = tuple(x + glyph.width for x, glyph in enumerate(row) if glyph is not None and glyph.grapheme.strip())
    if not ends:
        return ()
    first = next(x for x, glyph in enumerate(row) if glyph is not None and glyph.grapheme.strip())
    return (first, *ends)


def keyings(rows: tuple[Row, ...], is_top_first: bool) -> tuple[Keying | None, ...]:
    """
    Each row's keying, `None` for a row with nothing to type. The rows that have something start one after another,
    from the top or the bottom, and all key at the one speed that has the last of them done by the end.
    """
    stops = tuple(stops_of(row) for row in rows)
    keyed = [y for y, row_stops in enumerate(stops) if row_stops]
    if not is_top_first:
        keyed.reverse()
    starts = {y: STAGGER * rank / max(len(keyed) - 1, 1) for rank, y in enumerate(keyed)}
    per_key = min(((1 - starts[y]) / (len(stops[y]) - 1) for y in keyed), default=1.0)
    return tuple(
        Keying(stops=row_stops, start=starts[y], stop=starts[y] + (len(row_stops) - 1) * per_key) if row_stops else None
        for y, row_stops in enumerate(stops)
    )


def cursor_over(cell: StyledGrapheme) -> StyledGrapheme:
    """The cursor, drawn in the background of the cell it's over."""
    return StyledGrapheme(grapheme=CURSOR, style=CellStyle(foreground=PYTHON_YELLOW, background=cell.style.background))


def keyed_row(row: Row, behind: tuple[StyledGrapheme, ...], keying: Keying | None, typed: float) -> Row:
    """
    `row` typed in `typed` of the way over `behind`, its own cells with the characters gone, with the cursor
    just past the last character in while the row is part typed.
    """
    if keying is None or typed >= 1:
        return row
    end = keying.end(typed)
    if typed <= 0 or end >= len(row):
        return (*row[:end], *behind[end:])
    return (*row[:end], cursor_over(behind[end]), *behind[end + 1 :])


def typewriter(leaving: Grid, arriving: Grid, direction: Direction, easing: Easing) -> Frames:
    """
    The typewriter's frames: backspacing the leaving slide over its own backgrounds for the first part of the
    eased progress, then typing the arriving slide over its own.
    """
    erasings, typings = keyings(leaving, is_top_first=False), keyings(arriving, is_top_first=True)
    left_behind: Backgrounds = backgrounds(leaving)
    to_type_over: Backgrounds = backgrounds(arriving)

    def frame(t: float) -> Grid:
        eased = easing(t)
        if eased < ERASING:
            erased = between(eased, 0, ERASING)
            return tuple(
                keyed_row(row, behind, keying, 1 - keying.typed(erased) if keying else 1)
                for row, behind, keying in zip(leaving, left_behind, erasings, strict=True)
            )
        typed = between(eased, ERASING, 1)
        return tuple(
            keyed_row(row, behind, keying, keying.typed(typed) if keying else 1)
            for row, behind, keying in zip(arriving, to_type_over, typings, strict=True)
        )

    return frame
