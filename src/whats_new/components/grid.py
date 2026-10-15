"""
The slide grid: thumbnails of the whole deck, three across, windowed three rows at a time around the selection.

Each thumbnail is the slide's own content component drawn at a third of the width and clipped at its border,
not a picture, so it's exactly what the slide draws at that width. Thumbnails aren't live: they never take focus,
so they never receive a slide's keys or start its runs.
"""

from collections.abc import Callable

from counterweight.components import component
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.handlers import on_click
from counterweight.styles.utilities import *

from whats_new.components.look import dim
from whats_new.host import Host
from whats_new.slides import Slide
from whats_new.slides import SlideProps

COLUMNS = 3
ROWS = 3


def visible_range(selected: int, total: int) -> range:
    """The slide indexes the grid shows: three rows, with the selected row in the middle where the deck allows."""
    selected_row = selected // COLUMNS
    row_count = -(-total // COLUMNS)
    first_row = max(0, min(selected_row - ROWS // 2, row_count - ROWS))
    return range(first_row * COLUMNS, min(total, (first_row + ROWS) * COLUMNS))


@component
def thumbnail(
    slides: tuple[Slide, ...],
    index: int,
    is_selected: bool,
    jump: Callable[[int], None],
    host: Host,
) -> Div:
    slide = slides[index]
    props = SlideProps(step=slide.steps - 1, is_live=False, host=host, runs=slide.runs)
    return Div(
        style=col
        | border
        | border_lightrounded
        | overflow_hidden
        | (border_color("amber", 300) if is_selected else border_color("slate", 600)),
        on_input=on_click(lambda: jump(index)),
        children=(
            Text(content=f"{index + 1} | {slide.title}", style=(text_color("amber", 300) if is_selected else dim)),
            Div(style=col | fill(1) | overflow_hidden, children=(slide.content(props),)),
        ),
    )


@component
def grid(slides: tuple[Slide, ...], selected: int, jump: Callable[[int], None], host: Host) -> Div:
    return Div(
        style=display_grid
        | full
        | grid_template_columns(*(fr() for _ in range(COLUMNS)))
        | grid_template_rows(*(fr() for _ in range(ROWS))),
        children=tuple(
            # Keyed by slide index, so moving the selection a row mounts one new row and keeps the other two.
            thumbnail(slides, index, index == selected, jump, host).with_key(str(index))
            for index in visible_range(selected, len(slides))
        ),
    )
