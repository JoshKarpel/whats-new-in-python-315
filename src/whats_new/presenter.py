"""
The root component: which slide is showing, its reveal step, the grid, and the keys that move between them.

The deck's state is the current index, the step, and `selected`, which is `None` while a slide shows,
so "the grid is open" and "what it has selected" can't disagree.
"""

from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
from dataclasses import replace
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
from whats_new.components.code import CODE_THEMES
from whats_new.components.easing import EASINGS
from whats_new.components.frame import footer
from whats_new.components.frame import heading
from whats_new.components.grid import above
from whats_new.components.grid import below
from whats_new.components.grid import grid
from whats_new.components.picker import Choice
from whats_new.components.picker import picker
from whats_new.components.slide_body import slide_body
from whats_new.components.swipe import TRANSITIONS
from whats_new.components.swipe import Direction
from whats_new.components.swipe import Swipe
from whats_new.components.swipe import stage
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


def swipe_direction(before: Position, after: Position) -> Direction | None:
    """
    Which way a move from `before` to `after` swipes, or `None` if it doesn't: only moving from one slide
    straight to another swipes, as in spiel, not opening, leaving or jumping from the grid, or `r`.
    """
    if before.selected is not None or after.selected is not None or after.index == before.index:
        return None
    return Direction.NEXT if after.index > before.index else Direction.PREVIOUS


@dataclass(frozen=True, slots=True, eq=False)
class Mounting:
    """
    One mounting of the live slide: its key, and its own focus handle, since a swipe mounts two slides at once
    and two mounted components can't share a handle. Every move to another slide, or `r`, makes a new one.
    """

    serial: int
    focus: FocusHandle = field(default_factory=FocusHandle)

    @property
    def key(self) -> str:
        return f"slide-{self.serial}"


THEME = Choice(label="code theme", options=CODE_THEMES, key="F4")
TRANSITION = Choice(label="slide transition", options=TRANSITIONS, key="F3")

CHICAGO = ZoneInfo("America/Chicago")
"""Where the talk is given, so the clock reads the room's time, not the VM's UTC."""


@component
def slide_view(slide: Slide, step: int, is_live: bool, host: Host, code_theme: str, focus: FocusHandle) -> Div:
    """`slide` at `step` with its heading, as the stage shows it, where a swipe moves the two together."""
    return Div(
        style=col | fill(1),
        children=(
            *((heading(slide.title, slide.peps),) if slide.title_card is None else ()),
            Div(
                style=col | fill(1) | pad_x(1),
                children=(slide_body(slide, step, is_live, host, code_theme, focus),),
            ),
        ),
    )


@component
def root(
    slides: tuple[Slide, ...],
    host: Host,
    start: Checkpoint,
    remember: Callable[[Checkpoint], None],
    timezone: tzinfo = CHICAGO,
) -> Div:
    """
    The deck. It starts from `start` and calls `remember` with a new checkpoint whenever the slide, the code theme,
    or the transition changes, so a restart (live reload, or a crash on stage) comes back to the same slide,
    looking the same. The footer's clock reads the time in `timezone`.
    F3 opens the slide transition picker and F4 the code theme picker (see `picker`); the same key closes it unchanged.
    """
    position, set_position = use_state(Position(index=clamp(start.slide, 0, len(slides) - 1)))
    # The live slide's, owned here rather than by the slide, so closing a picker can give focus back to it.
    mounting, set_mounting = use_state(Mounting(serial=0))
    no_swipe: Swipe | None = None
    swipe, set_swipe = use_state(no_swipe)
    show_clock, set_show_clock = use_state(False)
    show_size, set_show_size = use_state(False)
    code_theme, set_code_theme = use_state(start.code_theme)
    transition, set_transition = use_state(start.transition)
    no_picker: Choice | None = None
    picking, set_picking = use_state(no_picker)
    picker_focus, _ = use_state(FocusHandle)
    screen = use_rects().border

    async def checkpoint() -> None:
        remember(Checkpoint(slide=position.index, code_theme=code_theme, transition=transition))

    use_effect(checkpoint, deps=(position.index, code_theme, transition))

    def view(at: Position, of: Mounting, is_live: bool) -> Component:
        return slide_view(slides[at.index], at.step, is_live, host, code_theme, of.focus).with_key(of.key)

    def go(moved: Position) -> None:
        """Moves to `moved`, mounting the slide there afresh if it's another slide (or `r`), swiping if it should."""
        set_position(moved)
        if moved.selected is not None:
            # The grid replaces the stage, which would replay a swipe left here when it came back.
            set_swipe(None)
        if (moved.index, moved.generation) == (position.index, position.generation):
            return
        set_mounting(Mounting(serial=mounting.serial + 1))
        direction = swipe_direction(position, moved)
        easing = EASINGS.get(transition)
        if direction is None or easing is None:
            set_swipe(None)
            return
        set_swipe(Swipe(leaving=view(position, mounting, is_live=False), direction=direction, easing=easing))

    def jump(index: int) -> None:
        go(Position(index=index))

    def toggle(choice: Choice) -> InputResponse:
        if picking is choice:
            set_picking(None)
            return (FocusOn(mounting.focus),)
        set_picking(choice)
        return (FocusOn(picker_focus),)

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
                return toggle(TRANSITION)
            case Key.F4:
                return toggle(THEME)
            case _:
                pass
        moved = navigate(position, event.key, slides)
        if moved is None:
            return None
        go(moved)
        return ()

    if position.selected is None:
        body: tuple[Component | AnyElement, ...] = (
            stage(view(position, mounting, is_live=True), swipe).with_key("stage"),
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
            ),
            # Last, so it paints over the slide.
            *(
                (
                    picker(
                        picking,
                        transition if picking is TRANSITION else code_theme,
                        set_transition if picking is TRANSITION else set_code_theme,
                        lambda: set_picking(None),
                        FocusOn(mounting.focus),
                        picker_focus,
                    ).with_key(f"picker-{picking.key}"),
                )
                if picking is not None
                else ()
            ),
        ),
    )
