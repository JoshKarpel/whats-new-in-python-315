"""
The slide grid: thumbnails of one section of the deck at a time, three across, windowed three rows at a time around
the selection, under a line naming the section. Moving the selection past a section's edge moves into the next one.

Each thumbnail is the slide's own content component drawn at a third of the width and clipped at its border,
not a picture, so it's exactly what the slide draws at that width. It draws the slide's first reveal step, the one
jumping to it lands on, so the grid's transitions into and out of a slide meet the slide as it shows.
Thumbnails aren't live: they never take focus, so they never receive a slide's keys or start its runs.

With F7's `zoom` picked, the grid zooms, easing in and out, at F8's speed. Opening, the selected thumbnail
starts filling the grid and shrinks into its place while the others grow in around it; leaving, the selected
thumbnail grows back to fill it. Its content reflows as it changes size, as a thumbnail's always does, rather than
scaling. The grid sits over the stage, so the slide it leaves for is already mounted, and live, beneath it.
F7's other transitions are drawn from pictures of the grid (see `crossing`), and `tiles` says where in one
each thumbnail is.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from counterweight.components import component
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.events import InputResponse
from counterweight.focus import FocusHandle
from counterweight.geometry import Region
from counterweight.handlers import on_click
from counterweight.hooks import use_state
from counterweight.styles import CellStyle
from counterweight.styles.utilities import *

from whats_new.components.animation import use_loop
from whats_new.components.animation import use_progress_since
from whats_new.components.crossing import Tiles
from whats_new.components.easing import ease_in_out
from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.look import TURN_PERIOD
from whats_new.components.look import dim
from whats_new.components.look import turning_edge
from whats_new.components.slide_body import slide_body
from whats_new.components.swipe import SWIPE
from whats_new.host import Host
from whats_new.slides import Slide
from whats_new.slides import sections

COLUMNS = 3
ROWS = 3
HEADER = 1
"""How many rows the line naming the section takes, above the thumbnails."""


class Toward(Enum):
    """Which way the grid zooms: out to the grid as it opens, or in to the selected slide as it closes."""

    GRID = "grid"
    SLIDE = "slide"


@dataclass(frozen=True, slots=True, eq=False)
class Zoom:
    """
    One zoom of the grid. Compared by identity, so each opening or closing plays afresh, even one that looks the same.
    """

    toward: Toward
    duration: timedelta

    def openness(self, progress: float) -> float:
        """
        How open the grid is `progress` of the way through the zoom: 0 with the selected thumbnail filling it,
        1 with every thumbnail in its place.
        """
        eased = ease_in_out(progress)
        return eased if self.toward is Toward.GRID else 1 - eased


@dataclass(frozen=True, slots=True)
class Cell:
    """Where a slide sits in the grid: its section's position in the deck, and its row and column in that section."""

    section: int
    row: int
    column: int


def cell_of(index: int, deck_sections: tuple[range, ...]) -> Cell:
    for number, section in enumerate(deck_sections):
        if index in section:
            row, column = divmod(index - section.start, COLUMNS)
            return Cell(section=number, row=row, column=column)
    raise IndexError(f"no slide {index} in a deck of {deck_sections[-1].stop}")


def last_row(section: range) -> int:
    return (len(section) - 1) // COLUMNS


def index_at(section: range, row: int, column: int) -> int:
    """The slide at `row` and `column` of `section`, or the last in that row if the row is shorter."""
    return min(section.start + row * COLUMNS + column, section.stop - 1)


def above(index: int, slides: tuple[Slide, ...]) -> int:
    """
    The slide above `index` in the grid: in the row above, or the previous section's last row from its first,
    or the deck's first slide from the first section's first row.
    """
    deck_sections = sections(slides)
    cell = cell_of(index, deck_sections)
    if cell.row > 0:
        return index_at(deck_sections[cell.section], cell.row - 1, cell.column)
    if cell.section == 0:
        return 0
    previous = deck_sections[cell.section - 1]
    return index_at(previous, last_row(previous), cell.column)


def below(index: int, slides: tuple[Slide, ...]) -> int:
    """
    The slide below `index` in the grid: in the row below, or the next section's first row from its last,
    or the deck's last slide from the last section's last row.
    """
    deck_sections = sections(slides)
    cell = cell_of(index, deck_sections)
    section = deck_sections[cell.section]
    if cell.row < last_row(section):
        return index_at(section, cell.row + 1, cell.column)
    if cell.section == len(deck_sections) - 1:
        return len(slides) - 1
    return index_at(deck_sections[cell.section + 1], 0, cell.column)


def visible_range(selected: int, section: range) -> range:
    """The slide indexes the grid shows: three rows of `section`, with the selected row in the middle where it can."""
    selected_row = (selected - section.start) // COLUMNS
    first_row = max(0, min(selected_row - ROWS // 2, last_row(section) + 1 - ROWS))
    start = section.start + first_row * COLUMNS
    return range(start, min(section.stop, start + ROWS * COLUMNS))


def shares(selected: int, count: int, openness: float) -> tuple[float, ...]:
    """
    The share of the grid's width (or height) each of `count` tracks takes, `openness` of the way from the `selected`
    track taking all of it to every track taking an equal share.
    """
    others = openness / count
    return tuple(1 - others * (count - 1) if track == selected else others for track in range(count))


def edges(length: int, count: int) -> tuple[int, ...]:
    """
    Where each of `count` equal tracks sharing `length` cells starts, and the last ends: each edge rounded to the
    nearest cell, as the layout rounds the grid's equal `fr` tracks, so the odd cells go wherever rounding puts them.
    """
    return tuple(round(length * track / count) for track in range(count + 1))


def tiles(width: int, height: int, selected: int, slides: tuple[Slide, ...]) -> Tiles:
    """Where the open grid, drawn `width` by `height` with `selected` selected, draws its header and thumbnails."""
    deck_sections = sections(slides)
    visible = visible_range(selected, deck_sections[cell_of(selected, deck_sections).section])
    across, down = edges(width, COLUMNS), edges(height - HEADER, ROWS)

    def region(index: int) -> Region:
        row, column = divmod(index - visible.start, COLUMNS)
        return Region(
            left=across[column], top=HEADER + down[row], right=across[column + 1], bottom=HEADER + down[row + 1]
        )

    return Tiles(
        header=Region(left=0, top=0, right=width, bottom=HEADER),
        thumbnails=tuple(region(index) for index in visible),
        selected=selected - visible.start,
    )


@component
def thumbnail(
    slides: tuple[Slide, ...],
    index: int,
    is_selected: bool,
    jump: Callable[[int], InputResponse],
    host: Host,
    code_theme: str,
) -> Div:
    """
    One slide's thumbnail, which jumps to it when clicked. The selected one's border turns as a title card's does,
    counting from the thumbnail's mount, so a picture of the grid moved on by a transition's length draws it
    where the live grid does when the transition ends.
    """
    slide = slides[index]
    # Its own, never the live slide's: a thumbnail never takes focus, but a handle names one component at a time.
    thumbnail_focus, _ = use_state(FocusHandle)
    border_phase = use_loop(TURN_PERIOD, is_playing=is_selected)
    return Div(
        style=col
        | border
        | border_lightrounded
        | overflow_hidden
        | (border_gradient(turning_edge(border_phase)) if is_selected else border_color("slate", 600)),
        on_input=on_click(lambda: jump(index)),
        children=(
            Text(content=f"{index + 1} | {slide.title}", style=(text_color("amber", 300) if is_selected else dim)),
            Div(
                style=col | fill(1) | overflow_hidden,
                children=(slide_body(slide, 0, False, host, code_theme, thumbnail_focus),),
            ),
        ),
    )


@component
def grid(
    slides: tuple[Slide, ...],
    selected: int,
    jump: Callable[[int], InputResponse],
    host: Host,
    code_theme: str,
    zoom: Zoom | None,
) -> Div:
    """
    The grid, over the stage, playing `zoom` from when it changes to another one: without one, it's open.
    Once a zoom in to the selected slide ends, it draws nothing, leaving the slide beneath it in view.
    """
    deck_sections = sections(slides)
    cell = cell_of(selected, deck_sections)
    section = deck_sections[cell.section]
    visible = visible_range(selected, section)
    progress = use_progress_since(zoom, SWIPE if zoom is None else zoom.duration)
    if zoom is not None and zoom.toward is Toward.SLIDE and progress >= 1.0:
        return Div(style=display_none)
    openness = 1.0 if zoom is None else zoom.openness(progress)
    # The selected row within the window, which isn't its row in the section once the window has moved down.
    row = (selected - visible.start) // COLUMNS
    return Div(
        style=position_absolute | inset_top(0) | inset_left(0) | full | col,
        children=(
            Text(
                content=(
                    Chunk(content=slides[section.start].title, style=CellStyle(foreground=PYTHON_YELLOW, bold=True)),
                    Chunk(content=f"  section {cell.section + 1} of {len(deck_sections)}", style=CellStyle(dim=True)),
                ),
                style=pad_x(1) | shrink(0),
            ),
            Div(
                style=display_grid
                | fill(1)
                | overflow_hidden
                | grid_template_columns(*(fr(share) for share in shares(cell.column, COLUMNS, openness)))
                | grid_template_rows(*(fr(share) for share in shares(row, ROWS, openness))),
                children=tuple(
                    # Keyed by slide index, so moving the selection a row mounts one new row and keeps the other two.
                    thumbnail(slides, index, index == selected, jump, host, code_theme).with_key(str(index))
                    for index in visible
                ),
            ),
        ),
    )
