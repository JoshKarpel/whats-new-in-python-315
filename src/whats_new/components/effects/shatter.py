"""
The shatter: the slide being left cracks into shards, like a pane of glass, and the shards fly apart and fall away,
uncovering the arriving slide behind them.

The shards are the Voronoi cells of a few dozen points scattered over the stage (the same points every time): each cell
of the picture belongs to the shard of the point nearest it on screen, where cells are twice as tall as wide, and the
right half of a two-cell-wide grapheme to the shard its left half is in, so the pair travels together. First the cracks
show, as the cells along each shard's edge pale. Then the shards set off, those nearest the middle first, each thrown
out from the middle (and a little the way the slides travel) along an arc that falls, darkening as it goes.
A shard moves whole, by whole cells, so what's printed on it stays legible as it flies, and every shard lands
beyond the stage's edges.
"""

import random
from dataclasses import dataclass
from math import hypot

from counterweight.elements import StyledGrapheme
from counterweight.styles import Color

from whats_new.components.animation import between
from whats_new.components.crossing import CELL_ASPECT
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.easing import Easing
from whats_new.components.effects.characters import Point
from whats_new.components.effects.shading import BLACK
from whats_new.components.effects.shading import shaded
from whats_new.components.swipe import Direction

CELLS_PER_SHARD = 90
"""How many cells of the picture there are to a shard: about thirty on the full stage, and at least one on any."""
CRACKING = 0.15
"""How much of the transition the cracks take to show, before the first shard sets off."""
CRACK = Color.from_hex("#94a3b8")
"""The pale slate a crack tints the cells along a shard's edge toward."""
CRACK_DEPTH = 3
"""How many of `SHADES` a crack tints the cells along a shard's edge toward `CRACK`."""
STAGGER = 0.3
"""How much of the transition the shards' departures are spread over, after the cracks, nearest the middle first."""
SIDEWAYS = 0.4
"""How much a shard is thrown the way the slides travel, as well as out from the middle."""
DOWNWARD = 0.6
"""How much a shard is thrown down, as well as out from the middle, as glass falls."""
KICK = 0.15
"""
How much of a shard's flight is the steady push the crack gives it, rather than speeding up as it falls:
too much, and the shards are gone before they're seen.
"""
RECEDE = 4
"""How many of `SHADES` a shard has darkened by when it lands, as it falls away from the viewer."""


@dataclass(frozen=True, slots=True)
class Bounds:
    """The cells from `left` up to (not including) `right`, and `top` down to (not including) `bottom`."""

    left: int
    top: int
    right: int
    bottom: int

    def is_off(self, across: int, down: int, width: int, height: int) -> bool:
        """Whether these cells, moved `across` and `down`, are all off a `width` by `height` stage."""
        return (
            self.right + across <= 0
            or self.left + across >= width
            or self.bottom + down <= 0
            or self.top + down >= height
        )

    def clearing(self, toward_x: float, toward_y: float, width: int, height: int) -> float:
        """
        How far on screen these cells have to move, along the unit vector `toward_x`, `toward_y`, to be all off a
        `width` by `height` stage, past whichever edge comes first, with a cell to spare for rounding to cells.
        """
        needed = []
        if toward_x > 0:
            needed.append((width - self.left + 1) / toward_x)
        if toward_x < 0:
            needed.append((self.right + 1) / -toward_x)
        if toward_y > 0:
            needed.append((height - self.top + 1) * CELL_ASPECT / toward_y)
        if toward_y < 0:
            needed.append((self.bottom + 1) * CELL_ASPECT / -toward_y)
        return min(needed)


@dataclass(frozen=True, slots=True)
class Shard:
    """
    One piece of the leaving picture: its cells, each `x`, `y`, what it shows and whether it's along the shard's
    edge, where a crack shows. It sets off `delay` of the way through the transition and lands, whole, `throw` away
    (on screen, in cell widths), just past the stage's edges. `bounds` bound its cells, so a frame can skip a shard
    that's off the stage without looking at each cell.
    """

    cells: tuple[tuple[int, int, StyledGrapheme | None, bool], ...]
    delay: float
    throw: Point
    bounds: Bounds

    def flown(self, progress: float) -> float:
        """How far through its flight the shard is, `progress` of the way through the transition: 0 until it sets off."""
        return between(progress, self.delay, 1.0)

    def offset(self, flown: float) -> tuple[int, int]:
        """
        How many whole cells across and down the shard has moved, `flown` of the way through its flight:
        pushed off gently, then ever faster, as something falling.
        """
        moved = KICK * flown + (1 - KICK) * flown**2
        return round(self.throw[0] * moved), round(self.throw[1] * moved / CELL_ASPECT)


def nearest(x: int, y: int, seeds: tuple[Point, ...]) -> int:
    """Which of `seeds` (on screen) is nearest the middle of cell `x`, `y`: which shard the cell is in."""
    middle_x, middle_y = x + 0.5, (y + 0.5) * CELL_ASPECT
    return min(range(len(seeds)), key=lambda index: hypot(seeds[index][0] - middle_x, seeds[index][1] - middle_y))


def shards(leaving: Grid, direction: Direction) -> tuple[Shard, ...]:
    """
    The leaving picture broken into shards, in the order to draw them: those setting off last first,
    so a shard in flight passes over those still in place.
    """
    width, height = dimensions(leaving)
    chance = random.Random(315)
    count = max(1, round(width * height / CELLS_PER_SHARD))
    seeds = tuple((chance.uniform(0, width), chance.uniform(0, height * CELL_ASPECT)) for _ in range(count))
    owners: list[list[int]] = []
    for y, row in enumerate(leaving):
        owned: list[int] = []
        for x, glyph in enumerate(row):
            is_right_half = glyph is None and x > 0
            owned.append(owned[x - 1] if is_right_half else nearest(x, y, seeds))
        owners.append(owned)

    def is_edge(x: int, y: int) -> bool:
        """Whether a neighbouring cell is in another shard, so a crack runs through cell `x`, `y`."""
        neighbours = ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
        return any(
            0 <= across < width and 0 <= down < height and owners[down][across] != owners[y][x]
            for across, down in neighbours
        )

    members: dict[int, list[tuple[int, int, StyledGrapheme | None, bool]]] = {}
    for y, row in enumerate(leaving):
        for x, glyph in enumerate(row):
            members.setdefault(owners[y][x], []).append((x, y, glyph, is_edge(x, y)))

    center_x, center_y = width / 2, height * CELL_ASPECT / 2
    farthest = hypot(center_x, center_y) or 1.0
    found: list[Shard] = []
    for index, cells in members.items():
        seed_x, seed_y = seeds[index]
        out_x, out_y = seed_x - center_x, seed_y - center_y
        out = hypot(out_x, out_y) or 1.0
        toward_x = out_x / out - SIDEWAYS * direction.value
        toward_y = out_y / out + DOWNWARD
        toward = hypot(toward_x, toward_y) or 1.0
        bounds = Bounds(
            left=min(x for x, _, _, _ in cells),
            top=min(y for _, y, _, _ in cells),
            right=max(x for x, _, _, _ in cells) + 1,
            bottom=max(y for _, y, _, _ in cells) + 1,
        )
        reach = bounds.clearing(toward_x / toward, toward_y / toward, width, height) * chance.uniform(1.0, 1.3)
        found.append(
            Shard(
                cells=tuple(cells),
                delay=CRACKING + STAGGER * (out / farthest) * chance.uniform(0.7, 1.0),
                throw=(toward_x / toward * reach, toward_y / toward * reach),
                bounds=bounds,
            )
        )
    return tuple(sorted(found, key=lambda shard: -shard.delay))


def shatter(leaving: Grid, arriving: Grid, direction: Direction, easing: Easing) -> Frames:
    """
    The shatter's frames: the arriving picture, with every shard drawn over it where its flight has taken it.
    At the start every shard is in place and uncracked, so the first frame is the leaving picture, and by the end
    every shard has landed beyond the stage, so the last is the arriving one. The eased progress drives the flights;
    a curve that overshoots throws each shard a little further, and back.
    """
    width, height = dimensions(leaving)
    pieces = shards(leaving, direction)

    def frame(t: float) -> Grid:
        progress = easing(t)
        crack = round(between(progress, 0.0, CRACKING) * CRACK_DEPTH)
        rows = [list(row) for row in arriving]
        for shard in pieces:
            flown = shard.flown(progress)
            across, down = shard.offset(flown)
            if shard.bounds.is_off(across, down, width, height):
                continue
            darkness = round(flown * RECEDE)
            for x, y, glyph, is_cracked in shard.cells:
                moved_x, moved_y = x + across, y + down
                if 0 <= moved_x < width and 0 <= moved_y < height:
                    cracked = shaded(glyph, CRACK, crack) if is_cracked else glyph
                    rows[moved_y][moved_x] = shaded(cracked, BLACK, darkness)
        return tuple(tuple(row) for row in rows)

    return frame
