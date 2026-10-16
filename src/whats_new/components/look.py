"""The deck's palette and the small styled pieces every section uses: headings, bullets, title cards."""

from counterweight.components import Component
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles import CellStyle
from counterweight.styles import Color
from counterweight.styles import Style
from counterweight.styles.utilities import *

PYTHON_BLUE = Color.from_hex("#4B8BBE")
PYTHON_YELLOW = Color.from_hex("#FFD43B")
CLAUDE_ORANGE = Color.from_hex("#D77757")
"""The orange Claude Code draws its spark and mascot in."""

CLAUDE_SPARK = "✻"
CLAUDE_MASCOT = " ▐▛███▜▌\n▝▜█████▛▘\n  ▘▘ ▝▝"
"""Claude Code's mascot, as its welcome screen draws it."""

bold = Style(text_style=CellStyle(bold=True))
dim = text_color("slate", 400)
emphasis = text_color("amber", 300)
heading_style = bold | Style(text_style=CellStyle(foreground=PYTHON_YELLOW))
code_border = border | border_heavy | Style(border_style=CellStyle(foreground=PYTHON_BLUE))


def drop_shadow(*children: Text | Div) -> Div:
    """
    `children` in a light-shade shadow: an outer box bordered only right and bottom,
    contracted by a cell so the shadow starts one cell in from the top and left.
    """
    return Div(
        style=border_right | border_bottom | border_lightshade | border_contract(1) | border_color("gray", 400),
        children=children,
    )


def title_card(title: str, subtitle: str = "") -> Div:
    """A centered, heavily bordered card in a drop shadow, for section and talk titles."""
    lines: tuple[Chunk, ...] = (Chunk(content=title, style=CellStyle(bold=True, foreground=PYTHON_YELLOW)),)
    if subtitle:
        lines = (*lines, Chunk.newline(), Chunk(content=subtitle, style=CellStyle(foreground=PYTHON_BLUE)))
    return drop_shadow(
        Text(
            content=lines,
            style=border | border_heavy | border_color("slate", 300) | pad_x(4) | pad_y(1) | text_justify_center,
        )
    )


def centered(*children: Component | Text | Div) -> Div:
    """`children` stacked in the middle of the slide."""
    return Div(style=col | fill(1) | center_children | gap_height(1), children=children)


def bullets(*items: str | Chunk | tuple[Chunk, ...]) -> Text:
    """A bulleted list, one item per line, each plain text, one chunk, or several."""
    chunks: list[Chunk] = []
    for item in items:
        if chunks:
            chunks.append(Chunk.newline())
        chunks.append(Chunk(content="• ", style=CellStyle(foreground=PYTHON_BLUE)))
        match item:
            case str():
                chunks.append(Chunk(content=item))
            case Chunk():
                chunks.append(item)
            case tuple():
                chunks.extend(item)
    return Text(content=tuple(chunks), style=text_wrap_pretty)


def code(text: str) -> Chunk:
    """Inline code in prose."""
    return Chunk(content=text, style=CellStyle(foreground=Color.from_hex("#79c0ff")))


def plain(text: str) -> Chunk:
    return Chunk(content=text)


def em(text: str) -> Chunk:
    return Chunk(content=text, style=CellStyle(foreground=PYTHON_YELLOW, bold=True))


def link(url: str) -> Chunk:
    """`url` without its scheme, as an OSC 8 hyperlink to it, for a terminal that opens links."""
    return Chunk(
        content=url.removeprefix("https://"),
        style=CellStyle(foreground=PYTHON_BLUE, underline=True, link=url),
    )


def made_with_claude() -> Text:
    """The disclosure that this deck was built with help from Claude Code, under Claude's spark, in its orange."""
    return Text(
        content=(
            Chunk(content=f"{CLAUDE_SPARK} ", style=CellStyle(foreground=CLAUDE_ORANGE, bold=True)),
            Chunk(content="built with help from Claude Code", style=CellStyle(foreground=CLAUDE_ORANGE)),
        ),
    )


def claude_mascot() -> Text:
    return Text(
        content=CLAUDE_MASCOT, style=Style(text_style=CellStyle(foreground=CLAUDE_ORANGE)) | text_wrap_none | shrink(0)
    )
