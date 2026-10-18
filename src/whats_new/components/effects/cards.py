"""
What the grid effects that move pictures about whole share, as cards: cutting one out of a picture, scaling it to
a size, laying it on a sheet, and a card's flight from one place and size to another, changing face on the way.

Scaling takes each cell from the nearest one of the picture, so a card at its own size is its picture exactly,
which is what lets an effect start on one picture and end on the other without a jump.
"""

from dataclasses import dataclass
from math import floor

from counterweight.elements import StyledGrapheme
from counterweight.geometry import Region
from counterweight.styles import CellStyle
from counterweight.styles.styles import UNSET
from counterweight.styles.styles import AnyColor

from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions

type Sheet = list[list[StyledGrapheme | None]]
"""A frame being drawn, which cards are laid on one after another, so a later one covers an earlier one."""


def blank(backdrop: AnyColor | UNSET) -> StyledGrapheme:
    """An empty cell on `backdrop`, what's left where a card has been lifted off."""
    return StyledGrapheme(grapheme=" ", style=CellStyle(background=backdrop))


def sheet_of(picture: Grid) -> Sheet:
    return [list(row) for row in picture]


def finished(sheet: Sheet) -> Grid:
    return tuple(tuple(row) for row in sheet)


def cut(picture: Grid, region: Region) -> Grid:
    """The part of `picture` inside `region`."""
    return tuple(row[region.left : region.right] for row in picture[region.top : region.bottom])


def vacated(picture: Grid, regions: tuple[Region, ...], backdrop: AnyColor | UNSET) -> Sheet:
    """`picture` with each of `regions` blanked on `backdrop`: where cards that land there are laid."""
    sheet = sheet_of(picture)
    for region in regions:
        for y in range(region.top, region.bottom):
            for x in range(region.left, region.right):
                sheet[y][x] = blank(backdrop)
    return sheet


def scaled(picture: Grid, width: int, height: int) -> Grid:
    """`picture` drawn `width` by `height`, each cell the nearest of the picture's: at its own size, itself."""
    source_width, source_height = dimensions(picture)
    if width <= 0 or height <= 0 or source_width == 0:
        return ()
    rows = tuple(picture[floor((y + 0.5) * source_height / height)] for y in range(height))
    columns = tuple(floor((x + 0.5) * source_width / width) for x in range(width))
    return tuple(tuple(row[x] for x in columns) for row in rows)


def laid(sheet: Sheet, picture: Grid, left: int, top: int) -> None:
    """Lays `picture` on `sheet` with its corner at `left` and `top`, whatever of it is on the sheet."""
    height = len(sheet)
    width = len(sheet[0]) if sheet else 0
    for y, row in enumerate(picture, start=top):
        if not 0 <= y < height:
            continue
        for x, glyph in enumerate(row, start=left):
            if 0 <= x < width:
                sheet[y][x] = glyph


def moved(start: Region, end: Region, eased: float) -> Region:
    """The region `eased` of the way from `start` to `end`, each edge rounded to a cell."""

    def edge(a: int, b: int) -> int:
        return round(a + (b - a) * eased)

    return Region(
        left=edge(start.left, end.left),
        top=edge(start.top, end.top),
        right=edge(start.right, end.right),
        bottom=edge(start.bottom, end.bottom),
    )


def shifted(region: Region, x: int, y: int) -> Region:
    return Region(left=region.left + x, top=region.top + y, right=region.right + x, bottom=region.bottom + y)


TURNS = 0.95
"""
How far along its flight a card turns from its front to its back. Late, since a back drawn larger than its own size
repeats its rows and columns, which garbles text far more than dropping them does while the front shrinks.
"""


@dataclass(frozen=True, slots=True)
class Card:
    """
    A picture flying from `start` to `end`, scaled to fit wherever it is: showing `front` for nearly all its
    flight and `back` as it lands, so a slide shrinking into its thumbnail lands as the thumbnail itself.
    """

    front: Grid
    back: Grid
    start: Region
    end: Region

    def laid(self, sheet: Sheet, eased: float) -> None:
        """Lays the card on `sheet` where it is `eased` of the way along its flight."""
        where = moved(self.start, self.end, eased)
        face = self.front if eased < TURNS else self.back
        laid(sheet, scaled(face, where.width, where.height), where.left, where.top)
