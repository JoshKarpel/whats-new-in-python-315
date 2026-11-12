"""
Text in layers, for an audience that hasn't had to think about Unicode: bytes, code points, graphemes,
then what a font and a terminal do with them; and "Spinal Tap", with an umlaut on its n, as code points under grapheme brackets.

Nothing here draws a combining mark itself. zellij, which the talk is presented through, drops every zero-width
code point (zellij-org/zellij#5500), so a mark is drawn as its spacing look-alike, which every terminal shows.
"""

from unicodedata import combining
from unicodedata import iter_graphemes
from unicodedata import name

from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles import CellStyle
from counterweight.styles.utilities import *

from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import NOTE
from whats_new.diagrams.draw import area
from whats_new.diagrams.draw import ink

BAND = "Spin\N{COMBINING DIAERESIS}al Tap"
CAFE = "cafe\N{COMBINING ACUTE ACCENT}"
CELL = 7
"""Wide enough for a `U+XXXX` label and a space."""

SPACING = {"\N{COMBINING DIAERESIS}": "\N{DIAERESIS}", "\N{COMBINING ACUTE ACCENT}": "\N{ACUTE ACCENT}"}
"""Each combining mark the diagrams show, as the spacing character that looks like it."""

PRECOMPOSED = {"e\N{COMBINING ACUTE ACCENT}": "\N{LATIN SMALL LETTER E WITH ACUTE}"}
"""
How a grapheme is drawn in the "what you see" row: as its one-code-point spelling, where it has one,
since zellij would drop the combining mark from the spelling the row is about.
"""


def glyph(code_point: str) -> str:
    """How one code point is drawn under its label: a combining mark as its spacing look-alike, a space as ␣."""
    if combining(code_point):
        return SPACING[code_point]
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
            glyphs.append(Chunk(content=glyph(code_point).center(CELL)))
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


LABEL = 15
"""The width of the column naming each layer."""
CODE_POINT = 8
"""The width of each code point's column."""


def layers() -> Div:
    """
    "café" spelled with a combining accent, one layer per row: the graphemes a reader sees, the code points a `str`
    holds, then the bytes UTF-8 stores them as; and last, what a font does with a grapheme.
    """
    graphemes = [str(g) for g in iter_graphemes(CAFE)]
    seen: list[Chunk] = []
    brackets: list[Chunk] = []
    for grapheme in graphemes:
        width = len(grapheme) * CODE_POINT
        seen.append(Chunk(content=PRECOMPOSED.get(grapheme, grapheme).center(width - 2) + "  ", style=HIGHLIGHT))
        brackets.append(Chunk(content="└" + "─" * (width - 4) + "┘  ", style=EDGE))
    points = "".join(f"U+{ord(c):04X}".ljust(CODE_POINT) for c in CAFE)
    names = "".join(glyph(c).center(6).ljust(CODE_POINT) for c in CAFE)
    encoded = "".join(c.encode().hex(" ").upper().center(6).ljust(CODE_POINT) for c in CAFE)
    right = LABEL + len(CAFE) * CODE_POINT
    return area(
        86,
        11,
        ink("what you see", 0, 0, NOTE),
        ink(tuple(seen), LABEL, 0),
        ink(tuple(brackets), LABEL, 1),
        ink(f"{len(graphemes)} graphemes", right, 0, HIGHLIGHT),
        ink("what a reader counts", right, 1, EDGE),
        ink("code points", 0, 3, NOTE),
        ink(points, LABEL, 3),
        ink(names, LABEL, 4, EDGE),
        ink(f"{len(CAFE)} code points", right, 3, HIGHLIGHT),
        ink("what a str holds, len() counts", right, 4, EDGE),
        ink(f"the last is {name(CAFE[-1])}", LABEL, 5, EDGE),
        ink("UTF-8 bytes", 0, 7, NOTE),
        ink(encoded, LABEL, 7),
        ink(f"{len(CAFE.encode())} bytes", right, 7, HIGHLIGHT),
        ink("what a file or a socket holds", right, 8, EDGE),
        ink("a font draws each grapheme as one glyph, placing the accent over the e", 0, 10, NOTE),
    )
