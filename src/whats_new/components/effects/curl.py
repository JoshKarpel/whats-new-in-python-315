"""
The page curl: the slide being left peels away from a bottom corner, as a page turned by hand, uncovering the
arriving slide beneath. Moving to the next slide it peels from the bottom right, and moving back from the bottom left.

A straight fold, square to the diagonal from that corner, sweeps across to the far corner. Behind the fold the page is
gone and the arriving slide shows, darkened in a soft shadow just behind the fold. In front of it, a band of the page
lies folded back over itself: the leaving slide's back, each cell the one mirrored across the fold, faded as text seen
through paper. The geometry is worked out on screen, where a cell is about twice as tall as it is wide,
so the fold runs at the angle it looks to.

"""

from functools import lru_cache
from math import floor
from math import hypot

from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color

from whats_new.components.crossing import CELL_ASPECT
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.easing import ease_in_out
from whats_new.components.effects.shading import BLACK
from whats_new.components.effects.shading import GLYPHS_KEPT
from whats_new.components.effects.shading import blended
from whats_new.components.effects.shading import shaded
from whats_new.components.swipe import Direction

PAPER = Color.from_hex("#e2e8f0")
"""The color the back of the page is tinted toward: a pale slate, as the slides' borders are."""

SHADOW = 6.0
"""How far behind the fold, on screen (in cell widths), the page's shadow reaches across the arriving slide."""
SHADOW_DEPTH = 5
"""How many of `SHADES` the shadow darkens by right at the fold."""
FLAP = 18.0
"""How wide, on screen, the band of the page folded back over itself gets, as it curls rather than lies flat."""
BACK_TINT = 2
"""How many of `SHADES` the back of the page is tinted toward `PAPER`."""
BACK_FADE = 5
"""How many of `SHADES` the characters on the back of the page fade toward its tint, as text seen through paper."""


@lru_cache(maxsize=GLYPHS_KEPT)
def back_of(glyph: StyledGrapheme | None) -> StyledGrapheme:
    """
    How `glyph` shows on the back of the page: its background tinted toward `PAPER`, so the folded band reads as a
    surface even over a blank slide, and its character faded toward that, as print seen through from behind.
    """
    if glyph is None:
        return StyledGrapheme(grapheme=" ")
    style = glyph.style
    paper = blended(style.background, PAPER, BACK_TINT)
    # A slide's own background is black wherever it isn't an RGB color.
    faded = blended(style.foreground, paper if isinstance(paper, Color) else BLACK, BACK_FADE)
    return StyledGrapheme(grapheme=glyph.grapheme, style=style | CellStyle(foreground=faded, background=paper))


def curl(leaving: Grid, arriving: Grid, direction: Direction) -> Frames:
    """
    The page curl's frames. The fold starts at the corner, so the first frame is all page, and the progress, easing
    in and out as a hand turns a page, carries it past the far corner by the shadow's reach, so the last is all
    arriving slide, shadow gone.
    """
    width, height = dimensions(leaving)
    diagonal = hypot(width, height * CELL_ASPECT)
    # Nothing to peel, and no diagonal to peel it along.
    if diagonal == 0:
        return lambda progress: leaving
    corner_x = width if direction is Direction.NEXT else 0
    corner_y = height * CELL_ASPECT
    # Toward the far corner, on screen: how far a point is along this from the corner is which side of the fold it's on.
    toward_x, toward_y = (width - 2 * corner_x) / diagonal, -corner_y / diagonal
    along = tuple(
        tuple((x + 0.5 - corner_x) * toward_x + ((y + 0.5) * CELL_ASPECT - corner_y) * toward_y for x in range(width))
        for y in range(height)
    )

    def back(x: int, y: int, past: float) -> StyledGrapheme | None:
        """
        The back of the page over cell `x`, `y`, `past` beyond the fold: the cell mirrored across the fold along its
        row, or nothing where that's off the page, as beyond the folded corner's edge. Mirrored along the row rather
        than square to the fold, since a slanted mirror maps neighbouring cells half a cell apart, doubling some
        characters and dropping others, where along the row each lands in a cell of its own.
        """
        mirrored = floor(x + 0.5 - 2 * past / toward_x)
        if not 0 <= mirrored < width:
            return None
        return back_of(leaving[y][mirrored])

    def frame(t: float) -> Grid:
        fold = ease_in_out(t) * (diagonal + SHADOW)
        flap = min(fold, FLAP)
        rows: list[tuple[StyledGrapheme | None, ...]] = []
        for y, (before, after, distances) in enumerate(zip(leaving, arriving, along, strict=True)):
            row: list[StyledGrapheme | None] = []
            for x, distance in enumerate(distances):
                if distance < fold - SHADOW:
                    row.append(after[x])
                elif distance < fold:
                    darkness = int((1 - (fold - distance) / SHADOW) * (SHADOW_DEPTH + 1))
                    row.append(shaded(after[x], BLACK, darkness))
                elif distance < fold + flap and (folded := back(x, y, distance - fold)) is not None:
                    row.append(folded)
                else:
                    row.append(before[x])
            rows.append(tuple(row))
        return tuple(rows)

    return frame
