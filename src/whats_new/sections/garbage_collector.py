"""7. The garbage collector saga: what the cycle collector does, and incremental GC's arrival and revert."""

from counterweight.components import component
from counterweight.elements import Div

from whats_new.components.code import code_example
from whats_new.components.code import code_snippet
from whats_new.components.code import labeled
from whats_new.components.layouts import code_above_runs
from whats_new.components.layouts import stack
from whats_new.components.look import attributed
from whats_new.components.look import bullets
from whats_new.components.look import centered
from whats_new.components.look import plain
from whats_new.components.look import title_card
from whats_new.diagrams import collector
from whats_new.runs import Expect
from whats_new.runs import Interpreter
from whats_new.runs import harness
from whats_new.slides import Slide
from whats_new.slides import SlideProps


@component
def section_title(props: SlideProps) -> Div:
    return centered(title_card("The garbage collector saga", is_live=props.is_live))


@component
def gc_cycles(props: SlideProps) -> Div:
    return stack(collector.cycle_collection(props.step, props.is_live))


@component
def gc_generations(props: SlideProps) -> Div:
    return stack(collector.generations(props.step, props.is_live))


@component
def gc_schedules(props: SlideProps) -> Div:
    return stack(collector.schedules(props.step, props.is_live))


@component
def gc_story(props: SlideProps) -> Div:
    return stack(
        collector.timeline(props.step, props.is_live),
        bullets(
            "3.15 ships the generational collector",
            "bringing the incremental one back now takes a PEP",
        ),
    )


REVERT_THREAD = "https://discuss.python.org/t/reverting-the-incremental-gc-in-python-3-14-and-3-15/107014"
"""The Steering Council-backed revert's thread, where Sergey Miryanov's posts below are."""

EARLY_RETURN = """\
gcstate->work_to_do += assess_work_to_do(gcstate);
if (gcstate->work_to_do < 0) {
    return;
}"""
"""The early return in `gc_collect_increment` that Sergey Miryanov points to, verbatim from `Python/gc.c`."""


@component
def gc_went_wrong(props: SlideProps) -> Div:
    return stack(
        labeled(
            "Python/gc.c, every automatic collection, since 3.14.1", code_snippet(props, EARLY_RETURN, language="c")
        ),
        bullets(
            (
                plain('"The incremental GC has early return since 3.14.1. Even if threshold0 reached, '),
                plain('it can exit early and skip all processing." '),
                attributed("Sergey Miryanov", f"{REVERT_THREAD}/22"),
            ),
            (
                plain("\"they do get reclaimed, but it can take a long time since it's controlled by the "),
                plain('work_to_do logic and the size of the old generation" '),
                attributed("Sergey Miryanov", f"{REVERT_THREAD}/29"),
            ),
        ),
        collector.waiting(props.step, props.is_live),
    )


@component
def gc_peaks(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        labeled(
            "gc_churn.py: cycles churning beside a long-lived heap",
            code_example(props, "gc/gc_churn.py", start="class Node", stop="peak ="),
        ),
        bullets(
            "in production: an httpx response cycle holding an 800 kB SSLContext",
            "it reproduces the memory complaint, not incremental GC's shorter pauses",
        ),
    )


SLIDES = (
    Slide(title="The garbage collector saga", content=section_title, is_title_card=True),
    Slide(
        title="The garbage collector: what it's for",
        content=gc_cycles,
        steps=collector.CYCLE_STEPS,
        ends_showing=collector.cycle_collection_ends_showing,
    ),
    Slide(
        title="The garbage collector: generations",
        content=gc_generations,
        steps=collector.GENERATION_STEPS,
        ends_showing=collector.generations_ends_showing,
    ),
    Slide(
        title="The garbage collector: two schedules",
        content=gc_schedules,
        steps=collector.SCHEDULE_STEPS,
        ends_showing=collector.schedules_ends_showing,
    ),
    Slide(
        title="The garbage collector",
        content=gc_story,
        steps=collector.TIMELINE_STEPS,
        ends_showing=collector.timeline_ends_showing,
    ),
    Slide(
        title="The garbage collector: what went wrong",
        content=gc_went_wrong,
        steps=collector.WAITING_STEPS,
        ends_showing=collector.waiting_ends_showing,
    ),
    Slide(
        title="The garbage collector: peak memory",
        content=gc_peaks,
        runs=(
            harness(
                "gc_peaks.py",
                Interpreter.PY313,
                Interpreter.PY3140,
                Interpreter.PY3144,
                Interpreter.PY314,
                Interpreter.PY315,
                label="3.13, 3.14.0, 3.14.4, 3.14.7, 3.15",
                expect=Expect(status=0, output="gc.get_threshold() = (2000, 10, 0)"),
            ),
        ),
    ),
)
