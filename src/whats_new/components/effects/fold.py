"""
The fold: the slide is a sheet of paper creased along the grid's lines, which folds up, its columns and then its rows,
into the one panel where its thumbnail goes, then turns over to show the grid on its other side and unfolds
as the grid, its rows and then its columns. Each panel folding in squashes toward the crease it folds about and
darkens as it turns from the viewer. Each fold eases in and out, as something moving whole does.
"""

from dataclasses import dataclass
from itertools import pairwise
from math import floor

from counterweight.animation import between
from counterweight.elements import StyledGrapheme

from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import Tiles
from whats_new.components.crossing import dimensions
from whats_new.components.easing import ease_in_out
from whats_new.components.effects.cards import blank
from whats_new.components.effects.characters import backdrop_of
from whats_new.components.effects.shading import BLACK
from whats_new.components.effects.shading import shaded

FOLDED = 6
"""How many of `SHADES` a panel darkens by as it folds flat, turned all the way from the viewer."""


@dataclass(frozen=True, slots=True)
class Axis:
    """
    The creases across one direction of the sheet: where each panel starts, and the last ends,
    and which panel is the one the sheet folds up into.
    """

    edges: tuple[int, ...]
    kept: int

    def folded(self, folding: float) -> tuple[tuple[int, int] | None, ...]:
        """
        What each cell along the axis shows with every other panel `folding` of the way flat against the kept one:
        which cell of the sheet, and how dark, or `None` for none, where the sheet has folded away from.
        """
        sizes = [
            (right - left) * (1 if panel == self.kept else 1 - folding)
            for panel, (left, right) in enumerate(pairwise(self.edges))
        ]
        # The kept panel stays put, and the others fold up against it, from either side.
        starts = [float(self.edges[self.kept])] * len(sizes)
        for panel in range(self.kept - 1, -1, -1):
            starts[panel] = starts[panel + 1] - sizes[panel]
        for panel in range(self.kept + 1, len(sizes)):
            starts[panel] = starts[panel - 1] + sizes[panel - 1]
        darkness = round(folding * FOLDED)

        def at(cell: int) -> tuple[int, int] | None:
            center = cell + 0.5
            for panel, (start, size) in enumerate(zip(starts, sizes, strict=True)):
                if size > 0 and start <= center < start + size:
                    left, right = self.edges[panel], self.edges[panel + 1]
                    source = min(left + floor((center - start) / size * (right - left)), right - 1)
                    return source, 0 if panel == self.kept else darkness
            return None

        return tuple(at(cell) for cell in range(self.edges[-1]))


def axes(tiles: Tiles, width: int, height: int) -> tuple[Axis, Axis]:
    """The creases across and down the sheet: along the grid's lines, the line naming the section a panel of its own."""
    across = sorted({0, width, *(edge for region in tiles.thumbnails for edge in (region.left, region.right))})
    down = sorted(
        {0, height, tiles.header.bottom, *(edge for region in tiles.thumbnails for edge in (region.top, region.bottom))}
    )
    return (
        Axis(edges=tuple(across), kept=across.index(tiles.chosen.left)),
        Axis(edges=tuple(down), kept=down.index(tiles.chosen.top)),
    )


def fold(slide: Grid, grid: Grid, tiles: Tiles) -> Frames:
    """
    The fold's frames: a quarter each to fold the columns and the rows, then to unfold the rows and the columns.
    Nothing folded at either end, the first frame is the slide and the last the grid.
    """
    width, height = dimensions(slide)
    empty = blank(backdrop_of(slide, grid))
    across, down = axes(tiles, width, height)

    def frame(t: float) -> Grid:
        picture = slide if t < 0.5 else grid
        if t < 0.5:
            columns, rows = between(t, 0, 0.25), between(t, 0.25, 0.5)
        else:
            columns, rows = 1 - between(t, 0.75, 1), 1 - between(t, 0.5, 0.75)
        xs, ys = across.folded(ease_in_out(columns)), down.folded(ease_in_out(rows))

        def cell(x: tuple[int, int] | None, y: tuple[int, int] | None) -> StyledGrapheme | None:
            if x is None or y is None:
                return empty
            return shaded(picture[y[0]][x[0]], BLACK, max(x[1], y[1]))

        return tuple(tuple(cell(x, y) for x in xs) for y in ys)

    return frame
