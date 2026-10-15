"""
The Tachyon stage: the deck runs Tachyon's live TUI inside itself, attached to its own process,
and makes itself do expensive things for it to watch.

It's one slide whose Space steps are its talking points, so the profiler pane survives the whole section.
Arriving starts nothing: `p` starts the profiler, and leaving the slide unmounts the pane, which hangs it up.
The profiler is the deck's child, attaching to its parent, which needs no ptrace permission beyond the default
on a machine without Yama (Yama's `ptrace_scope` 1 would refuse it).
"""

import asyncio
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta

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
from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.look import dim
from whats_new.components.run_pane import OUTPUT_STYLES
from whats_new.host import FlamegraphSite
from whats_new.runs import ROOT
from whats_new.slides import SlideProps
from whats_new.workloads import WORKLOADS
from whats_new.workloads import WORKLOADS_BY_KEY
from whats_new.workloads import Workload
from whats_new.workloads import perform

OUT = ROOT / "out"
FLAMEGRAPH = "deck-flamegraph.html"
FLAMEGRAPH_SECONDS = 10

MODES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("wall", ("--mode", "wall")),
    ("cpu", ("--mode", "cpu")),
    ("gil", ("--mode", "gil")),
    ("exception", ("--mode", "exception")),
    ("async-aware", ("--async-aware",)),
)

POINTS = (
    "p attaches Tachyon to this deck: the profiler is the deck's child, attached to its parent",
    "c: pure-Python CPU in a worker thread: the hot function, and the lines in it",
    "C: the same on the event loop: the deck freezes, and the profile explains it afterwards",
    "n: numpy: compiled code shows up as <native> frames",
    "i: blocking I/O: m to cpu mode, and the idle time vanishes",
    "a: asyncio tasks: m to async-aware mode, and the task tree comes back",
    "g: garbage cycles: <GC> frames",
    "e: raise and catch in a thread: exception mode samples only it",
    "drawing the profiler's screen is work the deck does: is it in the profile?",
    "f hands Tachyon the keyboard (s sort, t mode, x trends, h help); Ctrl+B takes it back",
    "F: a flamegraph of the next 10 seconds; D: what is every thread doing, right now?",
)
STEPS = len(POINTS)


def profiler_argv(pid: int, mode: int) -> tuple[str, ...]:
    """Tachyon's live TUI attached to `pid`, sampling every thread, in the mode at index `mode` of `MODES`."""
    # sys.executable, since the profiler must be the same minor version as the process it attaches to.
    return (sys.executable, "-m", "profiling.sampling", "attach", "--live", "-a", *MODES[mode][1], str(pid))


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


@dataclass(frozen=True, slots=True, eq=False)
class Started:
    """A workload started by a key press, compared by identity, so pressing the key again starts another."""

    workload: Workload


@component
def tachyon_stage(props: SlideProps) -> Div:
    focus = use_focus(auto_focus=props.is_live, is_focusable=props.is_live)
    pane, _ = use_state(FocusHandle)
    viewport, _ = use_state(ElementHandle)
    is_profiling, set_profiling = use_state(False)
    mode, set_mode = use_state(0)
    no_workload: Started | None = None
    started, set_started = use_state(no_workload)
    running, set_running = use_state(frozenset[str]())
    is_serving, set_serving = use_state(False)
    executor: Ref[ThreadPoolExecutor] = use_ref(new_executor)
    one_shot = use_command(columns=use_rects(viewport).content.width, timeout=timedelta(seconds=30))
    pid = os.getpid()

    async def run_workload() -> None:
        if started is None:
            return
        name = started.workload.name
        set_running(lambda names: names | {name})
        try:
            await perform(started.workload, executor.current)
        finally:
            set_running(lambda names: names - {name})

    use_effect(run_workload, deps=(started,))

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

    def on_input(event: InputEvent, receiver: Receiver) -> InputResponse:
        if not isinstance(event, KeyPressed):
            return None
        match event.key:
            case "p":
                set_profiling(lambda profiling: not profiling)
            case "m":
                set_mode(lambda m: (m + 1) % len(MODES))
            case "f" if is_profiling:
                return (FocusOn(pane),)
            case "F":
                OUT.mkdir(exist_ok=True)
                set_serving(True)
                one_shot.run(flamegraph_argv(pid))
            case "D":
                one_shot.run(dump_argv(pid))
            case Key.Escape:
                one_shot.cancel()
            case key if key in WORKLOADS_BY_KEY:
                set_started(Started(WORKLOADS_BY_KEY[key]))
            case _:
                return None
        return ()

    def take_back(event: InputEvent, receiver: Receiver) -> InputResponse:
        match event:
            case KeyPressed(key=Key.ControlB):
                return (FocusOn(focus.handle),)
            case _:
                return None

    latest = one_shot.latest
    flamegraph_ready = latest is not None and latest.argv == flamegraph_argv(pid) and latest.outcome == Exited(status=0)
    body: list[Component | AnyElement] = [
        strip(props.step, MODES[mode][0], tuple(sorted(running)), is_profiling),
    ]
    if is_profiling:
        body.append(
            terminal(
                profiler_argv(pid, mode),
                style=fill(3) | min_height(12),
                intercept=take_back,
                handle=pane,
                in_focus_order=False,
            ).with_key(f"profiler-{mode}")
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
    return Div(style=col | fill(1), on_input=on_input, children=tuple(body))


def strip(step: int, mode: str, running: tuple[str, ...], is_profiling: bool) -> Text:
    keys = " ".join(workload.key for workload in WORKLOADS)
    status = ", ".join(running) if running else "idle"
    return Text(
        content=(
            Chunk(content=POINTS[step], style=CellStyle(foreground=PYTHON_YELLOW, bold=True)),
            Chunk.newline(),
            Chunk(content=f"mode {mode}", style=CellStyle(foreground=PYTHON_BLUE)),
            Chunk(content=f" · {'profiling' if is_profiling else 'p to profile'} · running: {status}"),
            Chunk(content=f" · workloads {keys} · m mode · f focus", style=CellStyle(dim=True)),
        ),
        style=shrink(0),
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
