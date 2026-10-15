"""
The run pane: a slide's runs side by side, each started by its number key, with its output in color.

Mounting starts nothing. A key press bumps the run's request count in state, and an effect keyed on that count
starts the program, so a thumbnail or the export, which never press the key, never spawn anything.
"""

from datetime import timedelta

from counterweight.commands import CommandOutputStyles
from counterweight.commands import command_output
from counterweight.commands import use_command
from counterweight.components import component
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.events import InputEvent
from counterweight.events import InputResponse
from counterweight.events import KeyPressed
from counterweight.events import Receiver
from counterweight.hooks import ElementHandle
from counterweight.hooks import use_effect
from counterweight.hooks import use_focus
from counterweight.hooks import use_rects
from counterweight.hooks import use_state
from counterweight.keys import Key
from counterweight.styles import CellStyle
from counterweight.styles import Style
from counterweight.styles.utilities import *
from counterweight.widgets import ScrollAreaStyles

from whats_new.components.look import PYTHON_BLUE
from whats_new.components.look import PYTHON_YELLOW
from whats_new.runs import Run
from whats_new.slides import SlideProps

RUN_TIMEOUT = timedelta(seconds=90)
NUMBER_KEYS = tuple(str(n) for n in range(1, 10))

OUTPUT_STYLES = CommandOutputStyles(
    area=ScrollAreaStyles(
        box=border | border_lightrounded | border_color("slate", 600),
        focused_box=border_color("slate", 400),
    ),
)


@component
def run_pane(props: SlideProps, style: Style = default, vertical: bool = False) -> Div:
    """
    The slide's runs side by side (or stacked, if `vertical`), the first started by `1`, the next by `2`, and so on;
    pressing a run's key again runs it again. Escape stops every run in progress.
    Only a live slide's pane takes focus, which is how its keys reach it.
    """
    runs = props.runs
    if len(runs) > len(NUMBER_KEYS):
        raise ValueError(f"a slide can bind at most {len(NUMBER_KEYS)} runs, not {len(runs)}")

    use_focus(auto_focus=props.is_live, is_focusable=props.is_live)
    requests, set_requests = use_state(tuple(0 for _ in runs))
    cancels, set_cancels = use_state(0)

    def on_input(event: InputEvent, receiver: Receiver) -> InputResponse:
        match event:
            case KeyPressed(key=key) if key in NUMBER_KEYS[: len(runs)]:
                index = NUMBER_KEYS.index(key)
                set_requests(lambda counts: tuple(c + (i == index) for i, c in enumerate(counts)))
                return ()
            case KeyPressed(key=Key.Escape):
                set_cancels(lambda n: n + 1)
                return ()
            case _:
                return None

    return Div(
        style=(col if vertical else row) | fill(1) | gap(1) | style,
        on_input=on_input,
        children=tuple(
            run_column(
                run=run,
                argv=props.host.interpreters.argv(run),
                number=index + 1,
                request=requests[index],
                cancels=cancels,
                is_live=props.is_live,
            ).with_key(str(index))
            for index, run in enumerate(runs)
        ),
    )


@component
def run_column(run: Run, argv: tuple[str, ...], number: int, request: int, cancels: int, is_live: bool) -> Div:
    viewport, _ = use_state(ElementHandle)
    command = use_command(columns=use_rects(viewport).content.width, env=run.env, timeout=RUN_TIMEOUT)

    async def start() -> None:
        if request > 0:
            command.run(argv)

    use_effect(start, deps=(request,))

    async def stop() -> None:
        if cancels > 0:
            command.cancel()

    use_effect(stop, deps=(cancels,))

    return Div(
        style=col | fill(1),
        children=(
            Text(
                content=(
                    Chunk(content=f" {number} ", style=CellStyle(foreground=PYTHON_YELLOW, bold=True)),
                    Chunk(content=run.label, style=CellStyle(foreground=PYTHON_BLUE, bold=True)),
                ),
                style=shrink(0),
            ),
            command_output(
                command.latest,
                viewport,
                style=fill(1),
                styles=OUTPUT_STYLES,
                is_focusable=is_live,
            ),
        ),
    )
