"""5. Performance: Tachyon (the centerpiece), frame pointers, the JIT, base64, and the GC story."""

from datetime import timedelta

from counterweight.components import component
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles import CellStyle
from counterweight.styles.utilities import *

from whats_new.components.animation import use_loop
from whats_new.components.code import code_example
from whats_new.components.code import labeled
from whats_new.components.layouts import code_above_runs
from whats_new.components.layouts import stack
from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.look import bullets
from whats_new.components.look import centered
from whats_new.components.look import code
from whats_new.components.look import em
from whats_new.components.look import plain
from whats_new.components.look import title_card
from whats_new.components.run_pane import run_pane
from whats_new.diagrams import low_level
from whats_new.diagrams import profilers
from whats_new.runs import ROOT
from whats_new.runs import Capability
from whats_new.runs import Expect
from whats_new.runs import Interpreter
from whats_new.runs import Run
from whats_new.runs import harness
from whats_new.slides import Slide
from whats_new.slides import SlideProps
from whats_new.slides import TitleCard
from whats_new.tachyon import STEPS as TACHYON_STEPS
from whats_new.tachyon import tachyon_stage
from whats_new.tachyon import tachyon_tour

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


STREAK_WIDTH = 60
STREAK_PERIOD = timedelta(seconds=2.5)
TRAIL = "━━━━━━━━────────····"
"""The trail behind the particle, brightest nearest it."""


@component
def streak(is_live: bool) -> Text:
    """
    A particle streaking across, ahead of its own trail, looping while the slide is up:
    the one decorative animation, so it starts on arrival rather than on a key.
    """
    phase = use_loop(STREAK_PERIOD, is_live)
    # Past the right edge for the last third of each loop, so the streak comes round again after a pause.
    head = round(phase * STREAK_WIDTH * 1.5)
    cells = [" "] * STREAK_WIDTH
    shades: list[CellStyle] = [CellStyle()] * STREAK_WIDTH
    for distance, mark in enumerate(TRAIL, 1):
        x = head - distance
        if 0 <= x < STREAK_WIDTH:
            cells[x] = mark
            shades[x] = CellStyle(foreground=PYTHON_YELLOW, dim=distance > len(TRAIL) // 2)
    if head < STREAK_WIDTH:
        cells[head] = "●"
        shades[head] = CellStyle(foreground=PYTHON_YELLOW, bold=True)
    return Text(
        content=tuple(Chunk(content=cell, style=shade) for cell, shade in zip(cells, shades, strict=True)),
        style=text_wrap_none | shrink(0),
    )


@component
def tachyon_name(props: SlideProps) -> Div:
    return centered(
        title_card("Tachyon", "profiling.sampling", is_live=props.is_live),
        streak(props.is_live),
        bullets(
            (plain("a hypothetical "), em("faster-than-light"), plain(' particle ("tachy": swift)')),
            "the PEP calls it an internal codename, and gives no reason",
        ),
    )


@component
def why_sampling(props: SlideProps) -> Div:
    return stack(
        profilers.tracing_vs_sampling(props.step, props.is_live),
        bullets("production performance problems show up in situ: measure before optimizing"),
    )


@component
def sampling_overhead(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "performance/cpu.py"),
        bullets("the program times itself: the overhead it feels, not the profiler's start-up"),
    )


@component
def why_in_cpython(props: SlideProps) -> Div:
    return stack(profilers.architectures(), run_pane(props))


@component
def the_loop(props: SlideProps) -> Div:
    return stack(profilers.the_loop(props.host.pid))


@component
def more_tachyon(props: SlideProps) -> Div:
    return stack(
        bullets(
            (code("dump <pid>"), plain(": a one-shot stack, for asking a hung process what it's doing")),
            (code("--flamegraph"), plain(", "), code("--diff-flamegraph"), plain(", "), code("--heatmap")),
            (
                code("--gecko"),
                plain(" for profiler.firefox.com, "),
                code("--collapsed"),
                plain(" for any flamegraph tool"),
            ),
            (code("--opcodes"), plain(": which bytecode is running, specializations included")),
            "sampling rate depends on the hardware: don't expect the documented 1 MHz on a small VM",
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


@component
def gc_title(props: SlideProps) -> Div:
    return centered(title_card("The garbage collector saga", is_live=props.is_live))


@component
def gc_story(props: SlideProps) -> Div:
    return stack(
        low_level.gc_timeline(props.step, props.is_live),
        bullets(
            "3.15 ships the generational collector",
            "bringing the incremental one back now takes a PEP",
        ),
    )


@component
def gc_peaks(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        labeled(
            "gc_churn.py: cycles churning beside a long-lived heap",
            code_example(props, "performance/gc_churn.py", start="class Node", stop="peak ="),
        ),
        bullets("it reproduces the memory complaint, not incremental GC's shorter pauses"),
    )


FRAME_POINTER_DEMO = Run(
    label="perf record --call-graph fp",
    argv=(PY315, str(ROOT / "demos" / "frame_pointers" / "demo.py")),
    expect=Expect(status=0, output="without"),
    needs=frozenset({Capability.PERF}),
)

SLIDES = (
    Slide(title="Performance", content=section_title, title_card=TitleCard.SECTION),
    Slide(title="Tachyon", content=tachyon_name, title_card=TitleCard.SUBSECTION),
    Slide(
        title="Why sampling?",
        content=why_sampling,
        peps=(799,),
        steps=profilers.SAMPLING_STEPS,
        ends_showing=profilers.ends_showing,
    ),
    Slide(
        title="Tracing vs sampling: the overhead",
        content=sampling_overhead,
        peps=(799,),
        runs=(
            harness(
                "overhead.py",
                "performance/cpu.py",
                label="no profiler, tracing, sampling",
                expect=Expect(status=0, output="python -m profiling.sampling run cpu.py: "),
            ),
        ),
    ),
    Slide(
        title="Why in CPython?",
        content=why_in_cpython,
        peps=(799,),
        runs=(
            harness(
                "version_mismatch.py",
                PY314,
                label="3.15's Tachyon, 3.14's process",
                expect=Expect(status=0, output="Can't attach from a Python 3.15 process to a Python 3.14 process"),
            ),
        ),
    ),
    Slide(title="Profiling the talk, from inside the talk", content=the_loop, peps=(799,)),
    Slide(title="Tachyon, live", content=tachyon_stage, peps=(799,), steps=TACHYON_STEPS, tour=tachyon_tour),
    Slide(title="Tachyon: and also", content=more_tachyon, peps=(799,)),
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
    Slide(title="The garbage collector saga", content=gc_title, title_card=TitleCard.SUBSECTION),
    Slide(
        title="The garbage collector",
        content=gc_story,
        steps=low_level.GC_STEPS,
        ends_showing=low_level.gc_timeline_ends_showing,
    ),
    Slide(
        title="The garbage collector: peak memory",
        content=gc_peaks,
        runs=(
            harness(
                "gc_peaks.py",
                Interpreter.PY313,
                Interpreter.PY3144,
                PY314,
                PY315,
                label="3.13, 3.14.4, 3.14.7, 3.15",
                expect=Expect(status=0, output="gc.get_threshold() = (2000, 10, 0)"),
            ),
        ),
    ),
)
