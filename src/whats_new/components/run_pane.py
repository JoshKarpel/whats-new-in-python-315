"""
The run pane: one box at the slide's full width, showing whichever of the slide's runs was started last,
each started by its number key, with its output in color.

Mounting starts nothing. A key press records a new request in state, and an effect keyed on the request
starts the program, so a thumbnail or the export, which never press a key, never spawn anything.
"""

import asyncio
from dataclasses import dataclass
from datetime import timedelta

from counterweight.commands import CommandOutputStyles
from counterweight.commands import Running
from counterweight.commands import Starting
from counterweight.commands import outcome_text
from counterweight.commands import use_command
from counterweight.components import component
from counterweight.controls import ScrollBy
from counterweight.elements import Canvas
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.events import InputEvent
from counterweight.events import InputResponse
from counterweight.events import KeyPressed
from counterweight.events import Receiver
from counterweight.gradients import ConicGradient
from counterweight.gradients import conic_gradient
from counterweight.hooks import ElementHandle
from counterweight.hooks import use_effect
from counterweight.hooks import use_focus
from counterweight.hooks import use_rects
from counterweight.hooks import use_state
from counterweight.keys import Key
from counterweight.styles import Color
from counterweight.styles.utilities import *
from counterweight.widgets import ScrollAreaStyles
from counterweight.widgets import scroll_area

from whats_new.components.animation import use_loop
from whats_new.components.look import text_python_blue
from whats_new.components.look import text_python_yellow
from whats_new.runs import Run
from whats_new.runs import copy_examples
from whats_new.runs import rehomed
from whats_new.slides import SlideProps

RUN_TIMEOUT = timedelta(seconds=90)
NUMBER_KEYS = tuple(str(n) for n in range(1, 10))

ORBIT = timedelta(milliseconds=1500)
"""How long the light on the box's border takes to go once around it while a run is in progress."""
RESTING = Color.from_hex("#475569")
"""The box's border between runs: Tailwind's slate 600, as the other boxes on a slide."""
LIT = Color.from_hex("#93c5fd")
"""The head of the light that goes around the border while a run is in progress: Tailwind's blue 300."""

OUTPUT_STYLES = CommandOutputStyles(
    area=ScrollAreaStyles(
        box=border | border_lightrounded | border_color("slate", 600),
        focused_box=border_color("slate", 400),
    ),
)


@dataclass(frozen=True, slots=True)
class Request:
    """
    Which run to show, and the how-manyth press of any run's key asked for it,
    so pressing the same key again is a new request, which runs it again.
    """

    index: int
    press: int


@component
def run_pane(props: SlideProps) -> Div:
    """
    The slide's runs, named in a line above one box: `1` runs the first in the box, `2` the next, and so on,
    replacing whatever the box showed, and the line marks which one it shows, with how it's going at its right end.
    Pressing a run's key again runs it again. Escape stops the run in progress.
    While one is in progress, a light goes around the box's border, so a slow run doesn't look like a dead key.
    Up and Down scroll the output, so a long traceback can be read without reaching for the mouse.
    Every run executes a copy of `examples/` with the slide's edits written over it.
    Only a live slide's pane takes focus, which is how its keys reach it.
    """
    runs = props.runs
    if len(runs) > len(NUMBER_KEYS):
        raise ValueError(f"a slide can bind at most {len(NUMBER_KEYS)} runs, not {len(runs)}")

    # In the focus order, after the slide's editors, so Tab from the last editor comes back here.
    use_focus(auto_focus=props.is_live, handle=props.slide_focus, is_focusable=props.is_live)
    nothing_requested: Request | None = None
    request, set_request = use_state(nothing_requested)
    cancels, set_cancels = use_state(0)
    viewport, _ = use_state(ElementHandle)
    shown = None if request is None else runs[request.index]
    # The environment is read when the run starts, in the render that made the request, so it's the shown run's.
    command = use_command(
        columns=use_rects(viewport).content.width,
        env=frozendict() if shown is None else shown.env,
        timeout=RUN_TIMEOUT,
    )

    async def start() -> None:
        if shown is None:
            return
        examples_copy = props.host.examples_copy
        await asyncio.to_thread(copy_examples, examples_copy, props.edits)
        command.run(rehomed(props.host.interpreters.argv(shown), examples_copy))

    use_effect(start, deps=(request,))

    async def stop() -> None:
        if cancels > 0:
            command.cancel()

    use_effect(stop, deps=(cancels,))

    def on_input(event: InputEvent, receiver: Receiver) -> InputResponse:
        match event:
            case KeyPressed(key=key) if key in NUMBER_KEYS[: len(runs)]:
                index = NUMBER_KEYS.index(key)
                set_request(lambda current: Request(index=index, press=1 if current is None else current.press + 1))
                return ()
            case KeyPressed(key=Key.Escape):
                set_cancels(lambda n: n + 1)
                return ()
            case KeyPressed(key=Key.Up):
                return (ScrollBy(target=viewport, y=-1),)
            case KeyPressed(key=Key.Down):
                return (ScrollBy(target=viewport, y=1),)
            case _:
                return None

    latest = command.latest
    is_running = latest is not None and isinstance(latest.outcome, Starting | Running)
    phase = use_loop(ORBIT, is_running and props.is_live)
    return Div(
        # Across the slide, in a column that centers its other children.
        style=col | fill(1) | align_self_stretch,
        on_input=on_input,
        children=(
            # The outcome shares the line with the names, rather than taking a line under the box as
            # `command_output` does, so the box doesn't jump when the first run starts.
            Div(
                style=row | justify_children_space_between | shrink(0),
                children=(
                    Text(
                        content=tuple(
                            chunk
                            for index, run in enumerate(runs)
                            for chunk in run_name(index, run, is_shown=request is not None and request.index == index)
                        ),
                    ),
                    Text(
                        content="" if latest is None else outcome_text(latest.outcome) + " ",
                        style=default if latest is None else OUTPUT_STYLES.outcome_style(latest.outcome),
                    ),
                ),
            ),
            scroll_area(
                children=() if latest is None else (Canvas(painter=latest.output),),
                stick_to_end=True,
                style=fill(1),
                styles=ScrollAreaStyles(
                    box=OUTPUT_STYLES.area.box | (border_gradient(orbiting(phase)) if is_running else default),
                    focused_box=OUTPUT_STYLES.area.focused_box if not is_running else default,
                ),
                viewport=viewport,
                is_focusable=props.is_live,
                in_focus_order=False,
            ),
        ),
    )


def orbiting(phase: float) -> ConicGradient:
    """
    The border's colors `phase` of the way around while a run is in progress: a light going clockwise,
    brightening from its tail to its head, then gone, and the resting color the rest of the way round.
    """
    return conic_gradient((RESTING, 0), (LIT, 0.25), (RESTING, 0.3), start=360 * phase)


def run_name(index: int, run: Run, is_shown: bool) -> tuple[Chunk, ...]:
    """A run's key and label in the line above the box, bright for the run the box shows and dim for the rest."""
    intensity = text_bold | (text_not_dim if is_shown else text_dim)
    return (
        Chunk(content=f" {index + 1} ", style=intensity | text_python_yellow),
        Chunk(content=run.label, style=intensity | text_python_blue),
        Chunk(content="  "),
    )
