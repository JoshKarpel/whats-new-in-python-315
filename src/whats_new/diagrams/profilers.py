"""
Tachyon's diagrams: tracing vs sampling on one timeline, py-spy and austin vs Tachyon's architecture,
and the loop the Tachyon stage builds, the deck profiling itself.
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

CALLS = "main ─ parse ─┬─ load ─┬─ read ── decode ─┬─ render ─┬─ write ──"
TRACE = "▲▼     ▲▼     ▲▼ ▲▼    ▲▼ ▲▼   ▲▼     ▲▼  ▲▼ ▲▼     ▲▼ ▲▼    ▲▼"
SAMPLE = "    ●        ●        ●        ●        ●        ●        ●    "


def tracing_vs_sampling() -> Div:
    return area(
        86,
        9,
        ink("tracing", 0, 0, HIGHLIGHT),
        ink(TRACE, 12, 0, CROSSED),
        ink(CALLS, 12, 1),
        ink("a hook on every call and return: exact, and it slows everything down", 12, 2, NOTE),
        ink("sampling", 0, 5, HIGHLIGHT),
        ink(SAMPLE, 12, 5, HIGHLIGHT),
        ink(CALLS, 12, 6),
        ink("a stack snapshot every so often, from outside: statistical, and cheap", 12, 7, NOTE),
    )


def architectures() -> Div:
    return area(
        86,
        14,
        ink("py-spy, austin", 0, 0, HIGHLIGHT),
        node("profiler", 0, 1),
        ink("── reads memory ──▶", 13, 2),
        node("CPython 3.x", 33, 1),
        ink("with struct layouts for each version, so every release needs a catch-up release", 0, 4, NOTE),
        ink("Tachyon", 0, 7, HIGHLIGHT),
        node("profiling.sampling", 0, 8, style=HIGHLIGHT_NODE),
        ink("── _remote_debugging ──▶", 23, 9),
        node("CPython 3.15", 48, 8),
        ink("ships with the interpreter, so it supports each release on day one", 0, 11, NOTE),
        ink("and must be the same minor version as its target", 0, 12, CROSSED),
    )


def the_loop() -> Div:
    return area(
        86,
        13,
        node("the deck (pid 1234)", 0, 0, style=HIGHLIGHT_NODE),
        ink("── spawns, on a PTY ──▶", 23, 1),
        node("Tachyon --live 1234", 47, 0),
        ink("│", 57, 3),
        ink("│ attaches to its parent (ptrace: fine without Yama)", 57, 4, NOTE),
        ink("◀──────────────────────────────────────────────────┘", 6, 5),
        ink("│", 6, 3),
        ink("│", 6, 4),
        ink("its screen comes back through the PTY; the deck emulates it and draws it in a pane", 0, 7, NOTE),
        ink(
            (
                Chunk(content="and drawing that pane is work the deck does, so it's ", style=NOTE),
                Chunk(content="in the profile it's drawing", style=HIGHLIGHT),
            ),
            0,
            9,
        ),
        ink("(maybe: check it live)", 0, 10, EDGE),
    )
