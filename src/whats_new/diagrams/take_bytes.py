"""Memory after `bytes(buffer)` (two buffers) and after `buffer.take_bytes()` (one, handed over)."""

from counterweight.elements import Chunk
from counterweight.elements import Text
from counterweight.styles import CellStyle
from counterweight.styles.utilities import *

from whats_new.components.look import PYTHON_BLUE
from whats_new.diagrams.draw import CROSSED
from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT

BAR = 6
FULL = CellStyle(foreground=PYTHON_BLUE)


def buffer_line(name: str, is_full: bool, note: str = "") -> tuple[Chunk, ...]:
    return (
        Chunk(content=f"{name:>6} ─▶ ", style=EDGE),
        Chunk(content="█" * BAR if is_full else "▏" + " " * (BAR - 1), style=FULL),
        Chunk(content=" 50 MiB" if is_full else " empty", style=EDGE),
        Chunk(content=note, style=CROSSED),
        Chunk.newline(),
    )


def take_bytes_memory() -> Text:
    return Text(
        content=(
            Chunk(content="bytes(buffer)", style=HIGHLIGHT),
            Chunk.newline(),
            *buffer_line("buffer", True),
            *buffer_line("result", True, " a copy"),
            Chunk.newline(),
            Chunk(content="buffer.take_bytes()", style=HIGHLIGHT),
            Chunk.newline(),
            *buffer_line("buffer", False),
            *buffer_line("result", True)[:-1],
        ),
        style=text_wrap_none | shrink(0),
    )
