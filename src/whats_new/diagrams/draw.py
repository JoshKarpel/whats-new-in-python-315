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


def text_width(content: str | tuple[Chunk, ...]) -> int:
    """How many cells one line of diagram text takes: every diagram label is one cell per code point."""
    return len(content) if isinstance(content, str) else sum(len(chunk.content) for chunk in content)


def node_width(label: str | tuple[Chunk, ...]) -> int:
    """How many cells wide `node` draws `label`'s box: the label, a cell of padding each side, and the border."""
    return text_width(label) + 4


def middle(x: int, label: str | tuple[Chunk, ...]) -> int:
    """The column a connector meets the box `node(label, x, ...)` at: its middle, or right of it for an even width."""
    return x + node_width(label) // 2


def centered_node(label: str | tuple[Chunk, ...], column: int, y: int, style: Style = default) -> Text:
    """A `node` whose middle (see `middle`) is at `column`, so a connector drawn at `column` meets it squarely."""
    return node(label, column - node_width(label) // 2, y, style)


def ink(content: str | tuple[Chunk, ...], x: int, y: int, style: CellStyle = EDGE) -> Text:
    """Text (an edge, an arrow, a label) starting at `x`, `y`, which may span several lines."""
    chunks = (Chunk(content=content, style=style),) if isinstance(content, str) else content
    return Text(content=chunks, style=at(x, y) | text_wrap_none)


def centered_ink(content: str | tuple[Chunk, ...], column: int, y: int, style: CellStyle = EDGE) -> Text:
    """One line of `ink` centered on `column`, such as a label under a box."""
    return ink(content, column - text_width(content) // 2, y, style)


def fork(parent: int, children: tuple[int, ...], y: int) -> tuple[Text, Text]:
    """
    The two rows joining a box above, whose middle is at column `parent`, to boxes below whose middles are at
    `children`, left to right: a bar that rises at `parent` and drops at each child, then a `│` down to each.
    """
    left, right = min(parent, *children), max(parent, *children)
    bar = []
    for column in range(left, right + 1):
        rises, drops = column == parent, column in children
        if drops and column == left:
            bar.append("┌")
        elif drops and column == right:
            bar.append("┐")
        elif rises and drops:
            bar.append("┼")
        elif drops:
            bar.append("┬")
        elif rises:
            bar.append("┴")
        else:
            bar.append("─")
    stems = "".join("│" if column in children else " " for column in range(left, right + 1))
    return ink("".join(bar), left, y), ink(stems, left, y + 1)
