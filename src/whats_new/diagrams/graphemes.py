"""The family emoji's seven code points, four people joined by three zero-width joiners, under one grapheme."""

from counterweight.elements import Chunk
from counterweight.elements import Text
from counterweight.styles import CellStyle
from counterweight.styles.utilities import *

from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import NOTE

PEOPLE = ("👨", "👩", "👧", "👦")
CELL = 8


def family_code_points() -> Text:
    columns = len(PEOPLE) * 2 - 1
    width = columns * CELL
    label = " 1 grapheme "
    bar = "┌" + label.center(width - 2, "─") + "┐"
    points: list[Chunk] = []
    glyphs: list[Chunk] = []
    for index, person in enumerate(PEOPLE):
        if index:
            points.append(Chunk(content="U+200D".center(CELL), style=EDGE))
            glyphs.append(Chunk(content="ZWJ".center(CELL), style=EDGE))
        points.append(Chunk(content=f"U+{ord(person):X}".center(CELL), style=NOTE))
        # An emoji is two cells wide, so it centers in two fewer.
        glyphs.append(Chunk(content=person.center(CELL - 1)))
    return Text(
        content=(
            Chunk(content=bar, style=HIGHLIGHT),
            Chunk.newline(),
            *points,
            Chunk.newline(),
            *glyphs,
            Chunk.newline(),
            Chunk(content=f"{columns} code points", style=CellStyle(dim=True)),
        ),
        style=text_wrap_none | shrink(0),
    )
