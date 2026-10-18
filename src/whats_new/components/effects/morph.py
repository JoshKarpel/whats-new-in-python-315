"""
The morph: every character of the slide being left flies to where the same character sits on the arriving slide.
Characters the arriving slide has more of fly in from beyond the edges, and those it has fewer of fly out past them,
each straight out from (or in toward) the middle, so the leftovers burst outward and the newcomers gather in.

A shaded cell, such as the inside of a code box, flies too, carrying its color, so a box breaks up and reforms with
its text; only the backdrop stays put. A character on the backdrop takes the background of whatever it's crossing. Each character sets off at its own moment in the first part of the transition,
so they don't all move as one, and eases in and out over its own flight.
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
from whats_new.components.easing import ease_in_out
from whats_new.components.effects.characters import Point
from whats_new.components.effects.characters import backdrop_of
from whats_new.components.effects.characters import beyond
from whats_new.components.effects.characters import characters
from whats_new.components.effects.characters import drawn_over
from whats_new.components.effects.characters import emptied
from whats_new.components.swipe import Direction

STAGGER = 0.3
"""How much of the transition the characters' departures are spread over; each flies for the rest of it."""


@dataclass(frozen=True, slots=True)
class Flight:
    """
    One character's path, from `start` to `end`, setting off `delay` of the way through the transition.
    It shows as `leaving` for the first half of its flight and `arriving` for the second;
    a character only one slide has is the same at both.
    """

    start: Point
    end: Point
    leaving: StyledGrapheme
    arriving: StyledGrapheme
    delay: float

    def at(self, t: float) -> tuple[int, int, StyledGrapheme]:
        """Which cell the character is in, and what it shows, `t` of the way through the transition."""
        flown = between(t, self.delay, self.delay + 1 - STAGGER)
        eased = ease_in_out(flown)
        x = self.start[0] + (self.end[0] - self.start[0]) * eased
        y = self.start[1] + (self.end[1] - self.start[1]) * eased
        return round(x), round(y), self.leaving if flown < 0.5 else self.arriving


def flights(leaving: Grid, arriving: Grid, direction: Direction, backdrop: AnyColor | UNSET) -> tuple[Flight, ...]:
    """
    Every character's path: the nth of a grapheme on the leaving slide to the nth on the arriving one,
    reading order on each, and the rest off or on from beyond the edges. Those leaving come first, so they're drawn
    under those arriving.
    """
    width, height = dimensions(leaving)
    chance = random.Random(315)
    before, after = characters(leaving, backdrop), characters(arriving, backdrop)
    departing: list[Flight] = []
    moving: list[Flight] = []
    landing: list[Flight] = []
    for grapheme in sorted(before.keys() | after.keys()):
        froms, tos = before.get(grapheme, []), after.get(grapheme, [])
        for (start, old), (end, new) in zip(froms, tos, strict=False):
            moving.append(Flight(start=start, end=end, leaving=old, arriving=new, delay=chance.random() * STAGGER))
        for start, old in froms[len(tos) :]:
            away = beyond(start, width, height, direction)
            departing.append(Flight(start=start, end=away, leaving=old, arriving=old, delay=chance.random() * STAGGER))
        for end, new in tos[len(froms) :]:
            away = beyond(end, width, height, direction)
            landing.append(Flight(start=away, end=end, leaving=new, arriving=new, delay=chance.random() * STAGGER))
    return (*departing, *moving, *landing)


def morph(leaving: Grid, arriving: Grid, direction: Direction) -> Frames:
    """
    The morph's frames. Each draws the backdrop, then everything that moves where its flight has reached,
    so a cell that has landed looks exactly as its slide draws it.
    """
    backdrop = backdrop_of(leaving, arriving)
    paths = flights(leaving, arriving, direction, backdrop)
    under, over = emptied(leaving, backdrop), emptied(arriving, backdrop)

    def frame(t: float) -> Grid:
        # The two backdrops look the same, so they change over only at the end, where the last frame has to be exact.
        behind = over if t >= 1 else under
        return drawn_over(behind, (path.at(t) for path in paths), backdrop)

    return frame
