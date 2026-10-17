"""
The Tachyon stage: the deck runs Tachyon's live TUI inside itself, attached to its own process,
and makes itself do expensive things for it to watch.

It's one slide whose Space steps are its talking points, so the profiler pane survives the whole section.
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
from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.look import dim
from whats_new.components.run_pane import OUTPUT_STYLES
from whats_new.host import FlamegraphSite
from whats_new.runs import ROOT
from whats_new.slides import SlideProps
from whats_new.tours import showing
from whats_new.workloads import SECONDS
from whats_new.workloads import WORKLOADS_BY_KEY
from whats_new.workloads import Workload
from whats_new.workloads import perform

OUT = ROOT / "out"
FLAMEGRAPH = "deck-flamegraph.html"
FLAMEGRAPH_SECONDS = 10

# Tachyon refuses `-a` (every thread) with `--async-aware`, which reconstructs stacks from the tasks instead;
# the deck's tasks all run on its own loop, so that mode loses nothing by dropping it.
MODES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("wall", ("-a", "--mode", "wall")),
    ("cpu", ("-a", "--mode", "cpu")),
    ("gil", ("-a", "--mode", "gil")),
    ("exception", ("-a", "--mode", "exception")),
    ("async-aware", ("--async-aware",)),
)

POINTS = (
    "p attaches Tachyon to this deck: the profiler is its child, attached to its parent",
    "c: pure-Python CPU in a worker thread: the hot function, and the lines in it",
    "C: the same on the event loop: the deck freezes, and the profile explains why",
    "n: numpy: compiled code shows up as <native> frames",
    "i: blocking I/O: m to cpu mode, and the idle time vanishes",
    "a: asyncio tasks: m to async-aware mode, and the task tree comes back",
    "g: garbage cycles: <GC> frames",
    "e: raise and catch in a thread: exception mode samples only it",
    "drawing the profiler's screen is work the deck does, so it shows up in the profile",
    "f hands Tachyon the keyboard (s sort, t mode, x trends, h help); Tab takes it back",
    "F: a flamegraph of the next 10 seconds; D: what is every thread doing, right now?",
)
STEPS = len(POINTS)


def profiler_argv(pid: int, mode: int) -> tuple[str, ...]:
    """Tachyon's live TUI attached to `pid`, in the mode at index `mode` of `MODES`."""
    # sys.executable, since the profiler must be the same minor version as the process it attaches to.
    return (sys.executable, "-m", "profiling.sampling", "attach", "--live", *MODES[mode][1], str(pid))


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
    focus = use_focus(auto_focus=props.is_live, handle=props.slide_focus, is_focusable=props.is_live)
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
    pid = props.host.pid

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
    """
    The talking point, on one line (each fits the slide), then the mode and what's running,
    which wraps rather than being clipped when two long-named workloads run at once.
    """
    status = ", ".join(running) if running else "idle"
    return Text(
        content=(
            Chunk(content=POINTS[step], style=CellStyle(foreground=PYTHON_YELLOW, bold=True)),
            Chunk.newline(),
            Chunk(content=f"mode {mode}", style=CellStyle(foreground=PYTHON_BLUE)),
            Chunk(content=f" · {'profiling' if is_profiling else 'p to profile'} · running: {status}"),
        ),
        style=shrink(0) | text_wrap_pretty,
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


WORKLOAD = Wait(timedelta(seconds=SECONDS + 1))
"""Long enough for a workload to finish, in real time, with the profiler watching."""
LOOK = Wait(timedelta(seconds=3))


def press(*keys: str) -> list[AutopilotStep]:
    return [KeyPressed(key=key) for key in keys]


def to_mode(start: int, name: str) -> list[AutopilotStep]:
    """`m` as many times as it takes to get from the mode at index `start` of `MODES` to the one called `name`."""
    target = next(index for index, (mode, _) in enumerate(MODES) if mode == name)
    return press(*["m"] * ((target - start) % len(MODES)))


def tachyon_tour(step: int) -> Iterable[AutopilotStep]:
    """
    What each talking point says to do, done: attach, start each workload and let it finish under the profiler,
    move through the modes the points name, hand Tachyon the keyboard to sort its table, and dump every thread.
    The flamegraph (`F`) is left out: it serves a page the recording can't show.
    """
    match step:
        case 0:
            return [*press("p"), showing("Tachyon Profiler"), LOOK]
        case 1:
            return [*press("c"), WORKLOAD]
        case 2:
            # Freezes the deck, so the autopilot too: the wait ends once the deck draws again.
            return [*press("C"), WORKLOAD, LOOK]
        case 3:
            return [*press("n"), WORKLOAD]
        case 4:
            return [*press("i"), LOOK, *to_mode(0, "cpu"), WORKLOAD]
        case 5:
            return [*to_mode(1, "async-aware"), *press("a"), WORKLOAD]
        case 6:
            return [*press("g"), WORKLOAD]
        case 7:
            return [*to_mode(4, "exception"), *press("e"), WORKLOAD]
        case 9:
            return [*press("f"), LOOK, *press("s"), LOOK, KeyPressed(key=Key.Tab)]
        case 10:
            return [*press("D"), showing("exited"), LOOK]
        case _:
            return []
