"""
Exposé, as macOS lays out every window: the slide shrinks into its thumbnail while the others slide in from
whichever edge of the stage is nearest them, and the line naming the section drops in from the top.
Everything moves together, easing in and out.
"""

from counterweight.geometry import Region

from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import Tiles
from whats_new.components.crossing import dimensions
from whats_new.components.easing import ease_in_out
from whats_new.components.effects.cards import Card
from whats_new.components.effects.cards import cut
from whats_new.components.effects.cards import finished
from whats_new.components.effects.cards import shifted
from whats_new.components.effects.cards import vacated
from whats_new.components.effects.characters import backdrop_of


def offstage(region: Region, width: int, height: int) -> Region:
    """`region` moved straight out past whichever edge of a `width` by `height` stage it's nearest, just out of view."""
    nearest = min(
        (region.left, shifted(region, -region.right, 0)),
        (width - region.right, shifted(region, width - region.left, 0)),
        (region.top, shifted(region, 0, -region.bottom)),
        (height - region.bottom, shifted(region, 0, height - region.top)),
        key=lambda distance_and_place: distance_and_place[0],
    )
    return nearest[1]


def expose(slide: Grid, grid: Grid, tiles: Tiles) -> Frames:
    """
    Exposé's frames. The other thumbnails start out of view and the slide covers the stage, so the first frame is
    the slide; everything ends in its place on the grid, so the last is the grid.
    """
    width, height = dimensions(slide)
    backdrop = backdrop_of(slide, grid)
    sliding = tuple(
        Card(front=cut(grid, region), back=cut(grid, region), start=offstage(region, width, height), end=region)
        for region in (
            tiles.header,
            *(region for index, region in enumerate(tiles.thumbnails) if index != tiles.selected),
        )
    )
    shrinking = Card(
        front=slide,
        back=cut(grid, tiles.chosen),
        start=Region(left=0, top=0, right=width, bottom=height),
        end=tiles.chosen,
    )
    empty = vacated(grid, (tiles.header, *tiles.thumbnails), backdrop)

    def frame(t: float) -> Grid:
        eased = ease_in_out(t)
        sheet = [list(row) for row in empty]
        for card in sliding:
            card.laid(sheet, eased)
        # Last, so the others slide in under it.
        shrinking.laid(sheet, eased)
        return finished(sheet)

    return frame
