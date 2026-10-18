"""
Decay: the leaving slide crumbles cell by cell through ever lighter shade blocks down to dust, and the arriving slide
builds back up out of the dust through ever heavier ones. Each cell takes its own turn, set by a smooth noise field
tilted toward the side the arriving slide comes from, so the decay ripples across the slide in patches and fronts
rather than flickering everywhere at once.

A cell decays in its leaving character's color and rebuilds in its arriving one's, so text crumbles in its own color;
an empty cell crumbles in a dim dust color, which is what makes the ripple visible across the slide's empty spaces.
"""

import random
from functools import cache
from math import floor

from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color
from counterweight.styles.styles import UNSET
from counterweight.styles.styles import AnyColor

from whats_new.components.crossing import CELL_ASPECT
from whats_new.components.crossing import SPACE
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.easing import Easing
from whats_new.components.effects.masks import Thresholds
from whats_new.components.swipe import Direction

CRUMBLING = ("▓", "▒", "░")
"""The shades a cell decays through, heaviest first; it rebuilds through them in reverse."""
DUST = "·"
"""What a cell is at the bottom of its decay, between the two slides."""
DUST_COLOR = Color.from_hex("#334155")
"""The color an empty cell decays in: Tailwind's slate 700, dim on the deck's black, but there."""
SPAN = 0.3
"""How much of the eased progress each cell takes to go from the leaving character to the arriving one."""
STEPS = 2 * len(CRUMBLING) + 1
"""How many steps a cell shows between its two characters: down the shades, the dust, and back up."""
TILT = 0.45
"""How much of a cell's turn comes from where it is across the slide rather than from the noise."""
WAVELENGTHS = ((24.0, 0.65), (8.0, 0.35))
"""The noise's octaves: how many columns across each one's features are, and how much it counts for."""


def lattice_noise(width: int, height: int, wavelength: float, chance: random.Random) -> list[list[float]]:
    """
    Smooth value noise over a `width` by `height` picture, from 0 to 1: random values on a lattice `wavelength`
    columns apart (and as far apart on screen vertically), eased between, so neighboring cells get similar values.
    """
    rows_apart = wavelength / CELL_ASPECT
    columns, rows = int(width / wavelength) + 2, int(height / rows_apart) + 2
    knots = [[chance.random() for _ in range(columns)] for _ in range(rows)]

    def smooth(fraction: float) -> float:
        """Smoothstep, so the noise has no creases at the lattice's lines."""
        return fraction * fraction * (3 - 2 * fraction)

    def at(x: int, y: int) -> float:
        """The noise at cell `x`, `y`: its four surrounding knots, blended by how near it is to each."""
        across, down = x / wavelength, y / rows_apart
        left, top = floor(across), floor(down)
        horizontal, vertical = smooth(across - left), smooth(down - top)
        upper = knots[top][left] + (knots[top][left + 1] - knots[top][left]) * horizontal
        lower = knots[top + 1][left] + (knots[top + 1][left + 1] - knots[top + 1][left]) * horizontal
        return upper + (lower - upper) * vertical

    return [[at(x, y) for x in range(width)] for y in range(height)]


@cache
def rippling(width: int, height: int, direction: Direction) -> Thresholds:
    """
    Each cell's turn to start decaying, from 0 up to `1 - SPAN`, so every cell has finished by the end:
    smooth noise plus a tilt from the side the arriving slide comes from, spread evenly over that range by rank,
    so the decay moves at a steady pace whatever the noise happened to be.
    Cached, since the stage is the same size from one transition to the next.
    """
    chance = random.Random(315)
    octaves = [(lattice_noise(width, height, wavelength, chance), weight) for wavelength, weight in WAVELENGTHS]
    count = width * height

    def raw(x: int, y: int) -> float:
        """Cell `x`, `y`'s place in the order the cells decay in, before it's spread out by rank."""
        noise = sum(weight * field[y][x] for field, weight in octaves)
        across = (width - 1 - x if direction is Direction.NEXT else x) / max(width - 1, 1)
        return (1 - TILT) * noise + TILT * across

    ranked = sorted(range(count), key=lambda cell: raw(cell % width, cell // width))
    turns = [0.0] * count
    for rank, cell in enumerate(ranked):
        turns[cell] = rank / count * (1 - SPAN)
    return tuple(tuple(turns[y * width : (y + 1) * width]) for y in range(height))


@cache
def shaded(grapheme: str, foreground: AnyColor | UNSET, background: AnyColor | UNSET) -> StyledGrapheme:
    """A shade block or dust, `foreground` on `background`."""
    return StyledGrapheme(grapheme=grapheme, style=CellStyle(foreground=foreground, background=background))


def ink_of(glyph: StyledGrapheme | None) -> AnyColor | UNSET:
    """The color a cell decays or rebuilds in: its character's own, or the dust color for an empty one."""
    if glyph is None or not glyph.grapheme.strip():
        return DUST_COLOR
    return glyph.style.foreground


def stages(before: StyledGrapheme | None, after: StyledGrapheme | None) -> tuple[StyledGrapheme | None, ...]:
    """
    Everything one cell shows, in order: `before`, down the shades in its color and background, the dust, back up
    in `after`'s, and `after`. A continuation cell decays as the empty cell its grapheme leaves behind.
    """
    down_ink, down_background = ink_of(before), (before or SPACE).style.background
    up_ink, up_background = ink_of(after), (after or SPACE).style.background
    return (
        before,
        *(shaded(shade, down_ink, down_background) for shade in CRUMBLING),
        shaded(DUST, DUST_COLOR, up_background),
        *(shaded(shade, up_ink, up_background) for shade in reversed(CRUMBLING)),
        after,
    )


def decay(leaving: Grid, arriving: Grid, direction: Direction, easing: Easing) -> Frames:
    """
    Decay's frames. Each cell is the leaving character until the eased progress reaches its turn, the arriving one
    `SPAN` later, and in between, the step of its decay that far through.
    """
    width, height = dimensions(leaving)
    turns = rippling(width, height, direction)
    cells = tuple(
        tuple(stages(before, after) for before, after in zip(old, new, strict=True))
        for old, new in zip(leaving, arriving, strict=True)
    )
    last = STEPS + 1

    def frame(t: float) -> Grid:
        eased = easing(t)
        return tuple(
            tuple(
                steps[0]
                if (through := (eased - turn) / SPAN) <= 0
                else steps[last]
                if through >= 1
                else steps[1 + int(through * STEPS)]
                for steps, turn in zip(row, at, strict=True)
            )
            for row, at in zip(cells, turns, strict=True)
        )

    return frame
