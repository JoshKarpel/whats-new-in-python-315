"""
The deal: the slide shrinks into its thumbnail, then the rest of the deck is dealt onto the table around it, one card
at a time in reading order, each thrown in from the dealer's hand below the stage and caught in its place.
The line naming the section is dealt last. The slide eases in and out, as something moving whole does;
each dealt card is thrown, so it eases out.
"""

from counterweight.geometry import Region

from whats_new.components.animation import between
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import Tiles
from whats_new.components.crossing import dimensions
from whats_new.components.easing import ease_in_out
from whats_new.components.easing import ease_out
from whats_new.components.effects.cards import Card
from whats_new.components.effects.cards import cut
from whats_new.components.effects.cards import finished
from whats_new.components.effects.cards import vacated
from whats_new.components.effects.characters import backdrop_of

SHRUNK = 0.35
"""How much of the deal the slide takes to shrink into its thumbnail, before the first card is thrown."""
THROW = 0.25
"""How much of the deal each card's throw takes; the throws start evenly spread over the rest of it."""


def hand(region: Region, width: int, height: int) -> Region:
    """Where a card the size of `region` waits to be dealt: in the middle, just below a `width` by `height` stage."""
    left = (width - region.width) // 2
    return Region(left=left, top=height, right=left + region.width, bottom=height + region.height)


def deal(slide: Grid, grid: Grid, tiles: Tiles) -> Frames:
    """
    The deal's frames. The cards still to be dealt wait below the stage, under the slide covering it, so the first
    frame is the slide; the last card lands at the end, so the last frame is the grid.
    """
    width, height = dimensions(slide)
    backdrop = backdrop_of(slide, grid)
    dealt = (*(region for index, region in enumerate(tiles.thumbnails) if index != tiles.selected), tiles.header)
    cards = tuple(
        Card(front=cut(grid, region), back=cut(grid, region), start=hand(region, width, height), end=region)
        for region in dealt
    )
    spacing = (1 - SHRUNK - THROW) / max(len(cards) - 1, 1)
    shrinking = Card(
        front=slide,
        back=cut(grid, tiles.chosen),
        start=Region(left=0, top=0, right=width, bottom=height),
        end=tiles.chosen,
    )
    empty = vacated(grid, (tiles.header, *tiles.thumbnails), backdrop)

    def frame(t: float) -> Grid:
        sheet = [list(row) for row in empty]
        shrinking.laid(sheet, ease_in_out(between(t, 0, SHRUNK)))
        # In the order they're dealt, so each is thrown over those already on the table.
        for number, card in enumerate(cards):
            thrown = SHRUNK + number * spacing
            card.laid(sheet, ease_out(between(t, thrown, thrown + THROW)))
        return finished(sheet)

    return frame
