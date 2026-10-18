"""
The slide transitions drawn from pictures: the slide being left and the one arriving, each captured as a grid of
cells, and a frame of the transition computed from the two, cell by cell, for a canvas to draw over the stage.

Moving one slide's cells about needs no layout, so an effect can do anything to them that a function of the two
pictures and the progress can say: uncover the arriving slide in a pattern (`dissolve`, `wipe`, `iris`, `blinds`),
or fly each character to its place on the other (`morph`). The effects themselves live in `effects`,
one module each. The arriving slide is mounted and live beneath the canvas
the whole time, so it takes the keys at once, and shows as itself when the canvas goes.

The leaving picture is what the screen showed, from a `Screenshot`, so it's the slide as it was left, edits and run
output included. The arriving picture is a headless render of the slide's first frame, which is what the live slide
shows too, since a slide always arrives at its first step and mounting it starts nothing.

The grid's transitions (F7) are drawn the same way, between a slide and the grid: any `Effect`, or a `GridEffect`,
which knows where each thumbnail is, so it can move the slide into its own.
"""

from asyncio import create_task
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from functools import cache

from counterweight.app import app
from counterweight.clock import FrozenClock
from counterweight.components import Component
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.elements import Rows
from counterweight.elements import StyledGrapheme
from counterweight.geometry import Position
from counterweight.geometry import Region
from counterweight.output import Frame
from counterweight.paint import Cell
from counterweight.paint import Paint
from counterweight.styles import CellStyle

from whats_new.components.swipe import Direction

PHOTOGRAPHED = FrozenClock(datetime(2026, 10, 1, 12, 0, tzinfo=UTC))
"""The clock `photograph` renders on, which never moves, since it takes only the first frame."""

type Grid = tuple[tuple[StyledGrapheme | None, ...], ...]
"""
A picture, one entry per cell, row by row. `None` is the right half of the two-cell-wide grapheme to its left,
as a `Paint`'s continuation cell is, so every row is as long as the picture is wide and `x` indexes it directly.
"""

type Frames = Callable[[float], Grid]
"""One transition's frames: the picture to show `t` of the way through it, from 0 to 1."""

type Effect = Callable[[Grid, Grid, Direction], Frames]
"""
How one kind of transition turns the leaving and arriving pictures (the same size) into its frames,
given which way the presenter moved. Each effect eases its own motion, if it eases at all (see `easing`).
Whatever an effect works out from the pictures
alone, it works out once, here, rather than in every frame. Its first frame is the leaving picture and its last
the arriving one, so the transition starts and ends without a jump.
"""


@dataclass(frozen=True, slots=True)
class Tiles:
    """
    Where things are in a picture of the slide grid: the line naming the section, each thumbnail in reading order,
    and which of them is the slide the grid opens from or closes to.
    """

    header: Region
    thumbnails: tuple[Region, ...]
    selected: int

    @property
    def chosen(self) -> Region:
        """The selected slide's thumbnail."""
        return self.thumbnails[self.selected]


type GridEffect = Callable[[Grid, Grid, Tiles], Frames]
"""
How one kind of grid transition turns a picture of a slide and one of the grid (the same size) into the frames of
the grid opening from that slide, given where the `Tiles` are in the grid's picture. Closing plays the same frames
backwards, so its first frame is the slide's picture and its last the grid's, as an `Effect`'s are.
"""

SPACE = StyledGrapheme(grapheme=" ")


@cache
def glyph_of(cell: Cell) -> StyledGrapheme | None:
    """`cell` as a canvas draws it: its grapheme with its style, or `None` for a continuation cell."""
    if cell.is_continuation:
        return None
    style = cell.style
    return StyledGrapheme(
        grapheme=cell.grapheme,
        style=CellStyle(
            foreground=style.foreground,
            background=style.background,
            bold=style.bold,
            dim=style.dim,
            italic=style.italic,
            underline=style.underline,
            strikethrough=style.strikethrough,
            link=style.link,
        ),
    )


def picture_of(paint: Paint, region: Region) -> Grid:
    """The part of `paint` inside `region`. Any of it off the paint, as after the screen shrinks, is blank."""
    return tuple(
        tuple(
            SPACE if (cell := paint.get(Position(x, y))) is None else glyph_of(cell)
            for x in range(region.left, region.right)
        )
        for y in range(region.top, region.bottom)
    )


def rows_of(grid: Grid) -> Rows:
    """
    `grid` as a canvas's rows. Wherever cells taken from different pictures split a two-cell-wide grapheme,
    the half left over becomes a space, as a terminal leaves it.
    """
    return tuple(row_of(row) for row in grid)


def row_of(row: tuple[StyledGrapheme | None, ...]) -> tuple[StyledGrapheme, ...]:
    drawn: list[StyledGrapheme] = []
    for x, glyph in enumerate(row):
        if glyph is None:
            if not (x > 0 and (left := row[x - 1]) is not None and left.width == 2):
                drawn.append(SPACE)
            continue
        if glyph.width == 2 and not (x + 1 < len(row) and row[x + 1] is None):
            drawn.append(StyledGrapheme(grapheme=" ", style=glyph.style))
            continue
        drawn.append(glyph)
    return tuple(drawn)


CELL_ASPECT = 2.0
"""How many times taller a cell is than wide, near enough, so a circle of cells is twice as wide as it is tall."""


def dimensions(grid: Grid) -> tuple[int, int]:
    """How many cells wide and tall `grid` is."""
    return (len(grid[0]) if grid else 0), len(grid)


@dataclass(frozen=True, slots=True, eq=False)
class Crossing:
    """
    One transition drawn from pictures, as long as `duration`. Compared by identity, so each navigation plays afresh,
    even one that looks the same.
    """

    frames: Frames
    duration: timedelta


@dataclass(frozen=True, slots=True)
class Drawing:
    """A canvas's painter for `crossing`, `progress` of the way through it."""

    crossing: Crossing
    progress: float

    @property
    def natural_size(self) -> tuple[int, int]:
        return 0, 0

    @property
    def keeps_aspect_ratio(self) -> bool:
        return False

    def draw(self, width: int, height: int) -> Rows:
        return rows_of(self.crossing.frames(self.progress))


async def photograph(slide: Component, width: int, height: int) -> Grid:
    """
    The first frame `slide` draws, rendered headless at `width` by `height`. In a task of its own,
    so the app it runs sets its context variables in a copy of the caller's context, rather than in the deck's.
    On a frozen clock, so a title card's pulse is where it starts rather than wherever the render's own few
    milliseconds took it, which would make the showcases record differently every time.
    """
    frames: list[Frame] = []
    await create_task(
        app(
            slide,
            headless=True,
            dimensions=(width, height),
            autopilot=(Screenshot(handler=frames.append), Quit()),
            clock=PHOTOGRAPHED,
        )
    )
    (frame,) = frames
    return picture_of(frame.paint, frame.paint.bounds)
