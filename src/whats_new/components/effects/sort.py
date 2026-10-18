"""
The sort: each row of the slide being left sorts itself, its characters sliding along the row one after another,
smallest first, until the row reads in order, packed against the side the arriving slide comes from
(the right, moving to the next slide), just as `sorted` would leave a row whose spaces sort before everything.
Halfway through, every row holds the arriving slide's characters, sorted, which then unsort the same way
played backward, largest first, out to their places.

Each character slides over its own short part of the transition, following the easing curve F7 picked,
so a curve that bounces knocks each one into place like a bar in a sorting-algorithm visualizer.
A shaded cell, such as the inside of a code box, slides too, carrying its color: it holds a space, which sorts
first, so a box's shading gathers at the smallest end of its row and spreads back out with its text.
"""

from dataclasses import dataclass

from counterweight.elements import StyledGrapheme
from counterweight.styles.styles import UNSET
from counterweight.styles.styles import AnyColor

from whats_new.components.animation import between
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.easing import Easing
from whats_new.components.effects.characters import backdrop_of
from whats_new.components.effects.characters import drawn_over
from whats_new.components.effects.characters import emptied
from whats_new.components.effects.characters import moves
from whats_new.components.swipe import Direction

HALF = 0.5
"""How far through the transition the leaving rows are all sorted, and the arriving rows take their place."""
SLIDE = 0.15
"""How much of the transition each character takes to slide from one place in its row to the other."""


@dataclass(frozen=True, slots=True)
class Slide:
    """
    A character sliding along row `y` from column `start` to column `end`,
    over the part of the transition from `begin` to `begin` plus `SLIDE`.
    """

    start: int
    end: int
    y: int
    glyph: StyledGrapheme
    begin: float

    def at(self, t: float, easing: Easing) -> tuple[int, int, StyledGrapheme]:
        """Which cell the character is in `t` of the way through the transition."""
        slid = easing(between(t, self.begin, self.begin + SLIDE))
        return round(self.start + (self.end - self.start) * slid), self.y, self.glyph


def sorted_row(
    row: tuple[StyledGrapheme | None, ...], direction: Direction, backdrop: AnyColor | UNSET
) -> tuple[tuple[int, int, StyledGrapheme], ...]:
    """
    Each cell of `row` that moves, as its column, the column it sorts to, and itself, smallest first.
    Sorted by grapheme, equal ones keeping their order, and packed against the right edge, smallest leftmost,
    moving to the next slide, or mirrored, packed against the left edge, smallest rightmost, moving back.
    """
    found = sorted(
        ((x, glyph) for x, glyph in enumerate(row) if glyph is not None and moves(glyph, backdrop)),
        key=lambda placed: placed[1].grapheme,
    )
    taken = sum(glyph.width for _, glyph in found)
    width = len(row)
    placed: list[tuple[int, int, StyledGrapheme]] = []
    filled = 0
    for x, glyph in found:
        if direction is Direction.NEXT:
            placed.append((x, width - taken + filled, glyph))
        else:
            placed.append((x, taken - filled - glyph.width, glyph))
        filled += glyph.width
    return tuple(placed)


def sorting(grid: Grid, direction: Direction, backdrop: AnyColor | UNSET) -> tuple[Slide, ...]:
    """
    Every leaving character's slide into sorted order, the smallest of each row first, so each row's sorted run
    grows from one end while the rest of the row waits. Those that set off last are drawn first, under the rest.
    """
    slides: list[Slide] = []
    for y, row in enumerate(grid):
        ranked = sorted_row(row, direction, backdrop)
        last = max(len(ranked) - 1, 1)
        slides.extend(
            Slide(start=x, end=to, y=y, glyph=glyph, begin=(HALF - SLIDE) * rank / last)
            for rank, (x, to, glyph) in enumerate(ranked)
        )
    return tuple(sorted(slides, key=lambda slide: -slide.begin))


def unsorting(grid: Grid, direction: Direction, backdrop: AnyColor | UNSET) -> tuple[Slide, ...]:
    """
    Every arriving character's slide out of sorted order to its place, the sort played backward:
    the largest of each row first, ending with the smallest just as the transition ends.
    """
    slides: list[Slide] = []
    for y, row in enumerate(grid):
        ranked = sorted_row(row, direction, backdrop)
        last = max(len(ranked) - 1, 1)
        slides.extend(
            Slide(start=to, end=x, y=y, glyph=glyph, begin=HALF + (1 - HALF - SLIDE) * (last - rank) / last)
            for rank, (x, to, glyph) in enumerate(ranked)
        )
    return tuple(sorted(slides, key=lambda slide: -slide.begin))


def sort(leaving: Grid, arriving: Grid, direction: Direction, easing: Easing) -> Frames:
    """
    The sort's frames. Each draws the backdrop, then the leaving rows sorting, or past halfway the arriving rows
    unsorting, so a cell back in its place looks exactly as its slide draws it.
    """
    backdrop = backdrop_of(leaving, arriving)
    sorts, unsorts = sorting(leaving, direction, backdrop), unsorting(arriving, direction, backdrop)
    under, over = emptied(leaving, backdrop), emptied(arriving, backdrop)

    def frame(t: float) -> Grid:
        # The two backdrops look the same, so they change over only at the end, where the last frame has to be exact.
        behind = over if t >= 1 else under
        return drawn_over(behind, (slide.at(t, easing) for slide in (sorts if t < HALF else unsorts)), backdrop)

    return frame
