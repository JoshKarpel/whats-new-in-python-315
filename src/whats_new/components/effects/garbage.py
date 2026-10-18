"""
The garbage collection: a mark phase, then a sweep. First the arriving slide's characters light up green over the
slide being left, as the collector traces what's reachable: tracing starts from a root, the first character of each
cluster of text, and spreads to its neighbors a step at a time, so each word, line and block lights up from its
start outward. Then a sweep line tagged `<GC>` crosses the stage from the side the arriving slide comes from.
Ahead of it the leaving slide's characters still stand among the marked ones; just behind it the unreachable ones
crumble to dust and are gone, and the marked ones cool from green to their own colors.

Every cell's part in this is worked out once: when it's marked, and what it shows each column behind the sweep,
so a frame only looks up where the sweep has got to.
"""

from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
from math import floor
from typing import TypeGuard

from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color
from counterweight.styles.styles import UNSET
from counterweight.styles.styles import AnyColor

from whats_new.components.animation import between
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.effects.characters import backgrounds
from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.swipe import Direction

MARK = 0.4
"""How much of the progress the mark phase takes; the sweep takes the rest."""

REACH = 2
"""How many columns apart two characters can be and still reach each other, so tracing crosses a word's spaces."""

COOLING = 6
"""How many columns behind the sweep line a marked character takes to cool from green to its own colors."""

DUST = ("▒", "░")
"""What an unreachable character crumbles to, one column behind the sweep line and the next, before it's gone."""

REACHABLE = Color.from_hex("#4ade80")
DUSTY = Color.from_hex("#64748b")
LABEL = "<GC>"
LABEL_START = -1
"""Where the label starts, in columns from the sweep line, so its `G` rides the line."""

LINE = "┃"


def visible(glyph: StyledGrapheme | None) -> TypeGuard[StyledGrapheme]:
    """Whether `glyph` is a character to mark or sweep, rather than whitespace or a continuation."""
    return glyph is not None and bool(glyph.grapheme.strip())


def neighbors(x: int, y: int) -> Iterator[tuple[int, int]]:
    """The cells a character at `x`, `y` reaches: within `REACH` columns on its own row and the rows either side."""
    for dy in (-1, 0, 1):
        for dx in range(-REACH, REACH + 1):
            if dx or dy:
                yield x + dx, y + dy


def traced(arriving: Grid) -> dict[tuple[int, int], int]:
    """
    How many steps the trace takes to reach each of the arriving slide's characters, by cell: breadth first from a
    root, the first character in reading order of each cluster the trace hasn't reached yet.
    """
    characters = {(x, y) for y, row in enumerate(arriving) for x, glyph in enumerate(row) if visible(glyph)}
    depths: dict[tuple[int, int], int] = {}
    for root in sorted(characters, key=lambda cell: (cell[1], cell[0])):
        if root in depths:
            continue
        depths[root] = 0
        frontier = deque([root])
        while frontier:
            cell = frontier.popleft()
            for reached in neighbors(*cell):
                if reached in characters and reached not in depths:
                    depths[reached] = depths[cell] + 1
                    frontier.append(reached)
    return depths


def marks(arriving: Grid) -> tuple[tuple[float, ...], ...]:
    """
    For each cell, how far the progress has to get to mark it: within the mark phase for a character, by how
    deep the trace found it, and never for anything else. A continuation is marked with the grapheme it's half of.
    """
    depths = traced(arriving)
    deepest = max(depths.values(), default=0)
    never = float("inf")
    rows: list[tuple[float, ...]] = []
    for y, row in enumerate(arriving):
        cells: list[float] = []
        for x, glyph in enumerate(row):
            at = (x - 1, y) if glyph is None else (x, y)
            depth = depths.get(at)
            cells.append(never if depth is None else MARK * depth / (deepest + 1))
        rows.append(tuple(cells))
    return tuple(rows)


def cooled(glyph: StyledGrapheme, warmth: float) -> StyledGrapheme:
    """
    `glyph` part way from marked green to its own color, `warmth` of the way back to green. A color a terminal
    picks, which can't be blended, stays green until it's half cool.
    """
    return StyledGrapheme(
        grapheme=glyph.grapheme, style=glyph.style | CellStyle(foreground=cooled_color(glyph, warmth))
    )


def cooled_color(glyph: StyledGrapheme, warmth: float) -> AnyColor | UNSET:
    """`cooled`'s foreground: a blend where the color can be blended, and a switch at halfway where it can't."""
    own = glyph.style.foreground
    if isinstance(own, Color):
        return own.blend(REACHABLE, warmth)
    return REACHABLE if warmth > 0.5 else own


@dataclass(frozen=True, slots=True)
class Cell:
    """
    What one cell shows at each stage of the collection: `leaving` until it's marked at `marked_at`, then `marked`;
    `swept[b - 1]` with the sweep line `b` columns ahead of it, for `b` up to `COOLING`; and `arriving` after that.
    """

    leaving: StyledGrapheme | None
    marked: StyledGrapheme | None
    marked_at: float
    swept: tuple[StyledGrapheme | None, ...]
    arriving: StyledGrapheme | None


def cell_of(
    leaving: StyledGrapheme | None, arriving: StyledGrapheme | None, behind: StyledGrapheme, marked_at: float
) -> Cell:
    """
    One cell's stages, given what's there on each slide, the leaving slide's background `behind` it, and when it's
    marked. A cell with no character to mark keeps the leaving slide's until the sweep; one whose leaving character
    is unreachable crumbles to dust in the arriving slide's background.
    """
    if visible(arriving):
        marked = StyledGrapheme(
            grapheme=arriving.grapheme,
            style=CellStyle(foreground=REACHABLE, background=behind.style.background, bold=True),
        )
        swept = tuple(cooled(arriving, 1 - columns / COOLING) for columns in range(1, COOLING + 1))
        return Cell(leaving=leaving, marked=marked, marked_at=marked_at, swept=swept, arriving=arriving)
    if not visible(leaving) or arriving is None:
        return Cell(
            leaving=leaving, marked=leaving, marked_at=marked_at, swept=(arriving,) * COOLING, arriving=arriving
        )
    dust = tuple(
        StyledGrapheme(grapheme=grain, style=CellStyle(foreground=DUSTY, background=arriving.style.background))
        for grain in DUST
    )
    swept = (*dust, *(arriving,) * (COOLING - len(DUST)))
    return Cell(leaving=leaving, marked=leaving, marked_at=marked_at, swept=swept, arriving=arriving)


def garbage(leaving: Grid, arriving: Grid, direction: Direction) -> Frames:
    """
    The garbage collection's frames. The sweep line starts just off the stage on the side the arriving slide comes
    from, label and all, and ends past the other side by enough that the last column has cooled.
    """
    width, height = dimensions(leaving)
    when = marks(arriving)
    under, over = backgrounds(leaving), backgrounds(arriving)
    cells = tuple(
        tuple(cell_of(old, new, back, at) for old, new, back, at in zip(before, after, behind, row, strict=True))
        for before, after, behind, row in zip(leaving, arriving, under, when, strict=True)
    )
    # How far each column is from the edge the sweep starts at, so the sweep can count columns behind it.
    from_start = tuple((width - 1 - x if direction is Direction.NEXT else x) for x in range(width))
    start = -(len(LABEL) + LABEL_START)
    end = width + COOLING
    middle = height // 2
    label_style = CellStyle(foreground=Color.from_hex("#000000"), background=PYTHON_YELLOW, bold=True)

    def shown(cell: Cell, behind: int, t: float) -> StyledGrapheme | None:
        if behind < 0:
            return cell.marked if cell.marked_at < t else cell.leaving
        if 0 < behind <= COOLING:
            return cell.swept[behind - 1]
        # Under the sweep line itself too, which is drawn over it.
        return cell.arriving

    def frame(t: float) -> Grid:
        line = floor(start + between(t, MARK, 1) * (end - start))
        behind = tuple(line - column for column in from_start)
        rows = [[shown(cell, back, t) for cell, back in zip(row, behind, strict=True)] for row in cells]
        line_x = width - 1 - line if direction is Direction.NEXT else line
        if 0 <= line_x < width:
            for y, row in enumerate(rows):
                row[line_x] = StyledGrapheme(
                    grapheme=LINE,
                    style=CellStyle(foreground=PYTHON_YELLOW, background=over[y][line_x].style.background),
                )
        if height:
            for offset, character in enumerate(LABEL, start=line_x + LABEL_START):
                if 0 <= offset < width:
                    rows[middle][offset] = StyledGrapheme(grapheme=character, style=label_style)
        return tuple(tuple(row) for row in rows)

    return frame
