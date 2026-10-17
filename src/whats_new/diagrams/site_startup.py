"""
What `site.py` does with startup files at interpreter start, and when `.pth` import lines go away (PEP 829).
"""

from counterweight.elements import Chunk
from counterweight.elements import Div

from whats_new.diagrams.draw import CROSSED
from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import HIGHLIGHT_NODE
from whats_new.diagrams.draw import NOTE
from whats_new.diagrams.draw import area
from whats_new.diagrams.draw import ink
from whats_new.diagrams.draw import node


def site_startup() -> Div:
    return area(
        73,
        14,
        node("greet.pth", 0, 0),
        ink("─┬─ path lines ───────▶ sys.path", 13, 1),
        ink(" └─ import lines ─────▶ exec(), every start, used or not", 13, 2),
        node("greet.start", 0, 4, style=HIGHLIGHT_NODE),
        ink("─┬─ greet:hello ──────▶ resolve_name() ──▶ hello()", 15, 5),
        ink(" └─ same basename ────▶ ", 15, 6),
        ink("✗ greet.pth's import lines", 39, 6, CROSSED),
        ink(
            (
                Chunk(content="startup code becomes an ", style=NOTE),
                Chunk(content="entry point you can inspect", style=HIGHLIGHT),
                Chunk(content=", not a line of exec()", style=NOTE),
            ),
            0,
            9,
        ),
        ink("3.15 ── 3.17 ─────────── 3.18 ── 3.19 ─────────── 3.20 ──▶", 0, 11, EDGE),
        ink("import lines run         silently ignored         warning", 0, 12, NOTE),
        ink("(unless a .start)", 0, 13, EDGE),
    )
