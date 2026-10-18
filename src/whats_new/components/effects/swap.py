"""
The swap: characters the two slides share trade places in short hops, each to the nearest spot the same character
has on the arriving slide, while everything else decays: a character only the leaving slide has crumbles away
through shade blocks, and one only the arriving slide has condenses out of them, so the slide seems to rearrange
itself rather than be replaced.

A character is matched only to one close by, nearest pairs first, so nothing flies across the stage as in the
morph, and one already in its place on both slides stays put. A hop arcs up over the row, higher the farther
it goes, as something thrown does: steadily across, and up and down again. A shaded cell, such as the inside
of a code box, hops or decays too, carrying its color, so a box rearranges itself with its text; only the backdrop
stays put.
"""

import random
from dataclasses import dataclass
from math import hypot
from math import pi
from math import sin

from counterweight.elements import StyledGrapheme
from counterweight.styles.styles import UNSET
from counterweight.styles.styles import AnyColor

from whats_new.components.animation import between
from whats_new.components.crossing import CELL_ASPECT
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.effects.characters import Point
from whats_new.components.effects.characters import backdrop_of
from whats_new.components.effects.characters import characters
from whats_new.components.effects.characters import drawn_over
from whats_new.components.effects.characters import emptied
from whats_new.components.swipe import Direction

REACH = 20.0
"""How far, in columns as it looks on screen, a character hops at most; one with no partner that close decays."""
LIFT = 8.0
"""How many columns of hop lift a character one row at the top of its arc."""
HIGHEST = 2.0
"""How many rows a hop lifts a character at most."""
HOP = 0.4
"""How much of the transition each hop takes."""
FADE = 0.2
"""How much of the transition a character takes to decay through every shade, or to condense back."""
STAGGER = 0.24
"""How much of the transition each kind of change's start is spread over."""
FADING, HOPPING, CONDENSING = 0.0, 0.2, 0.55
"""When the first leaving character starts to decay, the first shared one to hop, and the first new one to condense."""
SHADES = ("▓", "▒", "░")
"""What a character shows as it decays, densest first; one condensing goes through them the other way."""


@dataclass(frozen=True, slots=True)
class Hop:
    """
    A character both slides have, hopping from `start` to `end` over the part of the transition from `begin` on,
    arcing up `lift` rows at the middle. It shows as `leaving` for the first half of the hop and `arriving` after.
    """

    start: Point
    end: Point
    leaving: StyledGrapheme
    arriving: StyledGrapheme
    begin: float
    lift: float

    def at(self, t: float) -> tuple[int, int, StyledGrapheme]:
        """Which cell the character is in, and what it shows, `t` of the way through the transition."""
        hopped = between(t, self.begin, self.begin + HOP)
        x = self.start[0] + (self.end[0] - self.start[0]) * hopped
        y = self.start[1] + (self.end[1] - self.start[1]) * hopped - self.lift * sin(pi * hopped)
        return round(x), round(y), self.leaving if hopped < 0.5 else self.arriving


@dataclass(frozen=True, slots=True)
class Decay:
    """
    A character only one slide has, at `x`, `y`, changing through the shades over the part of the transition
    from `begin` on: crumbling away if `is_leaving`, or condensing into place if not.
    """

    x: int
    y: int
    glyph: StyledGrapheme
    shades: tuple[StyledGrapheme, ...]
    begin: float
    is_leaving: bool

    def at(self, t: float) -> tuple[int, int, StyledGrapheme] | None:
        """What the cell shows `t` of the way through the transition, or `None` while the character is gone."""
        faded = between(t, self.begin, self.begin + FADE)
        stage = int(faded * (len(self.shades) + 1))
        if not self.is_leaving:
            stage = len(self.shades) + 1 - stage
        if stage == 0:
            return self.x, self.y, self.glyph
        if stage > len(self.shades):
            return None
        return self.x, self.y, self.shades[stage - 1]


def nearest_pairs(froms: list[Point], tos: list[Point]) -> list[tuple[int, int]]:
    """
    Which of `froms` goes to which of `tos`, by index: the closest pair first, then the closest of the rest,
    and so on, as long as a pair is within `REACH` on screen.
    """
    # Those already in the same place pair first, as they would by distance, by looking each one up: a box's shading
    # is mostly in the same place on both slides, and comparing every pair of its cells is slow.
    in_place = {point: end for end, point in enumerate(tos)}
    pairs = [(start, in_place[point]) for start, point in enumerate(froms) if point in in_place]
    taken_from = {start for start, _ in pairs}
    taken_to = {end for _, end in pairs}
    candidates = sorted(
        (distance, start, end)
        for start, (from_x, from_y) in enumerate(froms)
        if start not in taken_from
        for end, (to_x, to_y) in enumerate(tos)
        if end not in taken_to and (distance := hypot(to_x - from_x, (to_y - from_y) * CELL_ASPECT)) <= REACH
    )
    for _, start, end in candidates:
        if start in taken_from or end in taken_to:
            continue
        taken_from.add(start)
        taken_to.add(end)
        pairs.append((start, end))
    return pairs


def shaded(glyph: StyledGrapheme) -> tuple[StyledGrapheme, ...]:
    """Each shade `glyph` decays through, in its colors."""
    return tuple(StyledGrapheme(grapheme=shade, style=glyph.style) for shade in SHADES)


def rearranging(
    leaving: Grid, arriving: Grid, backdrop: AnyColor | UNSET
) -> tuple[tuple[Decay, ...], tuple[Hop, ...], tuple[Decay, ...]]:
    """
    What happens to every cell that moves: those only the leaving slide has decaying, those both have hopping,
    and those only the arriving slide has condensing, each starting at its own moment.
    """
    chance = random.Random(315)
    before, after = characters(leaving, backdrop), characters(arriving, backdrop)
    fading: list[Decay] = []
    hops: list[Hop] = []
    condensing: list[Decay] = []
    for grapheme in sorted(before.keys() | after.keys()):
        froms, tos = before.get(grapheme, []), after.get(grapheme, [])
        pairs = nearest_pairs([start for start, _ in froms], [end for end, _ in tos])
        for start_index, end_index in pairs:
            (start, old), (end, new) = froms[start_index], tos[end_index]
            distance = hypot(end[0] - start[0], (end[1] - start[1]) * CELL_ASPECT)
            hops.append(
                Hop(
                    start=start,
                    end=end,
                    leaving=old,
                    arriving=new,
                    begin=HOPPING + chance.random() * STAGGER,
                    lift=min(distance / LIFT, HIGHEST),
                )
            )
        hopped_from = {start for start, _ in pairs}
        hopped_to = {end for _, end in pairs}
        for index, ((x, y), old) in enumerate(froms):
            if index in hopped_from:
                continue
            begin = FADING + chance.random() * STAGGER
            fading.append(Decay(x=int(x), y=int(y), glyph=old, shades=shaded(old), begin=begin, is_leaving=True))
        for index, ((x, y), new) in enumerate(tos):
            if index in hopped_to:
                continue
            begin = CONDENSING + chance.random() * STAGGER
            condensing.append(Decay(x=int(x), y=int(y), glyph=new, shades=shaded(new), begin=begin, is_leaving=False))
    return tuple(fading), tuple(hops), tuple(condensing)


def swap(leaving: Grid, arriving: Grid, direction: Direction) -> Frames:
    """
    The swap's frames. Each draws the backdrop, then the decaying cells, the condensing ones, and the hopping ones
    over all of those, so a cell in its place looks exactly as its slide draws it.
    """
    backdrop = backdrop_of(leaving, arriving)
    fading, hops, condensing = rearranging(leaving, arriving, backdrop)
    under, over = emptied(leaving, backdrop), emptied(arriving, backdrop)

    def frame(t: float) -> Grid:
        # The two backdrops look the same, so they change over only at the end, where the last frame has to be exact.
        behind = over if t >= 1 else under
        decays = (place for decay in (*fading, *condensing) if (place := decay.at(t)) is not None)
        return drawn_over(behind, (*decays, *(hop.at(t) for hop in hops)), backdrop)

    return frame
