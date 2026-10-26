"""
The sections list Ctrl+D opens in the slide's place: one row per section of the deck, named by its title card,
with how many slides it has. Up and Down move the highlight, and Enter or a click opens the slide grid on that
section's title card, so the list is for crossing the deck and the grid for picking a slide within a section.
"""

from collections.abc import Callable
from functools import partial

from counterweight.components import component
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.events import InputResponse
from counterweight.handlers import on_click
from counterweight.styles.utilities import *

from whats_new.components.look import dim
from whats_new.components.look import highlight
from whats_new.slides import Slide
from whats_new.slides import sections

HINT = "↑ ↓ · Enter opens the grid there · Esc closes"


@component
def section_list(slides: tuple[Slide, ...], highlighted: int, open_section: Callable[[int], InputResponse]) -> Div:
    """
    Every section of `slides`, the one numbered `highlighted` highlighted, numbered from 1 as the grid's header
    numbers them. Clicking a row calls `open_section` with its number, counting from 0.
    """
    deck_sections = sections(slides)
    titles = tuple(slides[section.start].title for section in deck_sections)
    title_width = max(len(title) for title in titles)
    number_width = len(str(len(deck_sections)))
    rows = tuple(
        Text(
            content=(
                Chunk(content="▸ " if number == highlighted else "  ", style=highlight),
                Chunk(content=f"{number + 1:>{number_width}}  ", style=dim),
                Chunk(content=f"{title:<{title_width}}  ", style=highlight if number == highlighted else default),
                Chunk(content=f"{len(section):>2} slide{'' if len(section) == 1 else 's'}", style=dim),
            ),
            style=text_wrap_none | (text_bg("sky", 800) if number == highlighted else default),
            on_input=on_click(partial(open_section, number)),
        )
        for number, (title, section) in enumerate(zip(titles, deck_sections, strict=True))
    )
    return Div(
        style=position_absolute | inset_top(0) | inset_left(0) | full | col | center_children | gap_height(1),
        children=(
            Text(content="Sections", style=highlight),
            Div(style=col | shrink(0), children=rows),
            Text(content=HINT, style=dim | text_wrap_none),
        ),
    )
