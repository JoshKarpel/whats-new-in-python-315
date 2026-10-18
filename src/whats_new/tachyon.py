"""
The Tachyon stage: the deck runs Tachyon's live TUI inside itself, attached to its own process,
and makes itself do expensive things for it to watch.

It's one slide, so the profiler pane survives the whole section, with a line over the pane saying
the profiler's mode and what's running.
Arriving starts nothing: `p` starts the profiler, and leaving the slide unmounts the pane, which hangs it up.
The profiler is the deck's child, attaching to its parent, which needs no ptrace permission beyond the default
on a machine without Yama (Yama's `ptrace_scope` 1 would refuse it).
"""

import asyncio
import subprocess
import sys
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from pathlib import Path

from counterweight.autopilot import AutopilotStep
from counterweight.autopilot import Wait
from counterweight.commands import Exited
from counterweight.commands import command_output
from counterweight.commands import use_command
from counterweight.components import Component
from counterweight.components import component
from counterweight.controls import FocusOn
from counterweight.elements import AnyElement
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.events import InputEvent
from counterweight.events import InputResponse
from counterweight.events import KeyPressed
from counterweight.events import Receiver
from counterweight.focus import FocusHandle
from counterweight.hooks import ElementHandle
from counterweight.hooks import Ref
from counterweight.hooks import use_effect
from counterweight.hooks import use_focus
from counterweight.hooks import use_rects
from counterweight.hooks import use_ref
from counterweight.hooks import use_state
from counterweight.keys import Key
from counterweight.styles import CellStyle
from counterweight.styles.utilities import *
from counterweight.widgets import terminal

from whats_new.components.look import PYTHON_BLUE
from whats_new.components.look import dim
from whats_new.components.picker import Choice
from whats_new.components.picker import Option
from whats_new.components.picker import PickerHandles
from whats_new.components.picker import picker
from whats_new.components.run_pane import OUTPUT_STYLES
from whats_new.host import FlamegraphSite
from whats_new.runs import ROOT
from whats_new.slides import SlideProps
from whats_new.tours import showing
from whats_new.workloads import WORKLOADS
from whats_new.workloads import WORKLOADS_BY_NAME
from whats_new.workloads import Workload
from whats_new.workloads import perform

OUT = ROOT / "out"
FLAMEGRAPH = "deck-flamegraph.html"
FLAMEGRAPH_SECONDS = 10


@dataclass(frozen=True, slots=True)
class Mode:
    """A way to run Tachyon's live view: `options` are what it's given, and `description` is what the picker says."""

    name: str
    options: tuple[str, ...]
    description: str


# Tachyon refuses `-a` (every thread) with `--async-aware`, which reconstructs stacks from the tasks instead;
# the deck's tasks all run on its own loop, so that mode loses nothing by dropping it.
MODES = (
    Mode("wall", ("-a", "--mode", "wall"), "every sample, running or waiting"),
    Mode("cpu", ("-a", "--mode", "cpu"), "only samples on the CPU: waiting drops out"),
    Mode("gil", ("-a", "--mode", "gil"), "only samples holding the GIL"),
    Mode("exception", ("-a", "--mode", "exception"), "only samples handling an exception"),
    Mode("async-aware", ("--async-aware",), "stacks rebuilt from asyncio tasks, not threads"),
)
MODES_BY_NAME = {mode.name: mode for mode in MODES}

MODE_CHOICE = Choice(
    label="profiler mode", options=tuple(Option(mode.name, mode.description) for mode in MODES), key="m"
)
NO_WORKLOAD = "none"
WORKLOAD_CHOICE = Choice(
    label="workload",
    options=(
        Option(NO_WORKLOAD, "stop the workload: the deck alone"),
        *(Option(workload.name, workload.description) for workload in WORKLOADS),
    ),
    key="w",
)


PROFILER_ENV = frozendict(PYTHONPATH=str(Path(__file__).parent / "tachyon_site"))
"""What the profiler runs with: its `sitecustomize` draws Tachyon's medals as `#1` and so on (see its docstring)."""


def profiler_argv(pid: int, mode: Mode) -> tuple[str, ...]:
    """Tachyon's live TUI attached to `pid`, in `mode`."""
    # sys.executable, since the profiler must be the same minor version as the process it attaches to.
    return (sys.executable, "-m", "profiling.sampling", "attach", "--live", *mode.options, str(pid))


def flamegraph_argv(pid: int) -> tuple[str, ...]:
    return (
        sys.executable,
        "-m",
        "profiling.sampling",
        "attach",
        "-a",
        "-d",
        str(FLAMEGRAPH_SECONDS),
        "--flamegraph",
        "-o",
        str(OUT / FLAMEGRAPH),
        str(pid),
    )


def dump_argv(pid: int) -> tuple[str, ...]:
    return (sys.executable, "-m", "profiling.sampling", "dump", str(pid))


def new_executor() -> ThreadPoolExecutor:
    """The threads workloads run in, named so Tachyon's thread list says which threads they are."""
    return ThreadPoolExecutor(max_workers=4, thread_name_prefix="workload")


@component
def tachyon_stage(props: SlideProps) -> Div:
    focus = use_focus(auto_focus=props.is_live, handle=props.slide_focus, is_focusable=props.is_live)
    pane, _ = use_state(FocusHandle)
    viewport, _ = use_state(ElementHandle)
    is_profiling, set_profiling = use_state(False)
    mode, set_mode = use_state(MODES[0])
    no_picker: Choice | None = None
    picking, set_picking = use_state(no_picker)
    picker_handles, _ = use_state(PickerHandles.fresh)
    no_workload: Workload | None = None
    workload, set_workload = use_state(no_workload)
    is_serving, set_serving = use_state(False)
    executor: Ref[ThreadPoolExecutor] = use_ref(new_executor)
    one_shot = use_command(columns=use_rects(viewport).content.width, timeout=timedelta(seconds=30))
    pid = props.host.pid

    # Choosing another workload, or none, or leaving the slide, cancels this, which stops the one running.
    async def run_workload() -> None:
        if workload is not None:
            await perform(workload, executor.current)

    use_effect(run_workload, deps=(workload,))

    async def shut_down_executor() -> None:
        try:
            await asyncio.Event().wait()
        finally:
            executor.current.shutdown(wait=False, cancel_futures=True)

    use_effect(shut_down_executor, deps=())

    async def serve() -> None:
        if is_serving:
            await serve_flamegraphs(props.host.flamegraph)

    use_effect(serve, deps=(is_serving,))

    def choose(choice: Choice, name: str) -> None:
        if choice is MODE_CHOICE:
            set_mode(MODES_BY_NAME[name])
        else:
            set_workload(None if name == NO_WORKLOAD else WORKLOADS_BY_NAME[name])

    def on_input(event: InputEvent, receiver: Receiver) -> InputResponse:
        if not isinstance(event, KeyPressed):
            return None
        match event.key:
            case "p":
                set_profiling(lambda profiling: not profiling)
            case "m":
                set_picking(MODE_CHOICE)
                return picker_handles.opened()
            case "w":
                set_picking(WORKLOAD_CHOICE)
                return picker_handles.opened()
            # The pane's `take_back` claims Tab too, so Tab moves the keyboard in and out of the profiler.
            case Key.Tab if is_profiling:
                return (FocusOn(pane),)
            case "F":
                OUT.mkdir(exist_ok=True)
                set_serving(True)
                one_shot.run(flamegraph_argv(pid))
            case "D":
                one_shot.run(dump_argv(pid))
            case Key.Escape:
                one_shot.cancel()
            case "c":
                set_workload(None)
            case _:
                return None
        return ()

    # Safe to claim: Tachyon's TUI binds letters, arrows, /, + and -, but not Tab.
    def take_back(event: InputEvent, receiver: Receiver) -> InputResponse:
        match event:
            case KeyPressed(key=Key.Tab | Key.ControlB):
                return (FocusOn(focus.handle),)
            case _:
                return None

    latest = one_shot.latest
    flamegraph_ready = latest is not None and latest.argv == flamegraph_argv(pid) and latest.outcome == Exited(status=0)
    body: list[Component | AnyElement] = [
        strip(mode.name, None if workload is None else workload.name),
    ]
    if is_profiling:
        body.append(
            terminal(
                profiler_argv(pid, mode),
                env=PROFILER_ENV,
                style=fill(3) | min_height(12),
                intercept=take_back,
                handle=pane,
                in_focus_order=False,
            ).with_key(f"profiler-{mode.name}")
        )
    else:
        body.append(placeholder())
    if latest is not None:
        body.append(command_output(latest, viewport, style=fill(2), styles=OUTPUT_STYLES, is_focusable=False))
    if flamegraph_ready:
        url = props.host.flamegraph.url(FLAMEGRAPH)
        body.append(
            Text(
                content=(
                    Chunk(content="flamegraph: "),
                    Chunk(content=url, style=CellStyle(foreground=PYTHON_BLUE, underline=True, link=url)),
                ),
            )
        )
    if picking is not None:
        # Last, so it paints over the profiler.
        body.append(
            picker(
                picking,
                current_choice(picking, mode, workload),
                partial(choose, picking),
                lambda: set_picking(None),
                FocusOn(focus.handle),
                picker_handles,
            ).with_key(f"picker-{picking.key}")
        )
    return Div(style=col | fill(1) | position_relative, on_input=on_input, children=tuple(body))


def current_choice(choice: Choice, mode: Mode, workload: Workload | None) -> str:
    """What `choice`'s picker marks as current: the mode, or the workload running, or none."""
    if choice is MODE_CHOICE:
        return mode.name
    return NO_WORKLOAD if workload is None else workload.name


def strip(mode: str, running: str | None) -> Text:
    """The profiler's mode and what's running, on one line, centered over the pane."""
    value = CellStyle(foreground=PYTHON_BLUE)
    return Text(
        content=(
            Chunk(content="mode: "),
            Chunk(content=mode, style=value),
            Chunk(content=" · running: "),
            Chunk(content="idle" if running is None else running, style=value),
        ),
        style=shrink(0) | text_wrap_none | text_justify_center,
    )


def placeholder() -> Text:
    return Text(
        content="Tachyon's live view of this deck goes here: press p",
        style=dim
        | border
        | border_lightrounded
        | border_color("slate", 600)
        | fill(3)
        | center_children
        | text_justify_center,
    )


async def serve_flamegraphs(site: FlamegraphSite) -> None:
    """Serves `OUT` over HTTP until cancelled, which hangs the server up, so leaving the slide stops it."""
    server = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "http.server",
        "--bind",
        site.bind,
        str(site.port),
        "--directory",
        str(OUT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        await server.wait()
    finally:
        if server.returncode is None:
            server.terminate()
            await server.wait()


WORKLOAD = Wait(timedelta(seconds=7))
"""How long to watch each workload, in real time, before the next talking point."""
LOOK = Wait(timedelta(seconds=3))


def press(*keys: str) -> list[AutopilotStep]:
    return [KeyPressed(key=key) for key in keys]


def pick(choice: Choice, name: str) -> list[AutopilotStep]:
    """The option called `name`, picked by typing its name into `choice`'s picker, where it's the first match."""
    return [*press(choice.key), LOOK, *press(*name), KeyPressed(key=Key.Enter)]


def tachyon_tour(step: int) -> Iterable[AutopilotStep]:
    """
    The demo, done: attach, run each workload a while under the profiler, switching to the modes that show it best,
    clear the workload to watch the deck alone, hand Tachyon the keyboard to sort its table,
    and dump every thread while a workload is busy.
    The flamegraph (`F`) is left out: it serves a page the recording can't show.
    """
    if step != 0:
        return []
    return [
        # The profiler is the deck's child, attached to its parent.
        *press("p"),
        showing("Tachyon Profiler"),
        LOOK,
        # The hot function, and the lines in it.
        *pick(WORKLOAD_CHOICE, "pure-Python CPU, in a thread"),
        WORKLOAD,
        # The deck freezes, and the profile explains why. The autopilot freezes too,
        # and takes its turns between freezes.
        *pick(WORKLOAD_CHOICE, "pure-Python CPU, on the event loop"),
        WORKLOAD,
        LOOK,
        # Compiled code shows up as <native> frames.
        *pick(WORKLOAD_CHOICE, "numpy matmul"),
        WORKLOAD,
        # In cpu mode, the idle time vanishes.
        *pick(WORKLOAD_CHOICE, "blocking I/O"),
        LOOK,
        *pick(MODE_CHOICE, "cpu"),
        WORKLOAD,
        # In async-aware mode, the task tree comes back.
        *pick(MODE_CHOICE, "async-aware"),
        *pick(WORKLOAD_CHOICE, "asyncio tasks"),
        WORKLOAD,
        # <GC> frames.
        *pick(WORKLOAD_CHOICE, "garbage cycles"),
        WORKLOAD,
        # Exception mode samples only the thread raising.
        *pick(MODE_CHOICE, "exception"),
        *pick(WORKLOAD_CHOICE, "raise and catch"),
        WORKLOAD,
        # Drawing the profiler's screen is work the deck does, so it's in the profile too.
        *press("c"),
        LOOK,
        # Tab hands Tachyon the keyboard for its own keys, then takes it back.
        KeyPressed(key=Key.Tab),
        LOOK,
        *press("s"),
        LOOK,
        KeyPressed(key=Key.Tab),
        # What is every thread doing, right now?
        *pick(WORKLOAD_CHOICE, "pure-Python CPU, in a thread"),
        LOOK,
        *press("D"),
        showing("exited"),
        LOOK,
    ]
