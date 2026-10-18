"""
Pixelate: the leaving slide breaks up into ever chunkier blocks of color, the blocks fade from its colors to the
arriving slide's, and they break down again into ever finer ones until the arriving slide is sharp.

Each cell is two pixels, one above the other, drawn as an upper half block in the top pixel's color over the bottom
pixel's, so a pixel is about as tall on screen as it is wide and a block of pixels is square. A pixel of a slide is
the color of its cell's character, if it has one, or of its background. A block is the average of its pixels, and the
blocks are laid out from the middle of the stage, so a slide centered on the stage stays centered as it coarsens.
"""

from collections.abc import Callable
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from itertools import accumulate
from math import ceil
from operator import attrgetter

from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color
from counterweight.styles.styles import resolve_cell_style
from counterweight.styles.styles import rgb_of

from whats_new.components.crossing import SPACE
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.easing import Easing
from whats_new.components.swipe import Direction

UPPER_HALF = "▀"
SIZES = (2, 3, 4, 6, 8, 12)
"""How many pixels across (and down) a block is at each step of coarseness, finest first."""
COARSENING = 0.4
"""
How much of the eased progress the leaving slide takes to coarsen to the largest blocks, and the arriving slide
to sharpen from them; the blocks fade from one slide's colors to the other's in between.
"""
SCREENSHOT_FOREGROUND = Color.from_name("white")
SCREENSHOT_BACKGROUND = Color.from_name("black")
"""The terminal's default colors, as a screenshot draws them."""

type Colors = tuple[tuple[Color, ...], ...]
"""The color each cell of a picture reads as, row by row: two pixels, one above the other, of that color."""


@cache
def color_of(glyph: StyledGrapheme) -> Color:
    """The color a cell reads as from a distance: its character's, if it has one, or its background's."""
    style = resolve_cell_style(glyph.style)
    if glyph.grapheme.strip():
        return rgb_of(style.foreground, SCREENSHOT_FOREGROUND)
    return rgb_of(style.background, SCREENSHOT_BACKGROUND)


def colors_of(grid: Grid) -> Colors:
    """The color of each of `grid`'s cells. A continuation cell is the color of the grapheme to its left."""
    return tuple(
        tuple(color_of(glyph if glyph is not None else row[x - 1] or SPACE) for x, glyph in enumerate(row))
        for row in grid
    )


type Table = tuple[tuple[int, ...], ...]


def running_totals(cells: Colors, channel: Callable[[Color], int]) -> Table:
    """
    The total of `channel` over every pixel above and left of each point between pixels, so the total over any
    rectangle of pixels is four lookups whatever its size. Each cell is two pixels, one above the other.
    """
    width = len(cells[0]) if cells else 0
    running = [0] * (width + 1)
    totals = [tuple(running)]
    for row in cells:
        across = list(accumulate(map(channel, row), initial=0))
        for _ in range(2):
            running = [above + left for above, left in zip(running, across, strict=True)]
            totals.append(tuple(running))
    return tuple(totals)


@dataclass(frozen=True, slots=True)
class Totals:
    """A picture's running totals of each channel, so any block's average color is a few lookups."""

    red: Table
    green: Table
    blue: Table

    @classmethod
    def of(cls, cells: Colors) -> Totals:
        """The running totals of `cells`' pixels."""
        return cls(
            red=running_totals(cells, attrgetter("red")),
            green=running_totals(cells, attrgetter("green")),
            blue=running_totals(cells, attrgetter("blue")),
        )

    def average(self, left: int, top: int, right: int, bottom: int) -> Color:
        """The average color of the pixels from `left` and `top` up to (not including) `right` and `bottom`."""
        count = (right - left) * (bottom - top)
        red, green, blue = self.red, self.green, self.blue
        return Color(
            red=(red[bottom][right] - red[top][right] - red[bottom][left] + red[top][left]) // count,
            green=(green[bottom][right] - green[top][right] - green[bottom][left] + green[top][left]) // count,
            blue=(blue[bottom][right] - blue[top][right] - blue[bottom][left] + blue[top][left]) // count,
        )


@dataclass(frozen=True, slots=True)
class Blocks:
    """
    A picture divided into blocks `size` pixels square: where each block is, and which block each cell's top
    and bottom pixels fall in, row by row, as indices into the blocks.
    """

    size: int
    bounds: tuple[tuple[int, int, int, int], ...]
    """Each block's pixels, as the `left`, `top`, `right` and `bottom` of `Totals.average`, cut to the picture."""
    tops: tuple[tuple[int, ...], ...]
    bottoms: tuple[tuple[int, ...], ...]

    def averages(self, totals: Totals) -> tuple[Color, ...]:
        """Each block's color: the average of its pixels."""
        return tuple(totals.average(*bounds) for bounds in self.bounds)

    def drawn(self, colors: Sequence[Color]) -> Grid:
        """The blocks, each in its color from `colors`, as cells of upper half blocks."""
        pairs = tuple(
            tuple((colors[top], colors[bottom]) for top, bottom in zip(uppers, lowers, strict=True))
            for uppers, lowers in zip(self.tops, self.bottoms, strict=True)
        )
        glyphs = {
            (top, bottom): StyledGrapheme(grapheme=UPPER_HALF, style=CellStyle(foreground=top, background=bottom))
            for top, bottom in {pair for row in pairs for pair in row}
        }
        return tuple(tuple(glyphs[pair] for pair in row) for row in pairs)


@cache
def blocks_of(size: int, width: int, height: int) -> Blocks:
    """
    `size`-pixel blocks over a `width` by `height` picture of cells, centered on it.
    Cached, since the stage is the same size from one transition to the next.
    """
    across, down = ceil(width / size), ceil(2 * height / size)
    left, top = (across * size - width) // 2, (down * size - 2 * height) // 2

    def block(x: int, y: int) -> int:
        """Which block pixel `x`, `y` falls in."""
        return (y + top) // size * across + (x + left) // size

    def bounds(column: int, row: int) -> tuple[int, int, int, int]:
        """The pixels of the block in `column` and `row` of blocks, cut to the picture."""
        return (
            max(column * size - left, 0),
            max(row * size - top, 0),
            min((column + 1) * size - left, width),
            min((row + 1) * size - top, 2 * height),
        )

    return Blocks(
        size=size,
        bounds=tuple(bounds(column, row) for row in range(down) for column in range(across)),
        tops=tuple(tuple(block(x, 2 * y) for x in range(width)) for y in range(height)),
        bottoms=tuple(tuple(block(x, 2 * y + 1) for x in range(width)) for y in range(height)),
    )


def coarsenings(grid: Grid, totals: Totals, levels: Sequence[Blocks]) -> tuple[Grid, ...]:
    """`grid` itself, then drawn in blocks at each of `levels`, finest first, from its `totals`."""
    return (grid, *(blocks.drawn(blocks.averages(totals)) for blocks in levels))


def coarseness(progress: float) -> int:
    """
    How coarse a slide is `progress` of the way through its coarsening, as an index into its `coarsenings`:
    0, the slide itself, at the start or before it, and the largest blocks once it's done.
    """
    return max(0, min(ceil(progress / COARSENING * len(SIZES)), len(SIZES)))


def pixelate(leaving: Grid, arriving: Grid, direction: Direction, easing: Easing) -> Frames:
    """
    Pixelate's frames: the leaving slide coarsening, then the largest blocks fading between the slides' colors,
    then the arriving slide sharpening, each stage by the eased progress.
    """
    width, height = dimensions(leaving)
    levels = tuple(blocks_of(size, width, height) for size in SIZES)
    coarsest = levels[-1]
    leaving_totals, arriving_totals = Totals.of(colors_of(leaving)), Totals.of(colors_of(arriving))
    before, after = coarsenings(leaving, leaving_totals, levels), coarsenings(arriving, arriving_totals, levels)
    first, last = coarsest.averages(leaving_totals), coarsest.averages(arriving_totals)

    def frame(t: float) -> Grid:
        eased = easing(t)
        if eased <= COARSENING:
            return before[coarseness(eased)]
        if eased >= 1 - COARSENING:
            return after[coarseness(1 - eased)]
        fading = (eased - COARSENING) / (1 - 2 * COARSENING)
        return coarsest.drawn([old.blend(new, fading) for old, new in zip(first, last, strict=True)])

    return frame
