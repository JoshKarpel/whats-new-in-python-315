"""The frame around every presented slide: its heading, the PEP link line, and the footer."""

from datetime import timedelta

from counterweight.components import component
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.hooks import use_clock
from counterweight.styles import CellStyle
from counterweight.styles.utilities import *

from whats_new.components.look import PYTHON_BLUE
from whats_new.components.look import dim
from whats_new.components.look import heading_style
from whats_new.size import PRESENTING
from whats_new.slides import pep_url

TALK_TITLE = "What's New in Python 3.15"


def heading(title: str) -> Text:
    return Text(content=title, style=heading_style | pad_x(1) | shrink(0))


def pep_links(peps: tuple[int, ...]) -> Text:
    """
    One line linking every PEP a slide cites, as OSC 8 hyperlinks whose text is also the URL,
    so a terminal that only detects URLs in text can open them too.
    """
    chunks: list[Chunk] = []
    for number in peps:
        if chunks:
            chunks.append(Chunk(content="  "))
        url = pep_url(number)
        chunks.append(Chunk(content=f"PEP {number} ", style=CellStyle(foreground=PYTHON_BLUE, bold=True)))
        chunks.append(Chunk(content=url, style=CellStyle(foreground=PYTHON_BLUE, underline=True, link=url)))
    return Text(content=tuple(chunks), style=pad_x(1) | shrink(0))


@component
def footer(index: int, total: int, show_clock: bool, show_size: bool, columns: int, rows: int) -> Div:
    """
    The talk's title and the slide number, with the clock (F1) and the size check (F2) between them.
    The size check is green when the terminal is exactly the presenting width (and at least its height),
    and red otherwise, so a wrong browser zoom shows before the first diagram.
    """
    now = use_clock(timedelta(seconds=15)).now
    middle: list[Text] = []
    if show_clock:
        middle.append(Text(content=f"{now:%H:%M}", style=text_color("slate", 200)))
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
            Div(style=row | gap_width(2), children=tuple(middle)),
            Text(content=f"{index + 1} / {total}", style=dim | pad_x(1)),
        ),
    )


COLOR_OK = green_300
COLOR_BAD = red_400
