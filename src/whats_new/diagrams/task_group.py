"""
First mirror wins, as a task tree: three fetches start; then they race, slowed down enough to follow, `eu` finishes
first and its `tg.cancel()` stops the other two mid-flight; then the `async with` exits without raising.
"""

from datetime import timedelta

from counterweight.animation import between
from counterweight.components import Component
from counterweight.components import component
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles.utilities import default

from whats_new.components.animation import use_explanation
from whats_new.diagrams.draw import CROSSED
from whats_new.diagrams.draw import EDGE
from whats_new.diagrams.draw import HIGHLIGHT
from whats_new.diagrams.draw import HIGHLIGHT_NODE
from whats_new.diagrams.draw import NOTE
from whats_new.diagrams.draw import area
from whats_new.diagrams.draw import centered_ink
from whats_new.diagrams.draw import centered_node
from whats_new.diagrams.draw import fork
from whats_new.diagrams.draw import ink

STEPS = 3
MIRRORS = (("us", 0.3, 15), ("eu", 0.1, 37), ("ap", 0.5, 59))
"""Each mirror's name, how long its fetch takes in seconds, and the column its box is centered on."""
WINNER = "eu"
WIDTH = 74
"""Wide enough for the closing line, centered under the middle mirror."""
BAR = 16
RACE = timedelta(seconds=2)
"""How long the race takes on screen: the winner's 0.1 s, slowed down enough to follow."""
RACING = 0.8
"""The part of the race spent racing; the rest holds the moment of cancellation before the marks appear."""
WON = "✓ tg.cancel()"
"""The winner's mark, which appears as the race ends."""


def task_group(step: int, is_live: bool) -> Div | Component:
    if step == 0:
        return tree(step, finished=None)
    return race(step, is_live).with_key("race")


def ends_showing(step: int) -> str | None:
    """The race plays at step 1, and carries on, already over, into step 2."""
    return WON if step == 1 else None


@component
def race(step: int, is_live: bool) -> Div:
    progress = use_explanation(RACE, is_live)
    seconds = between(progress, 0, RACING) * min(delay for _, delay, _ in MIRRORS)
    return tree(step, finished=seconds if progress < 1 else None, is_over=progress >= 1)


def tree(step: int, finished: float | None, is_over: bool = False) -> Div:
    """
    The tree at `step`, with each fetch's bar filled to how far it got in `finished` seconds of the race,
    or empty before the race (step 0), or where the race left it once it's over.
    """
    columns = tuple(column for _, _, column in MIRRORS)
    winner_delay = min(delay for _, delay, _ in MIRRORS)
    elapsed = 0.0 if step == 0 else winner_delay if finished is None else finished
    parts: list[Text | Div] = [
        centered_node("async with TaskGroup() as tg", columns[1], 0),
        *fork(columns[1], columns, 3),
    ]
    for mirror, delay, column in MIRRORS:
        is_winner = mirror == WINNER
        filled = round(BAR * min(elapsed / delay, 1.0))
        bar_style = HIGHLIGHT if is_winner else CROSSED if is_over else NOTE
        parts += [
            centered_node(f"fetch {mirror}", column, 5, style=HIGHLIGHT_NODE if is_winner and is_over else default),
            centered_ink(f"{delay} s", column, 8, EDGE),
            ink(
                (Chunk(content="█" * filled, style=bar_style), Chunk(content="░" * (BAR - filled), style=EDGE)),
                column - BAR // 2,
                9,
            ),
        ]
        if is_over and is_winner:
            parts.append(centered_ink(WON, column, 10, HIGHLIGHT))
        elif is_over:
            parts.append(centered_ink("✗ cancelled", column, 10, CROSSED))
    if step >= 2:
        parts.append(
            centered_ink(
                (
                    Chunk(content="the async with exits ", style=NOTE),
                    Chunk(content="without raising CancelledError", style=HIGHLIGHT),
                    Chunk(content=": ('eu', ...) in 0.1 s", style=NOTE),
                ),
                columns[1],
                12,
            )
        )
    return area(WIDTH, 13, *parts)
