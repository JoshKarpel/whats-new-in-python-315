"""
First mirror wins, as a task tree revealed in steps: three fetches start, one finishes,
its `tg.cancel()` cancels the other two, and the `async with` exits without raising.
"""

from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles.utilities import default

from whats_new.diagrams.draw import CROSSED
from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import HIGHLIGHT_NODE
from whats_new.diagrams.draw import NOTE
from whats_new.diagrams.draw import area
from whats_new.diagrams.draw import ink
from whats_new.diagrams.draw import node

STEPS = 4
MIRRORS = (("us", "0.3 s", 6), ("eu", "0.1 s", 26), ("ap", "0.5 s", 46))


def task_group(step: int) -> Div:
    parts: list[Text | Div] = [
        node("async with TaskGroup() as tg", 19, 0),
        ink("┌───────────────────┼───────────────────┐", 11, 3),
        ink("│                   │                   │", 11, 4),
    ]
    for mirror, delay, x in MIRRORS:
        is_winner = mirror == "eu"
        parts.append(node(f"fetch {mirror}", x, 5, style=HIGHLIGHT_NODE if is_winner and step >= 1 else default))
        parts.append(ink(delay, x + 3, 8, EDGE))
    if step >= 1:
        parts.append(ink("✓ tg.cancel()", 26, 9, HIGHLIGHT))
    if step >= 2:
        parts += [ink("✗ cancelled", 5, 9, CROSSED), ink("✗ cancelled", 45, 9, CROSSED)]
    if step >= 3:
        parts.append(
            ink(
                (
                    Chunk(content="the async with exits ", style=NOTE),
                    Chunk(content="without raising CancelledError", style=HIGHLIGHT),
                    Chunk(content=": ('eu', ...) in 0.1 s", style=NOTE),
                ),
                5,
                11,
            )
        )
    return area(70, 12, *parts)
