"""
"Spin̈al Tap" as code points under grapheme brackets: the n̈ is two code points, n and a combining diaeresis,
under one grapheme.
"""

from unicodedata import combining
from unicodedata import iter_graphemes

from counterweight.elements import Chunk
from counterweight.elements import Text
from counterweight.styles import CellStyle
from counterweight.styles.utilities import *

from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import NOTE

BAND = "Spin̈al Tap"
CELL = 7
"""Wide enough for a `U+XXXX` label and a space."""

DOTTED_CIRCLE = "◌"
"""The conventional base for showing a combining mark on its own, so it doesn't combine with its neighbor."""


def glyph(code_point: str) -> str:
    """How one code point is drawn under its label: a combining mark on a dotted circle, a space as a visible ␣."""
    if combining(code_point):
        return DOTTED_CIRCLE + code_point
    if code_point == " ":
        return "␣"
    return code_point


def bracket(width: int, label: str) -> str:
    """A bracket `width` cells wide over one grapheme's code points, with `label` centered in its top edge."""
    return "┌" + label.center(width - 2, "─") + "┐"


def band_code_points() -> Text:
    graphemes = [str(g) for g in iter_graphemes(BAND)]
    brackets: list[Chunk] = []
    points: list[Chunk] = []
    glyphs: list[Chunk] = []
    for grapheme in graphemes:
        is_combined = len(grapheme) > 1
        brackets.append(
            Chunk(
                content=bracket(len(grapheme) * CELL, " 1 grapheme " if is_combined else ""),
                style=HIGHLIGHT if is_combined else EDGE,
            )
        )
        for code_point in grapheme:
            points.append(Chunk(content=f"U+{ord(code_point):04X}".center(CELL), style=NOTE))
            # center() counts code points, so a mark drawn on a dotted circle pads as if it took two cells.
            drawn = glyph(code_point)
            glyphs.append(Chunk(content=drawn.center(CELL + len(drawn) - 1)))
    return Text(
        content=(
            *brackets,
            Chunk.newline(),
            *points,
            Chunk.newline(),
            *glyphs,
            Chunk.newline(),
            Chunk(content=f"{len(BAND)} code points, {len(graphemes)} graphemes", style=CellStyle(dim=True)),
        ),
        style=text_wrap_none | shrink(0),
    )
