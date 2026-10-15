"""
The root component: which slide is showing, its reveal step, the grid, and the keys that move between them.

The deck's state is the current index, the step, and `selected`, which is `None` while a slide shows,
so "the grid is open" and "what it has selected" can't disagree.
"""

from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import replace
from datetime import tzinfo
from zoneinfo import ZoneInfo

from counterweight.components import Component
from counterweight.components import component
from counterweight.elements import AnyElement
from counterweight.elements import Div
from counterweight.events import InputEvent
from counterweight.events import InputResponse
from counterweight.events import KeyPressed
from counterweight.events import Receiver
from counterweight.hooks import use_effect
from counterweight.hooks import use_rects
from counterweight.hooks import use_state
from counterweight.keys import Key
from counterweight.styles.utilities import *

from whats_new.components.frame import footer
from whats_new.components.frame import heading
from whats_new.components.grid import COLUMNS
from whats_new.components.grid import grid
from whats_new.components.slide_body import slide_body
from whats_new.host import Host
from whats_new.slides import Slide


@dataclass(frozen=True, slots=True)
class Position:
    """Where the presenter is in the deck."""

    index: int
    step: int = 0
    generation: int = 0
    """Bumped by `r`, which remounts the slide, so its runs and reveals start fresh."""
    selected: int | None = None
    """The grid's selection, or `None` while the slide shows."""


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


def navigate(position: Position, key: str, slides: tuple[Slide, ...]) -> Position | None:
    """
    Where `key` moves the presenter from `position`, or `None` if the deck doesn't use that key there.
    This is the whole of the deck's navigation, as a pure function of the position and the key.
    """
    last = len(slides) - 1
    match position.selected, key:
        case None, Key.Right:
            return Position(index=min(position.index + 1, last))
        case None, Key.Left:
            return Position(index=max(position.index - 1, 0))
        case None, Key.Space:
            return replace(position, step=min(position.step + 1, slides[position.index].steps - 1))
        case None, "r":
            return replace(position, step=0, generation=position.generation + 1)
        case None, "d":
            return replace(position, selected=position.index)
        case int(selected), Key.Right:
            return replace(position, selected=clamp(selected + 1, 0, last))
        case int(selected), Key.Left:
            return replace(position, selected=clamp(selected - 1, 0, last))
        case int(selected), Key.Down:
            return replace(position, selected=clamp(selected + COLUMNS, 0, last))
        case int(selected), Key.Up:
            return replace(position, selected=clamp(selected - COLUMNS, 0, last))
        case int(selected), Key.Enter:
            return Position(index=selected)
        case int(), Key.Escape | "d":
            return replace(position, selected=None)
        case _:
            return None


CHICAGO = ZoneInfo("America/Chicago")
"""Where the talk is given, so the clock reads the room's time, not the VM's UTC."""


@component
def root(
    slides: tuple[Slide, ...],
    host: Host,
    start_index: int,
    remember_index: Callable[[int], None],
    timezone: tzinfo = CHICAGO,
) -> Div:
    """
    The deck. It starts on `start_index` and calls `remember_index` with the index after every move,
    so a restart (live reload, or a crash on stage) can come back to the same slide.
    The footer's clock reads the time in `timezone`.
    """
    position, set_position = use_state(Position(index=clamp(start_index, 0, len(slides) - 1)))
    show_clock, set_show_clock = use_state(False)
    show_size, set_show_size = use_state(False)
    screen = use_rects().border

    async def remember() -> None:
        remember_index(position.index)

    use_effect(remember, deps=(position.index,))

    def jump(index: int) -> None:
        set_position(Position(index=index))

    def on_input(event: InputEvent, receiver: Receiver) -> InputResponse:
        if not isinstance(event, KeyPressed):
            return None
        match event.key:
            case Key.F1:
                set_show_clock(lambda shown: not shown)
                return ()
            case Key.F2:
                set_show_size(lambda shown: not shown)
                return ()
        moved = navigate(position, event.key, slides)
        if moved is None:
            return None
        set_position(moved)
        return ()

    slide = slides[position.index]
    if position.selected is None:
        body: tuple[Component | AnyElement, ...] = (
            *((heading(slide.title, slide.peps),) if slide.has_heading else ()),
            Div(
                style=col | fill(1) | pad_x(1),
                # Keyed by index and generation: navigating away and back, or pressing r, mounts the slide fresh.
                children=(
                    slide_body(slide, position.step, True, host).with_key(
                        f"slide-{position.index}-{position.generation}"
                    ),
                ),
            ),
        )
    else:
        body = (grid(slides, position.selected, jump, host).with_key("grid"),)

    return Div(
        style=col | full,
        on_input=on_input,
        children=(
            *body,
            footer(position.index, len(slides), show_clock, show_size, screen.width, screen.height, timezone),
        ),
    )
