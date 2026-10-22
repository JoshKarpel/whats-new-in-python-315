"""
What the effects that move characters about share: where each character is, what a cell shows once its character
has gone, somewhere past the stage's edges to fly to or from, and drawing characters wherever they've got to.

What moves is every cell with something to see: a character, or a cell shaded off the slide's backdrop, such as the
inside of a code box, which moves with the code on it. What stays behind is the backdrop alone.
"""

from collections import Counter
from collections.abc import Iterable

from counterweight.elements import StyledGrapheme
from counterweight.styles import UNSET
from counterweight.styles import AnyColor
from counterweight.styles import CellStyle

from whats_new.components.crossing import CELL_ASPECT
from whats_new.components.crossing import SPACE
from whats_new.components.crossing import Grid
from whats_new.components.crossing import solid
from whats_new.components.swipe import Direction

type Point = tuple[float, float]

type Backgrounds = tuple[tuple[StyledGrapheme, ...], ...]
"""A picture with its characters gone: what characters move over. Never a continuation, so `x` always indexes a cell."""


def backdrop_of(*pictures: Grid) -> AnyColor | UNSET:
    """The background most of `pictures`' cells have: the slides' own, which their content sits on."""
    counts = Counter(solid(glyph.style.background) for picture in pictures for row in picture for glyph in row if glyph)
    return counts.most_common(1)[0][0] if counts else UNSET


def moves(glyph: StyledGrapheme | None, backdrop: AnyColor | UNSET) -> bool:
    """Whether `glyph` is something to see that moves: a visible character, or a cell shaded off the `backdrop`."""
    return glyph is not None and (bool(glyph.grapheme.strip()) or glyph.style.background != backdrop)


def characters(grid: Grid, backdrop: AnyColor | UNSET) -> dict[str, list[tuple[Point, StyledGrapheme]]]:
    """
    Where each cell of `grid` that moves is, grouped by grapheme, in reading order:
    the shaded spaces of a box group under `" "`, so they move to the arriving slide's shaded spaces.
    """
    found: dict[str, list[tuple[Point, StyledGrapheme]]] = {}
    for y, row in enumerate(grid):
        for x, glyph in enumerate(row):
            if glyph is not None and moves(glyph, backdrop):
                found.setdefault(glyph.grapheme, []).append(((x, y), glyph))
    return found


def beyond(point: Point, width: int, height: int, direction: Direction) -> Point:
    """
    Somewhere past the edges of a `width` by `height` stage, straight out from its middle through `point`
    (as it looks on screen, cells being taller than wide), or toward where the slides came from, from the very middle.
    """
    center_x, center_y = width / 2, height / 2
    out_x, out_y = point[0] - center_x, (point[1] - center_y) * CELL_ASPECT
    length = (out_x**2 + out_y**2) ** 0.5
    if length == 0:
        out_x, out_y, length = float(-direction.value), 0.0, 1.0
    reach = width + height * CELL_ASPECT
    return center_x + out_x / length * reach, center_y + out_y / length * reach / CELL_ASPECT


def background(glyph: StyledGrapheme | None, left: StyledGrapheme | None) -> StyledGrapheme:
    """
    What a cell shows with its character gone: whitespace as it is, and anything else as a space in its
    background, or in the background of `left`, the grapheme it's the right half of.
    """
    shown = glyph if glyph is not None else left
    if shown is None:
        return SPACE
    if not shown.grapheme.strip():
        return shown
    return StyledGrapheme(grapheme=" ", style=CellStyle(background=shown.style.background))


def backgrounds(grid: Grid) -> Backgrounds:
    """
    `grid` with its characters gone, its shading kept: what the effects that draw text over a slide's own
    backgrounds draw it over. Never a continuation.
    """
    return tuple(tuple(background(glyph, row[x - 1] if x > 0 else None) for x, glyph in enumerate(row)) for row in grid)


def emptied_cell(
    glyph: StyledGrapheme | None, left: StyledGrapheme | None, backdrop: AnyColor | UNSET
) -> StyledGrapheme:
    """
    What a cell shows once everything that moves has gone: whitespace on the `backdrop` as it is, and anything else
    as a space on the backdrop. `left` is the grapheme a continuation is the right half of.
    """
    shown = glyph if glyph is not None else left
    if shown is None:
        return SPACE
    if not moves(shown, backdrop):
        return shown
    return StyledGrapheme(grapheme=" ", style=CellStyle(background=backdrop))


def emptied(grid: Grid, backdrop: AnyColor | UNSET) -> Backgrounds:
    """
    `grid` with everything that moves gone, shading and all: the `backdrop` alone where anything was,
    which is what moving cells cross. Never a continuation.
    """
    return tuple(
        tuple(emptied_cell(glyph, row[x - 1] if x > 0 else None, backdrop) for x, glyph in enumerate(row))
        for row in grid
    )


def drawn_over(
    behind: Backgrounds, placed: Iterable[tuple[int, int, StyledGrapheme]], backdrop: AnyColor | UNSET
) -> Grid:
    """
    `behind`, with each of `placed` drawn at its `x` and `y`, in order, so a later one covers an earlier one.
    A shaded one keeps its own background, as the box it's part of moves with it; one on the `backdrop`, or with
    no background of its own, takes the background of whatever it's over, so a character crossing a box shows on the box, and one back in its own cell
    looks just as its slide drew it. One anywhere off the stage, even partly, isn't drawn.
    """
    height = len(behind)
    width = len(behind[0]) if behind else 0
    cells: list[list[StyledGrapheme | None]] = [list(row) for row in behind]
    for x, y, glyph in placed:
        if not (0 <= y < height and x >= 0 and x + glyph.width <= width):
            continue
        under = cells[y][x] or behind[y][x]
        if glyph.style.background is UNSET or glyph.style.background == backdrop:
            glyph = StyledGrapheme(
                grapheme=glyph.grapheme, style=glyph.style | CellStyle(background=under.style.background)
            )
        cells[y][x] = glyph
        if glyph.width == 2:
            cells[y][x + 1] = None
    return tuple(tuple(row) for row in cells)
