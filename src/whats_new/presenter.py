"""
The root component: which slide is showing, its reveal step, the grid, and the keys that move between them.

The deck's state is the current index, the step, and `selected`, which is `None` while a slide shows,
so "the grid is open" and "what it has selected" can't disagree.
"""

from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import replace
from datetime import timedelta
from datetime import tzinfo
from zoneinfo import ZoneInfo

from counterweight.components import Component
from counterweight.components import component
from counterweight.controls import FocusOn
from counterweight.elements import AnyElement
from counterweight.elements import Div
from counterweight.events import InputEvent
from counterweight.events import InputResponse
from counterweight.events import KeyPressed
from counterweight.events import Receiver
from counterweight.focus import FocusHandle
from counterweight.hooks import use_effect
from counterweight.hooks import use_rects
from counterweight.hooks import use_state
from counterweight.keys import Key
from counterweight.styles.utilities import *

from whats_new.checkpoint import Checkpoint
from whats_new.components.frame import footer
from whats_new.components.frame import heading
from whats_new.components.grid import above
from whats_new.components.grid import below
from whats_new.components.grid import grid
from whats_new.components.slide_body import slide_body
from whats_new.components.theme_picker import theme_picker
from whats_new.host import Host
from whats_new.slides import Slide
from whats_new.slides import next_section
from whats_new.slides import previous_section


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
        case None, Key.PageDown:
            return Position(index=next_section(position.index, slides))
        case None, Key.PageUp:
            return Position(index=previous_section(position.index, slides))
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
            return replace(position, selected=below(selected, slides))
        case int(selected), Key.Up:
            return replace(position, selected=above(selected, slides))
        case int(selected), Key.PageDown:
            return replace(position, selected=next_section(selected, slides))
        case int(selected), Key.PageUp:
            return replace(position, selected=previous_section(selected, slides))
        case int(selected), Key.Enter | "d":
            return Position(index=selected)
        case int(), Key.Escape:
            return replace(position, selected=None)
        case _:
            return None


def never_measured() -> timedelta | None:
    """The frame time where nothing measures it, as in the export and the tests."""
    return None


CHICAGO = ZoneInfo("America/Chicago")
"""Where the talk is given, so the clock reads the room's time, not the VM's UTC."""


@component
def root(
    slides: tuple[Slide, ...],
    host: Host,
    start: Checkpoint,
    remember: Callable[[Checkpoint], None],
    timezone: tzinfo = CHICAGO,
    last_frame: Callable[[], timedelta | None] = never_measured,
) -> Div:
    """
    The deck. It starts from `start` and calls `remember` with a new checkpoint whenever the slide or the code theme
    changes, so a restart (live reload, or a crash on stage) comes back to the same slide, in the same theme.
    The footer's clock reads the time in `timezone`, and its frame time (F3) is whatever `last_frame` reports.
    F4 opens the code theme picker (see `theme_picker`), and closes it unchanged.
    """
    position, set_position = use_state(Position(index=clamp(start.slide, 0, len(slides) - 1)))
    show_clock, set_show_clock = use_state(False)
    show_size, set_show_size = use_state(False)
    show_frame_time, set_show_frame_time = use_state(False)
    code_theme, set_code_theme = use_state(start.code_theme)
    is_picking_theme, set_picking_theme = use_state(False)
    # Owned here rather than by the slide, so closing the picker can give focus back to whatever takes the slide's keys.
    slide_focus, _ = use_state(FocusHandle)
    picker_focus, _ = use_state(FocusHandle)
    screen = use_rects().border

    async def checkpoint() -> None:
        remember(Checkpoint(slide=position.index, code_theme=code_theme))

    use_effect(checkpoint, deps=(position.index, code_theme))

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
            case Key.F3:
                set_show_frame_time(lambda shown: not shown)
                return ()
            case Key.F4:
                set_picking_theme(not is_picking_theme)
                return (FocusOn(slide_focus if is_picking_theme else picker_focus),)
            case _:
                pass
        moved = navigate(position, event.key, slides)
        if moved is None:
            return None
        set_position(moved)
        return ()

    slide = slides[position.index]
    if position.selected is None:
        body: tuple[Component | AnyElement, ...] = (
            *((heading(slide.title, slide.peps),) if slide.title_card is None else ()),
            Div(
                style=col | fill(1) | pad_x(1),
                # Keyed by index and generation: navigating away and back, or pressing r, mounts the slide fresh.
                children=(
                    slide_body(slide, position.step, True, host, code_theme, slide_focus).with_key(
                        f"slide-{position.index}-{position.generation}"
                    ),
                ),
            ),
        )
    else:
        body = (grid(slides, position.selected, jump, host, code_theme).with_key("grid"),)

    return Div(
        style=col | full | position_relative,
        on_input=on_input,
        children=(
            *body,
            footer(
                position.index,
                len(slides),
                show_clock,
                show_size,
                screen.width,
                screen.height,
                timezone,
                last_frame if show_frame_time else None,
            ),
            # Last, so it paints over the slide.
            *(
                (
                    theme_picker(
                        code_theme,
                        set_code_theme,
                        lambda: set_picking_theme(False),
                        FocusOn(slide_focus),
                        picker_focus,
                    ).with_key("theme-picker"),
                )
                if is_picking_theme
                else ()
            ),
        ),
    )
