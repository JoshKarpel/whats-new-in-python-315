"""
The diff: the transition as a unified diff of the two slides, row by row. Rows the slides share stay put as context;
each row only the leaving slide has turns red behind a `-` gutter, its replacement from the arriving slide is
inserted under it in green behind a `+`, and then the red row is deleted and the green one settles into the arriving
slide's own colors.

The listing is the two slides' rows matched the way `difflib` matches lines, with each replaced row's `+` right
under its `-` rather than after the whole hunk's, so the change reads pair by pair. A sweep moves down the listing,
each row taking its turn a little after the one above. While a `+` is in and its `-` not yet out, the listing is
longer than the stage, and the rows below are pushed down off its bottom edge, to come back up as the `-` rows go.
The direction plays no part: a diff reads top to bottom either way.
"""

from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import Enum
from itertools import zip_longest
from typing import assert_never

from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color

from whats_new.components.animation import between
from whats_new.components.crossing import SPACE
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.easing import Easing
from whats_new.components.swipe import Direction

type Row = tuple[StyledGrapheme | None, ...]

REMOVED = CellStyle(foreground=Color.from_hex("#ffa198"), background=Color.from_hex("#4a1d1f"))
"""A deleted row's colors, as GitHub's dark theme draws a diff's."""
ADDED = CellStyle(foreground=Color.from_hex("#7ee787"), background=Color.from_hex("#173a22"))
"""An added row's colors, as GitHub's dark theme draws a diff's."""

SPREAD = 0.6
"""How much of the eased progress the rows' turns are spread over, top to bottom; each takes the rest."""
MARKED = 0.15
"""How far through its turn a deleted row turns red."""
INSERTED = 0.3
"""How far through its turn an added row is inserted, in green: after its deleted row is red, before it's gone."""
DELETED = 0.6
"""How far through its turn a deleted row is gone."""
SETTLED = 0.8
"""How far through its turn an added row takes the arriving slide's colors."""


class Change(Enum):
    """What the diff says of a row: in both slides, only the leaving one, or only the arriving one."""

    CONTEXT = " "
    REMOVED = "-"
    ADDED = "+"


@dataclass(frozen=True, slots=True)
class Line:
    """
    One row of the listing: the slide's own `row`, how it shows in the diff (`marked`), and when its turn
    in the sweep comes, from 0 for the top of the listing up to (not including) 1.
    """

    change: Change
    row: Row
    marked: Row
    turn: float

    def shown(self, progress: float) -> Row | None:
        """The row as it shows `progress` of the way through the sweep, or `None` while it's out of the listing."""
        along = between(progress, self.turn * SPREAD, self.turn * SPREAD + 1 - SPREAD)
        match self.change:
            case Change.CONTEXT:
                return self.row
            case Change.REMOVED:
                if along < MARKED:
                    return self.row
                return self.marked if along < DELETED else None
            case Change.ADDED:
                if along < INSERTED:
                    return None
                return self.marked if along < SETTLED else self.row
            case _ as unreachable:
                assert_never(unreachable)


def marked(row: Row, change: Change, style: CellStyle) -> Row:
    """
    `row` as a diff line in `style`, its whole width tinted, behind its gutter: the first cell, which a slide
    leaves blank for a margin, so every character stays where the slide put it.
    """
    if not row:
        return row
    gutter = StyledGrapheme(grapheme=change.value, style=style | CellStyle(bold=True))
    return (
        gutter,
        *(None if glyph is None else StyledGrapheme(grapheme=glyph.grapheme, style=style) for glyph in row[1:]),
    )


def is_blank(row: Row) -> bool:
    """Whether `row` has no characters, only whitespace, whatever its backgrounds."""
    return all(glyph is None or not glyph.grapheme.strip() for glyph in row)


def listing(leaving: Grid, arriving: Grid) -> tuple[Line, ...]:
    """
    The unified diff of `leaving` into `arriving`, row by row, each replaced row's `+` straight after its `-`.
    The lines take their turns in order, a replaced row and its replacement together, so the `+` is always in
    before the `-` has gone, however short the listing.
    """
    steps: list[tuple[tuple[Change, Row], ...]] = []
    # Blank rows only extend a match, never anchor one: slides have so many that matching them splits a slide's
    # change into a block of deletions far from its block of insertions, rather than rows replacing rows.
    matcher = SequenceMatcher(is_blank, leaving, arriving, autojunk=False)
    for _, before_start, before_stop, after_start, after_stop in matcher.get_opcodes():
        before, after = leaving[before_start:before_stop], arriving[after_start:after_stop]
        if before == after:
            steps.extend(((Change.CONTEXT, row),) for row in before)
            continue
        for removed, added in zip_longest(before, after):
            step = []
            if removed is not None:
                step.append((Change.REMOVED, removed))
            if added is not None:
                step.append((Change.ADDED, added))
            steps.append(tuple(step))
    styles = {Change.CONTEXT: CellStyle(), Change.REMOVED: REMOVED, Change.ADDED: ADDED}
    return tuple(
        Line(change=change, row=row, marked=marked(row, change, styles[change]), turn=index / len(steps))
        for index, step in enumerate(steps)
        for change, row in step
    )


def diff(leaving: Grid, arriving: Grid, direction: Direction, easing: Easing) -> Frames:
    """
    The diff's frames: the listing as far as the stage shows it, `easing` setting the sweep's pace. Whenever the
    listing is shorter than the stage, as when a deleted row has gone a frame before its replacement comes in,
    blank rows fill the bottom.
    """
    width, height = dimensions(leaving)
    lines = listing(leaving, arriving)
    blank: Row = (SPACE,) * width

    def frame(t: float) -> Grid:
        eased = easing(t)
        shown = [row for line in lines if (row := line.shown(eased)) is not None][:height]
        return (*shown, *(blank,) * (height - len(shown)))

    return frame
