"""The frame around every presented slide: its heading, the PEP link line, and the footer."""

from datetime import timedelta
from datetime import tzinfo

from counterweight.components import component
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.gradients import LinearGradient
from counterweight.gradients import linear_gradient
from counterweight.gradients import ramp
from counterweight.hooks import use_clock
from counterweight.styles.utilities import *

from whats_new.components.look import PYTHON_BLUE
from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.look import dim
from whats_new.components.look import heading_style
from whats_new.components.look import linked
from whats_new.size import PRESENTING
from whats_new.slides import pep_url

TALK_TITLE = "What's New in Python 3.15"
PROGRESS = linear_gradient(PYTHON_BLUE, PYTHON_YELLOW, to="right", interpolation="oklch")
"""
The colors the footer's rule fills with, left to right, as the deck goes on: Python's blue, through teal and green,
to its yellow. Mixed in Oklch, since blue and yellow are opposites, which Oklab mixes through gray.
"""


def heading(title: str, peps: tuple[int, ...]) -> Text:
    """
    The slide's title, at the left of its top row, where a thumbnail's title sits, after the PEPs it cites: `PEP 814: frozendict`.
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
                style=text_bold | linked(pep_url(number)),
            )
        )
    prefix = (*links, Chunk(content=": ")) if links else ()
    return Text(content=(*prefix, Chunk(content=title)), style=heading_style | pad_x(1) | shrink(0))


@component
def footer(
    index: int,
    total: int,
    show_clock: bool,
    show_size: bool,
    columns: int,
    rows: int,
    timezone: tzinfo,
) -> Div:
    """
    The talk's title and the slide number, with the clock (F1) and the size check (F2) between them.
    The clock reads 12-hour time in `timezone`, not the machine's, which on the presenting VM is UTC.
    The size check is green when the terminal is exactly the presenting width (and at least its height),
    and red otherwise, so a wrong browser zoom shows before the first diagram.
    The rule above them is a progress bar through the deck (see `progress_rule`).
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
                        style=text_color(COLOR_OK if PRESENTING.fits_width(columns) else COLOR_BAD),
                    ),
                    Chunk(content="x"),
                    Chunk(
                        content=f"{rows}",
                        style=text_color(COLOR_OK if PRESENTING.fits_height(rows) else COLOR_BAD),
                    ),
                    Chunk(content=f" (want {PRESENTING.columns}x{PRESENTING.rows})", style=text_dim),
                ),
            )
        )
    return Div(
        style=row
        | justify_children_space_between
        | shrink(0)
        | border_top
        | border_light
        | border_gradient(progress_rule(index, total)),
        children=(
            Text(content=TALK_TITLE, style=dim | pad_x(1)),
            Div(style=row | gap_width(2), children=tuple(middle)),
            Text(content=f"{index + 1} / {total}", style=dim | pad_x(1)),
        ),
    )


def progress_rule(index: int, total: int) -> LinearGradient:
    """
    The footer's rule on slide `index` of `total`: `PROGRESS` from the left as far across as the slide is through
    the deck, and slate past it. The fill reveals `PROGRESS` in place rather than squeezing all of it into the fill,
    so how far along the talk is reads from the color at the fill's end too.
    """
    done = (index + 1) / total
    colors = ramp(PROGRESS)
    return linear_gradient(
        (PYTHON_BLUE, 0),
        (colors.color(colors.index(done)), done),
        (slate_600, done),
        to="right",
        interpolation="oklch",
    )


COLOR_OK = green_300
COLOR_BAD = red_400
