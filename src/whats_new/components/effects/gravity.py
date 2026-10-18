"""
Gravity: the slide being left crumbles from the bottom up, each character dropping off the bottom edge
faster and faster, and the arriving slide's characters fall in from above the top and land in their places,
the lowest rows first, so the slide stacks up from the floor the way a game of Tetris settles.

Every character falls under the same pull, so one with farther to go falls for longer and lands harder.
An arriving character's fall follows the easing curve F7 picked, applied to the fall's own constant acceleration,
so a curve that bounces bounces it off where it lands, and one that overshoots sinks it past its row and back.
A shaded cell, such as the inside of a code box, falls too, carrying its color, so a box crumbles and stacks up
again with its text; only the backdrop stays put.
"""

import random
from dataclasses import dataclass

from counterweight.elements import StyledGrapheme
from counterweight.styles.styles import UNSET
from counterweight.styles.styles import AnyColor

from whats_new.components.animation import between
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.easing import Easing
from whats_new.components.effects.characters import backdrop_of
from whats_new.components.effects.characters import characters
from whats_new.components.effects.characters import drawn_over
from whats_new.components.effects.characters import emptied
from whats_new.components.swipe import Direction

CRUMBLE = 0.2
"""How much of the transition the leaving rows let go over, the lowest first and the highest last."""
FALL = 0.3
"""How much of the transition a character takes to fall the whole height of the stage, from rest."""
FIRST_LANDING = 0.62
"""How far through the transition the arriving slide's lowest row lands; its highest lands at the very end."""
JITTER = 0.06
"""How much each leaving character's release is nudged at random, so a row crumbles rather than dropping as one bar."""
LANDING_JITTER = 0.02
"""How much each arriving character's landing is nudged at random: less than `JITTER`, so a row lands as a line."""


@dataclass(frozen=True, slots=True)
class Drop:
    """
    A leaving character at `x`, `y`, let go `release` of the way through the transition,
    falling from rest with `pull`, in rows per transition squared, until it's below the stage.
    """

    x: int
    y: int
    glyph: StyledGrapheme
    release: float
    pull: float

    def at(self, t: float) -> tuple[int, int, StyledGrapheme]:
        """Where the character has fallen to `t` of the way through the transition, its column unchanged."""
        fallen = max(t - self.release, 0.0)
        return self.x, round(self.y + self.pull * fallen**2), self.glyph


@dataclass(frozen=True, slots=True)
class Landing:
    """
    An arriving character falling from the row above the stage into its place at `x`, `y`,
    over the part of the transition from `start` to `land`, which ends no later than the transition does.
    """

    x: int
    y: int
    glyph: StyledGrapheme
    start: float
    land: float

    def at(self, t: float, easing: Easing) -> tuple[int, int, StyledGrapheme]:
        """
        Where the character has fallen to `t` of the way through the transition: the eased fall is the time
        squared, so under a linear curve it accelerates just as a leaving character does.
        """
        fallen = easing(between(t, self.start, self.land) ** 2)
        return self.x, round(-1 + (self.y + 1) * fallen), self.glyph


def cells(grid: Grid, backdrop: AnyColor | UNSET) -> list[tuple[int, int, StyledGrapheme]]:
    """Each cell of `grid` that falls, with the column and row it's in, as whole numbers."""
    return [(int(x), int(y), glyph) for found in characters(grid, backdrop).values() for (x, y), glyph in found]


def heights(rows: set[int]) -> dict[int, float]:
    """
    How high each of `rows` is among them, from 0 for the lowest to 1 for the highest,
    so a slide's rows take turns over the same span however much of the stage they fill.
    """
    highest = max(len(rows) - 1, 1)
    return {y: rank / highest for rank, y in enumerate(sorted(rows, reverse=True))}


def drops(leaving: Grid, height: int, chance: random.Random, backdrop: AnyColor | UNSET) -> tuple[Drop, ...]:
    """Every leaving cell's fall: the lower its row, the sooner it lets go."""
    pull = height / FALL**2
    found = cells(leaving, backdrop)
    order = heights({y for _, y, _ in found})
    return tuple(
        Drop(x=x, y=y, glyph=glyph, release=(CRUMBLE - JITTER) * order[y] + chance.random() * JITTER, pull=pull)
        for x, y, glyph in found
    )


def landings(arriving: Grid, height: int, chance: random.Random, backdrop: AnyColor | UNSET) -> tuple[Landing, ...]:
    """
    Every arriving character's fall, the lowest rows landing first, each falling for as long as gravity takes
    to bring it from above the stage down to its row, so the lowest characters fall farthest and fastest.
    """
    # Drawn from the top row down, so a character a springy curve carries past its row passes behind the row
    # below, which has already landed.
    found = sorted(cells(arriving, backdrop), key=lambda cell: cell[1])
    order = heights({y for _, y, _ in found})
    placed: list[Landing] = []
    for x, y, glyph in found:
        land = FIRST_LANDING + (1 - FIRST_LANDING - LANDING_JITTER) * order[y] + chance.random() * LANDING_JITTER
        falling = FALL * ((y + 1) / height) ** 0.5
        placed.append(Landing(x=x, y=y, glyph=glyph, start=land - falling, land=land))
    return tuple(placed)


def gravity(leaving: Grid, arriving: Grid, direction: Direction, easing: Easing) -> Frames:
    """
    Gravity's frames. Each draws the backdrop, then the leaving cells wherever they've fallen to, then the arriving
    ones over them, so a cell that has landed looks exactly as its slide draws it.
    """
    height = dimensions(leaving)[1]
    chance = random.Random(315)
    backdrop = backdrop_of(leaving, arriving)
    falling, settling = drops(leaving, height, chance, backdrop), landings(arriving, height, chance, backdrop)
    under, over = emptied(leaving, backdrop), emptied(arriving, backdrop)

    def frame(t: float) -> Grid:
        # The two backdrops look the same, so they change over only at the end, where the last frame has to be exact.
        behind = over if t >= 1 else under
        return drawn_over(
            behind, (*(drop.at(t) for drop in falling), *(landing.at(t, easing) for landing in settling)), backdrop
        )

    return frame
