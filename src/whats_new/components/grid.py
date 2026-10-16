"""
The slide grid: thumbnails of one section of the deck at a time, three across, windowed three rows at a time around
the selection, under a line naming the section. Moving the selection past a section's edge moves into the next one.

Each thumbnail is the slide's own content component drawn at a third of the width and clipped at its border,
not a picture, so it's exactly what the slide draws at that width. Thumbnails aren't live: they never take focus,
so they never receive a slide's keys or start its runs.
"""

from collections.abc import Callable
from dataclasses import dataclass

from counterweight.components import component
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.focus import FocusHandle
from counterweight.handlers import on_click
from counterweight.hooks import use_state
from counterweight.styles import CellStyle
from counterweight.styles.utilities import *

from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.look import dim
from whats_new.components.slide_body import slide_body
from whats_new.host import Host
from whats_new.slides import Slide
from whats_new.slides import sections

COLUMNS = 3
ROWS = 3


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


@component
def thumbnail(
    slides: tuple[Slide, ...],
    index: int,
    is_selected: bool,
    jump: Callable[[int], None],
    host: Host,
    code_theme: str,
) -> Div:
    slide = slides[index]
    # Its own, never the live slide's: a thumbnail never takes focus, but a handle names one component at a time.
    thumbnail_focus, _ = use_state(FocusHandle)
    return Div(
        style=col
        | border
        | border_lightrounded
        | overflow_hidden
        | (border_color("amber", 300) if is_selected else border_color("slate", 600)),
        on_input=on_click(lambda: jump(index)),
        children=(
            Text(content=f"{index + 1} | {slide.title}", style=(text_color("amber", 300) if is_selected else dim)),
            Div(
                style=col | fill(1) | overflow_hidden,
                children=(slide_body(slide, slide.steps - 1, False, host, code_theme, thumbnail_focus),),
            ),
        ),
    )


@component
def grid(slides: tuple[Slide, ...], selected: int, jump: Callable[[int], None], host: Host, code_theme: str) -> Div:
    deck_sections = sections(slides)
    number = cell_of(selected, deck_sections).section
    section = deck_sections[number]
    return Div(
        style=col | full,
        children=(
            Text(
                content=(
                    Chunk(content=slides[section.start].title, style=CellStyle(foreground=PYTHON_YELLOW, bold=True)),
                    Chunk(content=f"  section {number + 1} of {len(deck_sections)}", style=CellStyle(dim=True)),
                ),
                style=pad_x(1) | shrink(0),
            ),
            Div(
                style=display_grid
                | fill(1)
                | grid_template_columns(*(fr() for _ in range(COLUMNS)))
                | grid_template_rows(*(fr() for _ in range(ROWS))),
                children=tuple(
                    # Keyed by slide index, so moving the selection a row mounts one new row and keeps the other two.
                    thumbnail(slides, index, index == selected, jump, host, code_theme).with_key(str(index))
                    for index in visible_range(selected, section)
                ),
            ),
        ),
    )
