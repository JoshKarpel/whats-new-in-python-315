"""
The pieces diagrams are drawn from: a fixed-size area, bordered nodes placed at cell coordinates inside it,
and runs of box-drawing text for edges and labels, placed the same way.

Coordinates are cells from the area's top-left corner, so a diagram is drawn for one width:
the presenting size's.
"""

from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles import CellStyle
from counterweight.styles import Color
from counterweight.styles import Style
from counterweight.styles.utilities import *

from whats_new.components.look import PYTHON_BLUE
from whats_new.components.look import PYTHON_YELLOW

NODE = border | border_heavy | border_color("slate", 300) | pad_x(1)
EDGE = CellStyle(foreground=Color.from_hex("#94a3b8"))
CROSSED = CellStyle(foreground=Color.from_hex("#f87171"), bold=True)
HIGHLIGHT = CellStyle(foreground=PYTHON_YELLOW, bold=True)
NOTE = CellStyle(foreground=PYTHON_BLUE)
HIGHLIGHT_NODE = Style(text_style=HIGHLIGHT)


def area(columns: int, rows: int, *children: Text | Div, style: Style = default) -> Div:
    """A `columns` by `rows` box that positions `children` from its top-left corner."""
    return Div(style=position_relative | size(columns, rows) | shrink(0) | style, children=children)


def at(x: int, y: int) -> Style:
    return position_absolute | inset_left(x) | inset_top(y)


def node(label: str | tuple[Chunk, ...], x: int, y: int, style: Style = default) -> Text:
    """A bordered box around `label` with its top-left corner at `x`, `y`."""
    return Text(content=label, style=NODE | at(x, y) | style)


def ink(content: str | tuple[Chunk, ...], x: int, y: int, style: CellStyle = EDGE) -> Text:
    """Text (an edge, an arrow, a label) starting at `x`, `y`, which may span several lines."""
    chunks = (Chunk(content=content, style=style),) if isinstance(content, str) else content
    return Text(content=chunks, style=at(x, y) | text_wrap_none)
