"""5. Performance: Tachyon (the centerpiece), frame pointers, the JIT, base64, and the GC story."""

from counterweight.components import component
from counterweight.elements import Div
from counterweight.styles.utilities import *

from whats_new.components.code import code_example
from whats_new.components.layouts import code_above_runs
from whats_new.components.layouts import stack
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
from whats_new.runs import example
from whats_new.runs import harness
from whats_new.runs import on_both
from whats_new.runs import python
from whats_new.slides import Slide
from whats_new.slides import SlideProps
from whats_new.tachyon import STEPS as TACHYON_STEPS
from whats_new.tachyon import tachyon_stage

PY315 = Interpreter.PY315
PY314 = Interpreter.PY314


@component
def section_title(props: SlideProps) -> Div:
    return centered(
        title_card("Performance"),
        bullets(
            "an observability release: how do I see what Python is doing?",
            "Tachyon, frame pointers, JIT unwind info, gc.get_stats(), faulthandler",
        ),
    )


@component
def tachyon_name(props: SlideProps) -> Div:
    return centered(
        title_card("Tachyon", "profiling.sampling"),
        bullets(
            (plain("a hypothetical "), em("faster-than-light"), plain(' particle ("tachy": swift)')),
            "the PEP calls it an internal codename, and gives no reason",
        ),
    )


@component
def why_sampling(props: SlideProps) -> Div:
    return stack(
        profilers.tracing_vs_sampling(),
        bullets("production performance problems show up in situ: measure before optimizing"),
        run_pane(props),
    )


@component
def why_in_cpython(props: SlideProps) -> Div:
    return stack(profilers.architectures(), run_pane(props))


@component
def the_loop(props: SlideProps) -> Div:
    return stack(profilers.the_loop())


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
    return stack(low_level.frame_pointer_chain(props.step), run_pane(props))


@component
def jit(props: SlideProps) -> Div:
    return stack(
        low_level.jit_pipeline(),
        bullets("still experimental; uv's builds ship it compiled in and off"),
        run_pane(props),
    )


@component
def jit_speed(props: SlideProps) -> Div:
    return stack(
        bullets(
            "the whatsnew cites 7-8% geomean on x86-64 Linux, 11-12% on AArch64 macOS",
            "a float-heavy loop, on this VM, right now:",
        ),
        run_pane(props),
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
def gc_story(props: SlideProps) -> Div:
    return stack(
        low_level.gc_timeline(),
        bullets(
            "cycle churn beside a long-lived heap, peak memory per interpreter",
            "this reproduces the memory complaint, not incremental GC's shorter pauses",
        ),
        run_pane(props),
    )


FRAME_POINTER_DEMO = Run(
    label="perf record --call-graph fp",
    argv=(PY315, str(ROOT / "demos" / "frame_pointers" / "demo.py")),
    expect=Expect(status=0, output="without"),
    needs=frozenset({Capability.PERF}),
)

SLIDES = (
    Slide(title="Performance", content=section_title, has_heading=False),
    Slide(title="Tachyon", content=tachyon_name, has_heading=False),
    Slide(
        title="Why sampling?",
        content=why_sampling,
        peps=(799,),
        runs=(
            harness(
                "bench.py",
                "--interpreter",
                "py",
                PY315,
                "plain={py} {examples}/performance/cpu.py",
                "tracing={py} -m profiling.tracing -o /dev/null {examples}/performance/cpu.py",
                "sampling={py} -m profiling.sampling run -o /dev/null {examples}/performance/cpu.py",
                label="hyperfine",
                expect=Expect(status=0, output="sampling"),
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
    Slide(title="Tachyon, live", content=tachyon_stage, peps=(799,), steps=TACHYON_STEPS),
    Slide(title="Tachyon: and also", content=more_tachyon, peps=(799,)),
    Slide(
        title="Frame pointers",
        content=frame_pointers,
        peps=(831,),
        steps=low_level.FRAME_POINTER_STEPS,
        runs=(FRAME_POINTER_DEMO,),
    ),
    Slide(
        title="The JIT",
        content=jit,
        runs=(
            python(PY315, "performance/jit_status.py", expect=Expect(status=0, output="JIT enabled:   False")),
            Run(
                label="PYTHON_JIT=1",
                argv=(PY315, example("performance/jit_status.py")),
                env=frozendict(PYTHON_JIT="1"),
                expect=Expect(status=0, output="JIT enabled:   True"),
            ),
        ),
    ),
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
                label="nbody",
                expect=Expect(status=0, output="3.15 JIT"),
            ),
        ),
    ),
    Slide(
        title="base64",
        content=base64_speed,
        runs=on_both(
            "performance/base64_bench.py",
            new=Expect(status=0, output="b85encode 1 MB:"),
            old=Expect(status=0, output="b85encode 1 MB:"),
        ),
    ),
    Slide(
        title="The garbage collector",
        content=gc_story,
        runs=(
            harness(
                "gc_peaks.py",
                Interpreter.PY313,
                Interpreter.PY3144,
                PY314,
                PY315,
                label="peak memory",
                expect=Expect(status=0, output="gc.get_threshold() = (2000, 10, 0)"),
            ),
            python(
                PY315, "performance/gc_stats.py", label="gc.get_stats()", expect=Expect(status=0, output="'duration'")
            ),
        ),
    ),
)
