"""
Diagrams for the performance section below Python: the frame pointer chain (and what one extension built
without it does to it) and the JIT's pipeline.

The chain animates: a reveal step remounts the animated part, which plays it once.
"""

from datetime import timedelta

from counterweight.components import Component
from counterweight.components import component
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles import CellStyle
from counterweight.styles.utilities import default

from whats_new.components.animation import use_explanation
from whats_new.diagrams.draw import CROSSED
from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import HIGHLIGHT_NODE
from whats_new.diagrams.draw import NOTE
from whats_new.diagrams.draw import area
from whats_new.diagrams.draw import ink
from whats_new.diagrams.draw import node

FRAME_POINTER_STEPS = 3
"""The chain; then a walk along it, as perf takes one; then the same walk with one extension built without them."""

# Newest first, as a profiler reads them: each frame's saved rbp names its caller's frame.
STACK = (
    ("fib", "py::"),
    ("callback", "py::"),
    ("call_many", "churn.so"),
    ("outer_python_frame", "py::"),
    ("main", "python"),
    ("_start", "libc"),
)
EXTENSION = 2
HOP = timedelta(milliseconds=600)
"""How long the walk takes to follow one saved rbp."""
WALKED = ": one load per frame, no DWARF tables"
"""The end of the caption once a walk reaches `_start`."""
LOST_CALLERS = "its callers vanish"
"""The end of the caption once a walk stops at the extension."""
LOST = CellStyle(foreground=EDGE.foreground, dim=True)
ARROW_X = 37


def frame_pointers_end_showing(step: int) -> str | None:
    """Each walk's caption, which changes as the walk ends; step 0 is the chain, still."""
    return (None, WALKED, LOST_CALLERS)[step]


def frame_pointer_chain(step: int, is_live: bool) -> Div | Component:
    """
    The stack as a linked list, each frame's saved rbp pointing at its caller's; then a cursor walking it, as perf
    does; then the walk again, through an extension built without frame pointers, whose rbp holds data, where it
    stops and everything after it is lost.
    """
    if step == 0:
        return chain(is_broken=False, reached=None)
    return walk(is_broken=step >= 2, is_live=is_live).with_key(f"walk-{step}")


@component
def walk(is_broken: bool, is_live: bool) -> Div:
    hops = EXTENSION + 1 if is_broken else len(STACK) - 1
    progress = use_explanation(HOP * hops, is_live)
    return chain(is_broken=is_broken, reached=int(progress * hops))


def chain(is_broken: bool, reached: int | None) -> Div:
    """
    The chain, with the walk's cursor on the frame at index `reached` (or none, before a walk), every saved rbp
    before it followed. Broken, the walk's last hop is the extension's rbp, which leads nowhere.
    """
    is_stopped = is_broken and reached == EXTENSION + 1
    cursor = None if reached is None else min(reached, EXTENSION) if is_broken else reached
    parts: list[Text | Div] = [ink("a sample's stack, newest first", 2, 0, NOTE)]
    for row, (frame, owner) in enumerate(STACK):
        y = 1 + row * 2
        is_lost = is_stopped and row > EXTENSION
        box = LOST if is_lost else HIGHLIGHT if row == cursor else NOTE
        if row == cursor:
            parts.append(ink("▶", 0, y, HIGHLIGHT))
        parts.append(ink(f"│ {frame:<20} {owner:>9} │", 2, y, box))
        if row == len(STACK) - 1:
            continue
        is_followed = reached is not None and row < reached
        if is_broken and row == EXTENSION and is_stopped:
            parts.append(ink("saved rbp ──▶ ✗ not a frame: the walk stops", ARROW_X, y, CROSSED))
        elif is_lost:
            parts.append(ink("unreachable", ARROW_X, y, LOST))
        else:
            parts.append(ink(f"saved rbp ──▶ {STACK[row + 1][0]}", ARROW_X, y, HIGHLIGHT if is_followed else EDGE))
    parts.append(ink(caption(is_broken, reached), 2, 13))
    return area(80, 14, *parts)


def caption(is_broken: bool, reached: int | None) -> tuple[Chunk, ...]:
    if is_broken and reached == EXTENSION + 1:
        return (
            Chunk(content="one extension without frame pointers, and ", style=NOTE),
            Chunk(content=LOST_CALLERS, style=CROSSED),
        )
    if not is_broken and reached == len(STACK) - 1:
        return (
            Chunk(content="every frame, back to ", style=NOTE),
            Chunk(content="_start", style=HIGHLIGHT),
            Chunk(content=WALKED, style=NOTE),
        )
    return (Chunk(content="perf and eBPF walk this list: cheap, and no DWARF tables needed", style=NOTE),)


def jit_pipeline() -> Div:
    stages = (
        ("bytecode", False),
        ("specialized", False),
        ("trace", True),
        ("micro-ops", True),
        ("machine code", False),
    )
    parts: list[Text | Div] = []
    x = 0
    for index, (name, changed) in enumerate(stages):
        parts.append(node(name, x, 0, style=HIGHLIGHT_NODE if changed else default))
        x += len(name) + 4
        if index < len(stages) - 1:
            parts.append(ink("─▶", x, 1))
            x += 3
    parts += [
        ink("new in 3.15: a tracing frontend, register allocation,", 0, 4, HIGHLIGHT),
        ink("more constant propagation and refcount elimination", 0, 5, HIGHLIGHT),
        ink("and it tells GDB and backtrace() how to unwind through JIT frames", 0, 7, NOTE),
    ]
    return area(x, 8, *parts)
