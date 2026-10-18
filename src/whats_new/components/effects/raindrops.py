"""
The raindrops: three to five drops land at once, spread out over the stage, and each spreads a ripple (see `ripple`),
all at the same speed. A cell shows the arriving slide once any of the fronts has passed it, so the arriving slide
opens in several circles that grow into each other, and where the rings meet their pushes add up and interfere.

Where the drops land is drawn once, the same way every run: the stage is cut into a grid of patches, a few of them
picked, and a drop put somewhere near the middle of each, so no two drops bunch up.
"""

import random

from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.easing import Easing
from whats_new.components.effects.characters import Point
from whats_new.components.effects.ripple import rippling
from whats_new.components.swipe import Direction

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


def raindrops(leaving: Grid, arriving: Grid, direction: Direction, easing: Easing) -> Frames:
    """The raindrops' frames. The drops land in the same places whichever way the presenter moved."""
    width, height = dimensions(leaving)
    return rippling(leaving, arriving, easing, landings(width, height))
