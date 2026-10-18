"""
The ripples: three to five drops land at once, spread out over the stage, and a circular wave spreads out from each,
all at the same speed, until they have crossed the whole stage. A cell shows the arriving slide once any of the fronts
has passed it, so the arriving slide opens in several circles that grow into each other. The water near a front is
still moving: behind it each character is pushed in or out along the line from its drop by a sine wave that dies away
with distance behind the front, so the arriving slide wobbles as it's uncovered and settles once the front has gone
by. Where the waves overlap their pushes add up, so they interfere.

Where the drops land is drawn once, the same way every run: the stage is cut into a grid of patches, a few of them
picked, and a drop put somewhere near the middle of each, so no two drops bunch up.

How far each cell is from each drop, and which way is outward, is worked out once; a frame only finds the cells close
behind each front and looks up how far the wave pushes them.
"""

import random
from bisect import bisect_left
from bisect import bisect_right
from dataclasses import dataclass
from math import exp
from math import hypot
from math import pi
from math import sin

from whats_new.components.crossing import CELL_ASPECT
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.effects.characters import Point
from whats_new.components.swipe import Direction

WAVELENGTH = 7.0
"""How far apart the wave's crests are, in columns (a row counting as `CELL_ASPECT` columns, as on screen)."""

AMPLITUDE = 2.0
"""How many columns the wave pushes a character at most."""

DAMPING = 4.0
"""How many columns behind the front the wave's push takes to fall to about a third."""

TAIL = 14.0
"""How far behind the front the wave reaches, in columns; past it the water is still and the arriving slide settled."""

STEPS = 8
"""How many steps of the wave's shape to work out per column behind the front."""

PROFILE = tuple(
    AMPLITUDE * sin(2 * pi * step / STEPS / WAVELENGTH) * exp(-step / STEPS / DAMPING)
    # One step more than the tail holds: a cell found just inside the tail can round to exactly its end.
    for step in range(int(TAIL * STEPS) + 1)
)
"""How far the wave pushes a character outward at each step behind the front: zero at the front, then a damped sine."""

SETTLING = 0.3
"""
How much of the end of the progress the water takes to settle, every push dying away to nothing, so the last
frame is unmoved even where another drop's wave is still crossing it.
"""

PATCHES = (3, 2)
"""How many patches across and down the stage is cut into, at most one drop to a patch."""

FEWEST, MOST = 3, 5
"""How many drops there can be."""

INSET = 0.2
"""How far in from each side of its patch a drop lands at least, as a share of the patch, so drops in neighboring
patches stay apart."""


def landings(width: int, height: int) -> tuple[Point, ...]:
    """Where the drops land on a `width` by `height` stage, in cells: one each in a few patches picked at random."""
    chance = random.Random(315)
    across, down = PATCHES
    patches = [(column, row) for row in range(down) for column in range(across)]
    picked = chance.sample(patches, chance.randint(FEWEST, MOST))
    return tuple(
        (
            width * (column + chance.uniform(INSET, 1 - INSET)) / across,
            height * (row + chance.uniform(INSET, 1 - INSET)) / down,
        )
        for column, row in picked
    )


@dataclass(frozen=True, slots=True)
class Wave:
    """
    One drop's wave, by cell, nearest the drop first: each cell's index in the picture read row by row, its distance
    from the drop, and which way is outward from the drop, as columns and rows a unit push moves it.
    """

    cells: tuple[int, ...]
    distances: tuple[float, ...]
    outward: tuple[tuple[float, float], ...]


def wave_from(drop: Point, width: int, height: int) -> Wave:
    """The wave from a drop at `drop`, in cells, over a `width` by `height` stage."""
    measured = []
    for y in range(height):
        for x in range(width):
            across, down = x + 0.5 - drop[0], (y + 0.5 - drop[1]) * CELL_ASPECT
            distance = hypot(across, down)
            unit = (across / distance, down / distance / CELL_ASPECT) if distance else (0.0, 0.0)
            measured.append((distance, y * width + x, unit))
    measured.sort()
    return Wave(
        cells=tuple(cell for _, cell, _ in measured),
        distances=tuple(distance for distance, _, _ in measured),
        outward=tuple(unit for _, _, unit in measured),
    )


def rippling(leaving: Grid, arriving: Grid, drops: tuple[Point, ...]) -> Frames:
    """
    The frames of a wave spreading from each of `drops`, in cells, all at the same speed: fast enough that by the
    end every cell is a whole tail behind the nearest front. The water settles as the end nears, so the last frame
    is the arriving slide, unmoved.
    Each frame shows each cell's own slide, the arriving one once a front has passed it, taken from where the waves
    have pushed the cell's contents from.
    """
    width, height = dimensions(leaving)
    waves = tuple(wave_from(drop, width, height) for drop in drops)
    nearest = [float("inf")] * (width * height)
    for wave in waves:
        for cell, distance in zip(wave.cells, wave.distances, strict=True):
            nearest[cell] = min(nearest[cell], distance)
    reach = max(nearest, default=0.0) + TAIL
    before = tuple(glyph for row in leaving for glyph in row)
    after = tuple(glyph for row in arriving for glyph in row)

    def frame(t: float) -> Grid:
        front = t * reach
        cells = [new if near < front else old for old, new, near in zip(before, after, nearest, strict=True)]
        calm = min(max((1 - t) / SETTLING, 0.0), 1.0)
        pushes: dict[int, tuple[float, float]] = {}
        for wave in waves if calm else ():
            first = bisect_right(wave.distances, front - TAIL)
            last = bisect_left(wave.distances, front)
            for index in range(first, last):
                push = calm * PROFILE[int((front - wave.distances[index]) * STEPS)]
                across, down = wave.outward[index]
                cell = wave.cells[index]
                pushed_across, pushed_down = pushes.get(cell, (0.0, 0.0))
                pushes[cell] = (pushed_across + push * across, pushed_down + push * down)
        for cell, (across, down) in pushes.items():
            y, x = divmod(cell, width)
            from_x = min(max(x - round(across), 0), width - 1)
            from_y = min(max(y - round(down), 0), height - 1)
            source = from_y * width + from_x
            if source != cell:
                cells[cell] = after[source] if nearest[cell] < front else before[source]
        return tuple(tuple(cells[y * width : (y + 1) * width]) for y in range(height))

    return frame


def ripples(leaving: Grid, arriving: Grid, direction: Direction) -> Frames:
    """The ripples' frames. The drops land in the same places whichever way the presenter moved."""
    width, height = dimensions(leaving)
    return rippling(leaving, arriving, landings(width, height))
