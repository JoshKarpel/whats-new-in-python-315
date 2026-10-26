"""
The root component: which slide is showing, its reveal step, the grid and the sections list, and the keys that move
between them.

The deck's state is the current index, the step, and `browsing`, which is `None` while a slide shows,
so "the grid is open" and "what it has selected" can't disagree, and neither can the grid and the list both be open.
"""

import random
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
from dataclasses import replace
from datetime import tzinfo
from typing import assert_never
from zoneinfo import ZoneInfo

from counterweight.components import Component
from counterweight.components import component
from counterweight.controls import AnyControl
from counterweight.controls import FocusOn
from counterweight.controls import Screenshot
from counterweight.elements import Div
from counterweight.events import InputEvent
from counterweight.events import InputResponse
from counterweight.events import KeyPressed
from counterweight.events import Receiver
from counterweight.focus import ElementHandle
from counterweight.focus import FocusHandle
from counterweight.hooks import use_effect
from counterweight.hooks import use_rects
from counterweight.hooks import use_state
from counterweight.keys import Key
from counterweight.paint import Frame
from counterweight.styles.utilities import *

from whats_new.checkpoint import Checkpoint
from whats_new.components.code import CODE_THEMES
from whats_new.components.crossing import Crossing
from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import Tiles
from whats_new.components.crossing import photograph
from whats_new.components.crossing import picture_of
from whats_new.components.frame import footer
from whats_new.components.frame import heading
from whats_new.components.grid import Toward
from whats_new.components.grid import Zoom
from whats_new.components.grid import above
from whats_new.components.grid import below
from whats_new.components.grid import grid
from whats_new.components.grid import tiles
from whats_new.components.picker import Choice
from whats_new.components.picker import Option
from whats_new.components.picker import Picking
from whats_new.components.picker import Section
from whats_new.components.picker import picker
from whats_new.components.section_list import section_list
from whats_new.components.slide_body import slide_body
from whats_new.components.stage import Playing
from whats_new.components.stage import cover
from whats_new.components.stage import stage
from whats_new.components.swipe import SWIPE
from whats_new.components.swipe import Direction
from whats_new.components.swipe import Swipe
from whats_new.components.transitions import AHEAD
from whats_new.components.transitions import DESCRIBED
from whats_new.components.transitions import GRID_GROUPS
from whats_new.components.transitions import GROUP_ABOUT
from whats_new.components.transitions import SPEEDS
from whats_new.components.transitions import Choose
from whats_new.components.transitions import ChooseGrid
from whats_new.components.transitions import Crossed
from whats_new.components.transitions import Swiped
from whats_new.components.transitions import Tiled
from whats_new.components.transitions import Zoomed
from whats_new.components.transitions import grid_transition_for
from whats_new.components.transitions import transition_for
from whats_new.host import Host
from whats_new.slides import Slide
from whats_new.slides import next_section
from whats_new.slides import previous_section
from whats_new.slides import section_of
from whats_new.slides import sections


@dataclass(frozen=True, slots=True)
class InGrid:
    """The slide grid is open, with the slide at `selected` selected."""

    selected: int


@dataclass(frozen=True, slots=True)
class InSectionList:
    """The sections list is open, with the section numbered `highlighted` (counting from 0) highlighted."""

    highlighted: int


@dataclass(frozen=True, slots=True)
class Position:
    """Where the presenter is in the deck."""

    index: int
    step: int = 0
    generation: int = 0
    """Bumped by `r`, which remounts the slide, so its runs and reveals start fresh."""
    browsing: InGrid | InSectionList | None = None
    """What shows in the slide's place, or `None` while the slide shows."""


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


def navigate(position: Position, key: str, slides: tuple[Slide, ...]) -> Position | None:
    """
    Where `key` moves the presenter from `position`, or `None` if the deck doesn't use that key there.
    This is the whole of the deck's navigation, as a pure function of the position and the key.
    """
    last = len(slides) - 1
    match position.browsing, key:
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
            return replace(position, browsing=InGrid(position.index))
        case None, Key.ControlD:
            return replace(position, browsing=InSectionList(section_of(position.index, slides)))
        case InGrid(selected), Key.Right:
            return replace(position, browsing=InGrid(clamp(selected + 1, 0, last)))
        case InGrid(selected), Key.Left:
            return replace(position, browsing=InGrid(clamp(selected - 1, 0, last)))
        case InGrid(selected), Key.Down:
            return replace(position, browsing=InGrid(below(selected, slides)))
        case InGrid(selected), Key.Up:
            return replace(position, browsing=InGrid(above(selected, slides)))
        case InGrid(selected), Key.PageDown:
            return replace(position, browsing=InGrid(next_section(selected, slides)))
        case InGrid(selected), Key.PageUp:
            return replace(position, browsing=InGrid(previous_section(selected, slides)))
        case InGrid(selected), Key.Enter | "d":
            return Position(index=selected)
        case InGrid(selected), Key.ControlD:
            return replace(position, browsing=InSectionList(section_of(selected, slides)))
        case InGrid(), Key.Escape:
            return replace(position, browsing=None)
        case InSectionList(highlighted), Key.Down:
            return replace(position, browsing=InSectionList(min(highlighted + 1, len(sections(slides)) - 1)))
        case InSectionList(highlighted), Key.Up:
            return replace(position, browsing=InSectionList(max(highlighted - 1, 0)))
        case InSectionList(highlighted), Key.Enter:
            return replace(position, browsing=InGrid(sections(slides)[highlighted].start))
        case InSectionList(), Key.Escape | Key.ControlD:
            return replace(position, browsing=None)
        case _:
            return None


def swipe_direction(before: Position, after: Position) -> Direction | None:
    """
    Which way a move from `before` to `after` swipes, or `None` if it doesn't: only moving from one slide
    straight to another swipes, as in spiel, not opening, leaving or jumping from the grid or the sections list, or `r`.
    """
    if before.browsing is not None or after.browsing is not None or after.index == before.index:
        return None
    return Direction.NEXT if after.index > before.index else Direction.PREVIOUS


def zoom_toward(before: Position, after: Position) -> Toward | None:
    """
    Which way a move from `before` to `after` zooms the grid, or `None` if it doesn't: opening the grid, from the slide
    or the sections list, zooms out to it, and leaving it for the slide, by a jump or Escape, zooms in to the slide.
    Opening or leaving the sections list otherwise cuts straight to it.
    """
    match before.browsing, after.browsing:
        case InGrid(), InGrid():
            return None
        case _, InGrid():
            return Toward.GRID
        case InGrid(), None:
            return Toward.SLIDE
        case _:
            return None


type GridMotion = Zoom | Crossing
"""The grid opening or closing: zooming, or a transition drawn from pictures over whichever of it or the slide is live."""


def grid_frames(transition: Tiled | Crossed, slide: Grid, opened: Grid, where: Tiles, toward: Toward) -> Frames:
    """
    The frames of the grid opening from `slide` to `opened`, the grid's picture with its thumbnails `where` they are,
    or of it closing back, `toward` one or the other: a grid effect's, played backwards closing, or an F6 effect's,
    played opening as moving on to the next slide, and closing as moving back.
    """
    match transition:
        case Tiled(effect=effect):
            opening = effect(slide, opened, where)
            return opening if toward is Toward.GRID else lambda t: opening(1 - t)
        case Crossed(effect=effect):
            if toward is Toward.GRID:
                return effect(slide, opened, Direction.NEXT)
            return effect(opened, slide, Direction.PREVIOUS)
        case _ as unreachable:
            assert_never(unreachable)


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


THEME = Choice.listing(label="code theme", options=tuple(Option(theme) for theme in CODE_THEMES), key="F4")
TRANSITION = Choice.listing(
    label="slide transition", options=tuple(Option(name, about) for name, about in DESCRIBED.items()), key="F6"
)
PACE = Choice.listing(label="transition speed", options=tuple(Option(name) for name in SPEEDS), key="F8")
GRID_TRANSITION = Choice(
    label="grid transition",
    sections=(
        Section(title=None, options=tuple(Option(name, about) for name, about in AHEAD.items())),
        *(
            Section(
                title=group.title,
                options=tuple(Option(name, transition.description) for name, transition in group.transitions.items()),
                about=GROUP_ABOUT,
            )
            for group in GRID_GROUPS
        ),
    ),
    key="F7",
)

CHICAGO = ZoneInfo("America/Chicago")
"""Where the talk is given, so the clock reads the room's time, not the VM's UTC."""


@component
def slide_view(slide: Slide, step: int, is_live: bool, host: Host, code_theme: str, focus: FocusHandle) -> Div:
    """`slide` at `step` with its heading, as the stage shows it, where a swipe moves the two together."""
    return Div(
        style=col | fill(1),
        children=(
            *((heading(slide.title, slide.peps),) if not slide.is_title_card else ()),
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
    choose: Choose = random.choice,
    choose_grid: ChooseGrid = random.choice,
) -> Div:
    """
    The deck. It starts from `start` and calls `remember` with a new checkpoint whenever the slide, the code theme,
    the transition, its speed, or the grid's transition changes, so a restart (live reload, or a crash on stage)
    comes back to the same slide, looking the same. The footer's clock reads the time in `timezone`, and `choose`
    picks each move's transition while F6 has `random` picked, and `choose_grid` the grid's while F7 has `random`
    or a group's bar picked.
    F4 opens the code theme picker, F6 the slide transition picker, F7 the grid transition picker,
    and F8 the speed picker (see `picker`); the same key closes it unchanged.
    Not F5, which the presenting browser keeps for itself.
    """
    position, set_position = use_state(Position(index=clamp(start.slide, 0, len(slides) - 1)))
    # The live slide's, owned here rather than by the slide, so closing a picker can give focus back to it.
    mounting, set_mounting = use_state(Mounting(serial=0))
    no_transition: Playing | None = None
    playing, set_playing = use_state(no_transition)
    no_motion: GridMotion | None = None
    motion, set_motion = use_state(no_motion)
    show_clock, set_show_clock = use_state(False)
    show_size, set_show_size = use_state(False)
    code_theme, set_code_theme = use_state(start.code_theme)
    transition, set_transition = use_state(start.transition)
    speed, set_speed = use_state(start.speed)
    grid_transition, set_grid_transition = use_state(start.grid_transition)
    no_picker: Picking | None = None
    picking, set_picking = use_state(no_picker)
    stage_handle, _ = use_state(ElementHandle)
    screen = use_rects().border
    stage_area = use_rects(stage_handle).content

    async def checkpoint() -> None:
        remember(
            Checkpoint(
                slide=position.index,
                code_theme=code_theme,
                transition=transition,
                speed=speed,
                grid_transition=grid_transition,
            )
        )

    use_effect(checkpoint, deps=(position.index, code_theme, transition, speed, grid_transition))

    def view(at: Position, of: Mounting, is_live: bool) -> Component:
        return slide_view(slides[at.index], at.step, is_live, host, code_theme, of.focus).with_key(of.key)

    def move_grid(toward: Toward, moved: Position, pace: float) -> tuple[AnyControl, ...]:
        """
        Opens the grid, or closes it to the slide `moved` is on, `toward` one or the other, playing F7's transition
        at `pace`. One drawn from pictures can't start until it has a picture of the screen, so this returns
        the screenshot that starts it.
        """
        set_motion(None)
        match transition_picked := grid_transition_for(grid_transition, choose_grid):
            case None:
                return ()
            case Zoomed():
                set_motion(Zoom(toward=toward, duration=SWIPE / pace))
                return ()
            case Tiled(duration=duration) | Crossed(duration=duration):
                area = stage_area
                # The grid as it opens, or as it would be closing to the slide, the same grid the zoom draws.
                selected = moved.browsing.selected if isinstance(moved.browsing, InGrid) else moved.index
                opened = grid(slides, selected, jump, host, code_theme, None)
                arriving = slide_view(slides[moved.index], moved.step, True, host, code_theme, FocusHandle())
                where = tiles(area.width, area.height, selected, slides)
                length = duration / pace

                async def cross(frame: Frame) -> None:
                    """Taken before the render that opens the grid or mounts the slide, so that render draws the first frame."""
                    # Whichever of the two mounts now is live beneath the canvas for `length`, so each is pictured
                    # as it will be when the canvas goes.
                    pictured = await photograph(opened, area.width, area.height, after=length)
                    slide = (
                        picture_of(frame.paint, area)
                        if toward is Toward.GRID
                        else await photograph(arriving, area.width, area.height, after=length)
                    )
                    frames = grid_frames(transition_picked, slide, pictured, where, toward)
                    set_motion(Crossing(frames=frames, duration=length))

                return (Screenshot(handler=cross),)
            case _ as unreachable:
                assert_never(unreachable)

    def go(moved: Position) -> tuple[AnyControl, ...]:
        """
        Moves to `moved`, mounting the slide there afresh if it's another slide (or `r`), and playing the transition
        into it or opening or closing the grid with its own if it should. Any other move ends the grid's still playing.
        A crossing can't start until it has a picture of the screen, so `go` returns the screenshot that starts it.
        """
        set_position(moved)
        pace = SPEEDS[speed]
        if moved.browsing is not None:
            # The grid or the list replaces the stage, which would replay a transition left here when it came back.
            set_playing(None)
        if (moved.index, moved.generation) != (position.index, position.generation):
            set_mounting(Mounting(serial=mounting.serial + 1))
            set_playing(None)
        toward = zoom_toward(position, moved)
        if toward is not None:
            return move_grid(toward, moved, pace)
        set_motion(None)
        direction = swipe_direction(position, moved)
        if direction is None:
            return ()
        match transition_for(transition, choose):
            case None:
                return ()
            case Swiped():
                leaving = view(position, mounting, is_live=False)
                set_playing(Swipe(leaving=leaving, direction=direction, duration=SWIPE / pace))
                return ()
            case Crossed(effect=effect, duration=duration):
                # As the live slide will draw once the canvas goes, though with a focus handle of its own.
                arriving = slide_view(slides[moved.index], moved.step, True, host, code_theme, FocusHandle())
                area = stage_area
                length = duration / pace

                async def cross(frame: Frame) -> None:
                    """Taken before the render that mounts the arriving slide, so that render draws the first frame."""
                    leaving = picture_of(frame.paint, area)
                    arrived = await photograph(arriving, area.width, area.height, after=length)
                    frames = effect(leaving, arrived, direction)
                    set_playing(Crossing(frames=frames, duration=length))

                return (Screenshot(handler=cross),)
            case _ as unreachable:
                assert_never(unreachable)

    def jump(index: int) -> InputResponse:
        return go(Position(index=index))

    def open_section(number: int) -> InputResponse:
        return go(replace(position, browsing=InGrid(sections(slides)[number].start)))

    def toggle(choice: Choice) -> InputResponse:
        if picking is not None and picking.choice is choice:
            set_picking(None)
            return (FocusOn(mounting.focus),)
        opening = Picking(choice)
        set_picking(opening)
        return opening.opened()

    def chosen(choice: Choice) -> tuple[str, Callable[[str], object]]:
        """What `choice`'s picker shows as chosen, and what choosing another calls."""
        if choice is TRANSITION:
            return transition, set_transition
        if choice is PACE:
            return speed, set_speed
        if choice is GRID_TRANSITION:
            return grid_transition, set_grid_transition
        return code_theme, set_code_theme

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
            case Key.F4:
                return toggle(THEME)
            case Key.F6:
                return toggle(TRANSITION)
            case Key.F7:
                return toggle(GRID_TRANSITION)
            case Key.F8:
                return toggle(PACE)
            case _:
                pass
        moved = navigate(position, event.key, slides)
        if moved is None:
            return None
        return go(moved)

    layers: list[Component] = []
    zoom = motion if isinstance(motion, Zoom) else None
    match position.browsing:
        case None:
            layers.append(stage(view(position, mounting, is_live=True), playing).with_key("stage"))
            # The grid stays over the stage while it zooms in to the slide it left for, already mounted beneath it.
            if zoom is not None:
                layers.append(grid(slides, position.index, jump, host, code_theme, zoom).with_key("grid"))
        case InGrid(selected):
            layers.append(grid(slides, selected, jump, host, code_theme, zoom).with_key("grid"))
        case InSectionList(highlighted):
            layers.append(section_list(slides, highlighted, open_section).with_key("sections"))
        case _ as unreachable:
            assert_never(unreachable)
    if isinstance(motion, Crossing):
        layers.append(cover(motion).with_key("cover"))

    return Div(
        style=col | full | position_relative,
        on_input=on_input,
        children=(
            Div(style=col | fill(1) | position_relative, children=tuple(layers), handle=stage_handle),
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
                        picking.choice,
                        *chosen(picking.choice),
                        lambda: set_picking(None),
                        FocusOn(mounting.focus),
                        picking.handles,
                    ).with_key(picking.key),
                )
                if picking is not None
                else ()
            ),
        ),
    )
