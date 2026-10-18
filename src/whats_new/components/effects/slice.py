"""
The slice, as `deck[3:12]` cuts a sequence: the slide is cut along the grid's rows, and each band slides off sideways,
pulling the same band of the grid in behind it, alternate bands going opposite ways. The band holding the slide's
thumbnail goes first, and the others follow outward from it. Each band moves whole, so it eases in and out.
"""

from counterweight.elements import StyledGrapheme

from whats_new.components.animation import between
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import Tiles
from whats_new.components.crossing import dimensions
from whats_new.components.easing import ease_in_out

STAGGER = 0.15
"""How much later each band starts sliding than the one before it, nearer the slide's thumbnail."""


def bands(tiles: Tiles, height: int) -> tuple[int, ...]:
    """Where each band starts, and the last ends: the line naming the section, then each row of thumbnails."""
    return tuple(
        sorted(
            {
                0,
                height,
                tiles.header.bottom,
                *(edge for region in tiles.thumbnails for edge in (region.top, region.bottom)),
            }
        )
    )


def sliced(slide: Grid, grid: Grid, tiles: Tiles) -> Frames:
    """
    The slice's frames. No band has moved at first, so the first frame is the slide; every one has slid all the way
    by the end, so the last is the grid.
    """
    width, height = dimensions(slide)
    edges = bands(tiles, height)
    kept = edges.index(tiles.chosen.top)
    count = len(edges) - 1
    delays = tuple(abs(band - kept) for band in range(count))
    sliding = 1 - max(delays) * STAGGER
    # Which band each row is in, and which way that band goes: the slide's own band to the left.
    band_of = tuple(next(band for band in range(count) if edges[band] <= y < edges[band + 1]) for y in range(height))
    ways = tuple(1 if (band - kept) % 2 == 0 else -1 for band in range(count))

    def frame(t: float) -> Grid:
        offsets = tuple(
            round(ease_in_out(between(t, delay * STAGGER, delay * STAGGER + sliding)) * width) for delay in delays
        )

        def row(y: int) -> tuple[StyledGrapheme | None, ...]:
            band = band_of[y]
            # Going left, the slide's band is followed in by the grid's from the right; going right, from the left.
            shift = offsets[band] * ways[band]
            return tuple(
                slide[y][x + shift] if 0 <= x + shift < width else grid[y][x + shift - width * ways[band]]
                for x in range(width)
            )

        return tuple(row(y) for y in range(height))

    return frame
