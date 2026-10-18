"""
The scale: the slide shrinks into its thumbnail over the grid, scaled whole rather than reflowed, as the zoom does,
dropping rows and columns as it goes, and lands as the thumbnail itself. It eases in and out, as something moving
whole does.
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
from whats_new.components.effects.cards import sheet_of


def scale(slide: Grid, grid: Grid, tiles: Tiles) -> Frames:
    """The scale's frames: the slide, full size over the grid at first, and its thumbnail in place at last."""
    width, height = dimensions(slide)
    card = Card(
        front=slide,
        back=cut(grid, tiles.chosen),
        start=Region(left=0, top=0, right=width, bottom=height),
        end=tiles.chosen,
    )

    def frame(t: float) -> Grid:
        sheet = sheet_of(grid)
        card.laid(sheet, ease_in_out(t))
        return finished(sheet)

    return frame
