"""5. Performance: frame pointers, the JIT, and base64."""

from counterweight.components import component
from counterweight.elements import Div
from counterweight.styles.utilities import *

from whats_new.components.code import code_example
from whats_new.components.code import labeled
from whats_new.components.layouts import code_above_runs
from whats_new.components.layouts import stack
from whats_new.components.look import bullets
from whats_new.components.look import centered
from whats_new.components.look import code
from whats_new.components.look import plain
from whats_new.components.look import title_card
from whats_new.components.run_pane import run_pane
from whats_new.diagrams import low_level
from whats_new.runs import ROOT
from whats_new.runs import Capability
from whats_new.runs import Expect
from whats_new.runs import Interpreter
from whats_new.runs import Run
from whats_new.runs import harness
from whats_new.slides import Slide
from whats_new.slides import SlideProps

PY315 = Interpreter.PY315
PY314 = Interpreter.PY314


@component
def section_title(props: SlideProps) -> Div:
    return centered(
        title_card("Performance", is_live=props.is_live),
        bullets(
            "an observability release: how do I see what Python is doing?",
            "Tachyon, frame pointers, JIT unwind info, gc.get_stats(), faulthandler",
        ),
    )


@component
def frame_pointers(props: SlideProps) -> Div:
    return stack(low_level.frame_pointer_chain(props.step, props.is_live), run_pane(props))


@component
def jit(props: SlideProps) -> Div:
    return stack(
        low_level.jit_pipeline(),
        bullets(
            "a just-in-time compiler: turns hot bytecode into machine code while the program runs",
            "still experimental: uv's builds ship it compiled in, and off",
            (code("PYTHON_JIT=1"), plain(" turns it on, and "), code("sys._jit.is_enabled()"), plain(" says so")),
            "the whatsnew cites 7-8% geomean on x86-64 Linux, 11-12% on AArch64 macOS",
        ),
    )


@component
def jit_speed(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        labeled(
            "nbody.py: the hot loop, run 60,000 times",
            code_example(props, "performance/nbody.py", start="    for _ in range(steps)", stop="        for b in"),
        ),
    )


@component
def base64_speed(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "performance/base64_bench.py", start="print(sys"),
        bullets(
            "C rewrites, and b32/b85 moved to C",
            "a 5 MB PDF in a JSON body for an LLM API: real, and small next to the network",
        ),
    )


FRAME_POINTER_DEMO = Run(
    label="perf record --call-graph fp",
    argv=(PY315, str(ROOT / "demos" / "frame_pointers" / "demo.py")),
    expect=Expect(status=0, output="without"),
    needs=frozenset({Capability.PERF}),
)

SLIDES = (
    Slide(title="Performance", content=section_title, is_title_card=True),
    Slide(
        title="Frame pointers",
        content=frame_pointers,
        peps=(831,),
        steps=low_level.FRAME_POINTER_STEPS,
        runs=(FRAME_POINTER_DEMO,),
        ends_showing=low_level.frame_pointers_end_showing,
    ),
    Slide(title="The JIT", content=jit),
    Slide(
        title="The JIT: how much faster?",
        content=jit_speed,
        runs=(
            harness(
                "bench.py",
                "--interpreter",
                "py315",
                PY315,
                "--interpreter",
                "py314",
                PY314,
                "3.14={py314} {examples}/performance/nbody.py",
                "3.14 JIT=env PYTHON_JIT=1 {py314} {examples}/performance/nbody.py",
                "3.15={py315} {examples}/performance/nbody.py",
                "3.15 JIT=env PYTHON_JIT=1 {py315} {examples}/performance/nbody.py",
                label="hyperfine",
                expect=Expect(status=0, output="3.15 JIT"),
            ),
        ),
    ),
    Slide(
        title="base64",
        content=base64_speed,
        runs=(
            harness(
                "versions.py",
                "performance/base64_bench.py",
                PY314,
                PY315,
                label="3.14 and 3.15, side by side",
                expect=Expect(status=0, output="b85encode 1 MB"),
            ),
        ),
    ),
)
