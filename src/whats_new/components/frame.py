"""The frame around every presented slide: its heading, the PEP link line, and the footer."""

from collections.abc import Callable
from datetime import timedelta
from datetime import tzinfo

from counterweight.components import component
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.hooks import use_clock
from counterweight.styles import CellStyle
from counterweight.styles import Style
from counterweight.styles.utilities import *

from whats_new.components.look import PYTHON_BLUE
from whats_new.components.look import dim
from whats_new.components.look import heading_style
from whats_new.size import PRESENTING
from whats_new.slides import pep_url

TALK_TITLE = "What's New in Python 3.15"


def heading(title: str, peps: tuple[int, ...]) -> Text:
    """
    The slide's title, centered on its top row, after the PEPs it cites: `PEP 814: frozendict`.
    Each `PEP <n>` is an OSC 8 hyperlink to it, and the URL isn't spelled out, since from a seat,
    searching for "PEP 814" is quicker than typing one, and a line of links would cost a row on every such slide.
    """
    links: list[Chunk] = []
    for number in peps:
        if links:
            links.append(Chunk(content=", "))
        links.append(
            Chunk(
                content=f"PEP {number}",
                style=CellStyle(foreground=PYTHON_BLUE, bold=True, underline=True, link=pep_url(number)),
            )
        )
    prefix = (*links, Chunk(content=": ")) if links else ()
    return Text(
        content=(*prefix, Chunk(content=title)), style=heading_style | pad_x(1) | shrink(0) | text_justify_center
    )


@component
def footer(
    index: int,
    total: int,
    show_clock: bool,
    show_size: bool,
    columns: int,
    rows: int,
    timezone: tzinfo,
    last_frame: Callable[[], timedelta | None] | None,
) -> Div:
    """
    The talk's title and the slide number, with the clock (F1), the size check (F2) and the frame time (F3,
    shown when `last_frame` is given) between them.
    The clock reads 12-hour time in `timezone`, not the machine's, which on the presenting VM is UTC.
    The size check is green when the terminal is exactly the presenting width (and at least its height),
    and red otherwise, so a wrong browser zoom shows before the first diagram.
    """
    now = use_clock(timedelta(seconds=15)).now
    middle: list[Text] = []
    if show_clock:
        middle.append(
            Text(content=f"{now.astimezone(timezone):%I:%M %p}".removeprefix("0"), style=text_color("slate", 200))
        )
    if show_size:
        middle.append(
            Text(
                content=(
                    Chunk(
                        content=f"{columns}",
                        style=CellStyle(
                            foreground=COLOR_OK if PRESENTING.fits_width(columns) else COLOR_BAD,
                        ),
                    ),
                    Chunk(content="x"),
                    Chunk(
                        content=f"{rows}",
                        style=CellStyle(foreground=COLOR_OK if PRESENTING.fits_height(rows) else COLOR_BAD),
                    ),
                    Chunk(content=f" (want {PRESENTING.columns}x{PRESENTING.rows})", style=CellStyle(dim=True)),
                ),
            )
        )
    return Div(
        style=row | justify_children_space_between | shrink(0) | border_top | border_light | border_color("slate", 600),
        children=(
            Text(content=TALK_TITLE, style=dim | pad_x(1)),
            Div(
                style=row | gap_width(2),
                children=(*middle, *(() if last_frame is None else (frame_time(last_frame),))),
            ),
            Text(content=f"{index + 1} / {total}", style=dim | pad_x(1)),
        ),
    )


@component
def frame_time(last_frame: Callable[[], timedelta | None]) -> Text:
    """
    How long the last frame took to render, re-read twice a second, which renders a frame itself:
    green within one 60 Hz refresh, amber within two, red beyond.
    """
    use_clock(FRAME_TIME_INTERVAL)
    last = last_frame()
    if last is None:
        return Text(content="frame: -", style=dim)
    color = COLOR_OK if last <= ONE_REFRESH else COLOR_SLOW if last <= 2 * ONE_REFRESH else COLOR_BAD
    return Text(
        content=f"frame {last.total_seconds() * 1000:.1f} ms", style=Style(text_style=CellStyle(foreground=color))
    )


FRAME_TIME_INTERVAL = timedelta(milliseconds=500)
ONE_REFRESH = timedelta(seconds=1 / 60)

COLOR_OK = green_300
COLOR_SLOW = amber_300
COLOR_BAD = red_400
