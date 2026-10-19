"""
Tachyon's diagrams: tracing vs sampling on one timeline, py-spy and austin vs Tachyon's architecture,
and the loop the Tachyon stage builds, the deck profiling itself.
"""

from datetime import timedelta

from counterweight.components import Component
from counterweight.components import component
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles import CellStyle

from whats_new.components.animation import use_explanation
from whats_new.diagrams.draw import CROSSED
from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import HIGHLIGHT_NODE
from whats_new.diagrams.draw import NOTE
from whats_new.diagrams.draw import area
from whats_new.diagrams.draw import centered_ink
from whats_new.diagrams.draw import centered_node
from whats_new.diagrams.draw import ink
from whats_new.diagrams.draw import node
from whats_new.diagrams.draw import node_width
from whats_new.tachyon import MODES
from whats_new.tachyon import profiler_argv

CALLS = "main ─ parse ─┬─ load ─┬─ read ── decode ─┬─ render ─┬─ write ──"
"""The program's calls, in order; each `┬` is where the call before it calls a helper, drawn on the line below."""
HELPERS = ("strip", "len", "get", "append")
"""The quick helper calls hanging off each `┬`, left to right: most calls in a real program are tiny ones like these."""


def helper_line() -> str:
    """The line under `CALLS`: each helper's name, hanging off its `┬`."""
    line = [" "] * len(CALLS)
    branches = [column for column, mark in enumerate(CALLS) if mark == "┬"]
    for column, name in zip(branches, HELPERS, strict=True):
        line[column : column + len(name) + 2] = f"└ {name}"
    return "".join(line)


def trace_line() -> str:
    """A tracing hook's `▲▼` (the call, then the return) at the start of every call, the helpers' included."""
    line = [" "] * len(CALLS)
    for column, mark in enumerate(CALLS):
        if mark == "┬" or (mark.isalpha() and (column == 0 or CALLS[column - 1] == " ")):
            line[column : column + 2] = "▲▼"
    return "".join(line)


CALLED = helper_line()
TRACE = trace_line()
SAMPLE = "    ●        ●        ●        ●        ●        ●        ●    "
"""A sample every 9 cells, on a clock rather than on calls, so it never lands on one of the quick helpers."""
SAMPLING_STEPS = 2
TIMELINE = timedelta(seconds=4)
TRACING_COST = "a hook on every call and return: exact, and it slows everything"
"""What tracing costs, which appears once the playhead reaches the end of the calls."""
AHEAD = EDGE | CellStyle(dim=True)
"""The calls the playhead hasn't reached yet."""


def tracing_vs_sampling(step: int, is_live: bool) -> Div | Component:
    """
    The two rows of one program's calls (with the quick helpers some of them call hanging beneath),
    the hooks each profiler fires along it, and what that costs.
    At step 1 a playhead runs along the calls, and each row fires as it passes: tracing at every call and return,
    sampling only at its ticks.
    """
    if step == 0:
        return timeline(0)
    return playing_timeline(is_live).with_key("playing")


def ends_showing(step: int) -> str | None:
    """What tracing costs, once the playhead has run the length of the calls at step 1."""
    return TRACING_COST if step == 1 else None


@component
def playing_timeline(is_live: bool) -> Div:
    return timeline(round(use_explanation(TIMELINE, is_live) * len(CALLS)))


def timeline(reached: int) -> Div:
    """The timeline with the playhead `reached` cells along the calls, every hook before it fired; 0 is before it starts."""

    def played(line: str, y: int) -> Text:
        """`line` (the calls, or the helpers under them) lit up to the playhead, and dim past it."""
        if not 0 < reached < len(CALLS):
            return ink(line, 12, y)
        return ink(
            (
                Chunk(content=line[:reached], style=EDGE),
                Chunk(content=line[reached], style=HIGHLIGHT),
                Chunk(content=line[reached + 1 :], style=AHEAD),
            ),
            12,
            y,
        )

    is_done = reached >= len(CALLS)
    return area(
        76,
        9,
        ink("tracing", 0, 0, HIGHLIGHT),
        ink(TRACE[:reached], 12, 0, CROSSED),
        played(CALLS, 1),
        played(CALLED, 2),
        *((ink(TRACING_COST, 12, 3, NOTE),) if is_done else ()),
        ink("sampling", 0, 5, HIGHLIGHT),
        ink(SAMPLE[:reached], 12, 5, HIGHLIGHT),
        played(CALLS, 6),
        played(CALLED, 7),
        *((ink("a snapshot of the stack now and then, from outside: cheap", 12, 8, NOTE),) if is_done else ()),
    )


def architectures() -> Div:
    return area(
        80,
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


SCREEN = "its screen comes back through the PTY, and the deck draws it in a pane"


def the_loop(pid: int) -> Div:
    """
    The deck above the profiler it spawns, with the two arrows between them: down, spawning it on a PTY,
    and up, the profiler attaching to its parent. Everything is centered on one column, in an area exactly as wide
    as its widest line, so the slide centers the whole drawing. The profiler's box holds the command the Tachyon
    stage runs, as the deck builds it, attaching to `pid`, the deck's own process.
    """
    profiler = " ".join(("python", *profiler_argv(pid, MODES[0])[1:]))
    width = max(len(SCREEN), node_width(profiler))
    middle = width // 2
    down, up = middle - 3, middle + 3
    return area(
        width,
        13,
        centered_node(f"the deck, pid {pid}", middle, 0, style=HIGHLIGHT_NODE),
        ink("│\n│\n▼", down, 3),
        ink("▲\n│\n│", up, 3),
        ink("spawns it, on a PTY", down - 2 - len("spawns it, on a PTY"), 4, NOTE),
        ink("attaches to its parent", up + 3, 4, NOTE),
        centered_node(profiler, middle, 6),
        centered_ink(SCREEN, middle, 10, NOTE),
        centered_ink(
            (
                Chunk(content="and drawing that pane is work the deck does, so it's ", style=NOTE),
                Chunk(content="in the profile", style=HIGHLIGHT),
            ),
            middle,
            12,
        ),
    )
