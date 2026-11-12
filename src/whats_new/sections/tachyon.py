"""6. Tachyon, the sampling profiler (the centerpiece): why sampling, why in CPython, and the deck profiling itself."""

from datetime import timedelta

from counterweight.components import component
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.gradients import linear_gradient
from counterweight.hooks import use_loop
from counterweight.styles import CellStyle
from counterweight.styles import Color
from counterweight.styles.utilities import *

from whats_new.components.code import code_example
from whats_new.components.code import labeled
from whats_new.components.layouts import code_above_runs
from whats_new.components.layouts import side_by_side
from whats_new.components.layouts import stack
from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.look import bullets
from whats_new.components.look import centered
from whats_new.components.look import code
from whats_new.components.look import em
from whats_new.components.look import plain
from whats_new.components.look import title_card
from whats_new.components.run_pane import run_pane
from whats_new.diagrams import profilers
from whats_new.runs import Expect
from whats_new.runs import Interpreter
from whats_new.runs import harness
from whats_new.runs import python
from whats_new.slides import Slide
from whats_new.slides import SlideProps
from whats_new.tachyon import tachyon_stage
from whats_new.tachyon import tachyon_tour

PY315 = Interpreter.PY315
PY314 = Interpreter.PY314


STREAK_WIDTH = 60
STREAK_PERIOD = timedelta(seconds=2.5)
TRAIL = "━━━━━━━━────────····"
"""The trail behind the particle, thinning away from it."""
EMBER = PYTHON_YELLOW.blend(Color.from_hex("#000000"), 0.85)
"""The color the trail fades to at its end, from Python's yellow at the particle."""


@component
def streak(is_live: bool) -> Text:
    """
    A particle streaking across, ahead of its own trail, looping while the slide is up:
    the one decorative animation, so it starts on arrival rather than on a key.
    """
    phase = use_loop(STREAK_PERIOD, is_playing=is_live)
    # Past the right edge for the last third of each loop, so the streak comes round again after a pause.
    head = round(phase * STREAK_WIDTH * 1.5)
    cells = [" "] * STREAK_WIDTH
    for distance, mark in enumerate(TRAIL, 1):
        x = head - distance
        if 0 <= x < STREAK_WIDTH:
            cells[x] = mark
    # The trail fades along the text's content box, which is the streak's whole width, from the particle back.
    span = STREAK_WIDTH - 1
    fade = linear_gradient((EMBER, (head - len(TRAIL)) / span), (PYTHON_YELLOW, (head - 1) / span), to="right")
    behind = min(head, STREAK_WIDTH)
    return Text(
        content=(
            Chunk(content="".join(cells[:behind])),
            *(
                (Chunk(content="●", style=CellStyle(foreground=PYTHON_YELLOW, bold=True)),)
                if head < STREAK_WIDTH
                else ()
            ),
            Chunk(content="".join(cells[behind + 1 :])),
        ),
        style=text_gradient(fade) | text_wrap_none | shrink(0),
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
        bullets(
            "tracing is planned ahead: start the program under it, and it slows the whole run",
            "sampling is ad hoc: attach to the process already running, in place, once it's slow",
        ),
    )


@component
def sampling_overhead(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "tachyon/cpu.py"),
        bullets("the program times itself: the overhead it feels, not the profiler's start-up"),
    )


@component
def why_in_cpython(props: SlideProps) -> Div:
    return stack(profilers.architectures(), run_pane(props))


@component
def finding_the_slow_line(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "tachyon/report.py", is_numbered=True),
    )


@component
def the_fix(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        side_by_side(
            labeled("report.py", code_example(props, "tachyon/report.py", start="def unique_users", stop="lines =")),
            labeled(
                "report_fixed.py",
                code_example(props, "tachyon/report_fixed.py", start="def unique_users", stop="lines ="),
            ),
        ),
        bullets(
            (code("not in"), plain(" a list compares against every user so far; a set hashes once")),
            (plain("profile it again: what's left is building the lines, and "), code("parse")),
        ),
    )


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


SLIDES = (
    Slide(title="Tachyon", content=tachyon_name, is_title_card=True),
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
                "tachyon/cpu.py",
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
    Slide(
        title="Finding the slow line",
        content=finding_the_slow_line,
        peps=(799,),
        runs=(
            python(PY315, "tachyon/report.py", label="python report.py", expect=Expect(status=0, output="3,000 users")),
            harness(
                "profile.py",
                "tracing",
                "tachyon/report.py",
                label="profiling.tracing",
                expect=Expect(status=0, output="report.py:7(unique_users)"),
            ),
            harness(
                "profile.py",
                "sampling",
                "tachyon/report.py",
                label="profiling.sampling run",
                expect=Expect(status=0, output="report.py:10(unique_users)"),
            ),
        ),
    ),
    Slide(
        title="Finding the slow line: the fix",
        content=the_fix,
        peps=(799,),
        runs=(
            python(
                PY315,
                "tachyon/report_fixed.py",
                label="python report_fixed.py",
                expect=Expect(status=0, output="3,000 users"),
            ),
            harness(
                "profile.py",
                "sampling",
                "tachyon/report_fixed.py",
                label="profiling.sampling run",
                expect=Expect(status=0, output="report_fixed.py:14(<module>)"),
            ),
        ),
    ),
    Slide(title="Profiling the talk, from inside the talk", content=the_loop, peps=(799,)),
    Slide(title="Tachyon, live", content=tachyon_stage, peps=(799,), tour=tachyon_tour),
    Slide(title="Tachyon: and also", content=more_tachyon, peps=(799,)),
)
