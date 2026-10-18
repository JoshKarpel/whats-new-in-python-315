"""
The unpack, as `*section` unpacks a sequence: the slide shrinks into its thumbnail, then the rest of its section
bursts out from under it, every thumbnail at once, each flying from the slide's place to its own.
The line naming the section is written out across the top as they go. The slide eases in and out, as something
moving whole does; the burst is thrown, so it eases out, and the writing goes at a steady pace.
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
from whats_new.components.effects.cards import laid
from whats_new.components.effects.cards import vacated
from whats_new.components.effects.characters import backdrop_of

PACKED = 0.4
"""How much of the unpack the slide takes to shrink into its thumbnail, with the others packed under it."""


def unpack(slide: Grid, grid: Grid, tiles: Tiles) -> Frames:
    """
    The unpack's frames. The others start packed under the slide, which covers the stage, so the first frame is
    the slide; every one lands at the end, so the last frame is the grid.
    """
    width, height = dimensions(slide)
    backdrop = backdrop_of(slide, grid)
    unpacked = tuple(
        Card(front=cut(grid, region), back=cut(grid, region), start=tiles.chosen, end=region)
        for index, region in enumerate(tiles.thumbnails)
        if index != tiles.selected
    )
    shrinking = Card(
        front=slide,
        back=cut(grid, tiles.chosen),
        start=Region(left=0, top=0, right=width, bottom=height),
        end=tiles.chosen,
    )
    header = cut(grid, tiles.header)
    empty = vacated(grid, (tiles.header, *tiles.thumbnails), backdrop)

    def frame(t: float) -> Grid:
        sheet = [list(row) for row in empty]
        burst = between(t, PACKED, 1)
        written = round(burst * tiles.header.width)
        laid(sheet, tuple(row[:written] for row in header), tiles.header.left, tiles.header.top)
        for card in unpacked:
            card.laid(sheet, ease_out(burst))
        # Last, so the others burst out from under it.
        shrinking.laid(sheet, ease_in_out(between(t, 0, PACKED)))
        return finished(sheet)

    return frame
