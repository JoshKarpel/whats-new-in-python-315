"""3. Concurrency: TaskGroup.cancel, iterator synchronization, and the state of free-threading."""

from functools import partial

from counterweight.components import component
from counterweight.elements import Div
from counterweight.styles.utilities import *

from whats_new.components.code import code_example
from whats_new.components.code import labeled
from whats_new.components.layouts import code_above_runs
from whats_new.components.layouts import notes_beside_code_above_runs
from whats_new.components.layouts import side_by_side
from whats_new.components.layouts import stack
from whats_new.components.look import bullets
from whats_new.components.look import centered
from whats_new.components.look import code
from whats_new.components.look import em
from whats_new.components.look import plain
from whats_new.components.look import title_card
from whats_new.diagrams import fan_out
from whats_new.diagrams import task_group
from whats_new.runs import Expect
from whats_new.runs import Interpreter
from whats_new.runs import on_both
from whats_new.runs import python
from whats_new.slides import Slide
from whats_new.slides import SlideProps

PY315 = Interpreter.PY315
PY314 = Interpreter.PY314


@component
def section_title(props: SlideProps) -> Div:
    return centered(title_card("Concurrency", is_live=props.is_live))


@component
def first_wins(props: SlideProps) -> Div:
    return code_above_runs(props, code_example(props, "concurrency/first_wins.py", start="DELAYS"))


@component
def first_wins_tree(props: SlideProps) -> Div:
    return stack(task_group.task_group(props.step, props.is_live))


@component
def first_wins_old(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "concurrency/first_wins_old.py", start="class Done"),
    )


@component
def shutdown(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "concurrency/shutdown.py", start="async def worker"),
    )


@component
def shared_generator(props: SlideProps) -> Div:
    return notes_beside_code_above_runs(
        props,
        code_example(props, "concurrency/shared_generator.py", start="def rows"),
        bullets(
            "never safe to share one generator between threads",
            "the same on 3.14 and 3.15, with or without the GIL",
        ),
    )


@component
def broken_fan_out(props: SlideProps) -> Div:
    return stack(fan_out.fan_out(fan_out.BROKEN, props.step, props.is_live))


@component
def shared_iterator(props: SlideProps) -> Div:
    return notes_beside_code_above_runs(
        props,
        code_example(props, "concurrency/shared_iterator.py", start="class Countdown"),
        bullets(
            (
                plain("on a free-threaded build, a hand-written "),
                code("__next__"),
                plain(" hands out "),
                em("duplicates"),
                plain(", silently"),
            ),
            "the same on 3.14t and 3.15t",
        ),
    )


@component
def serialize(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "concurrency/serialize.py", start="def consume"),
        bullets("the counts sum to 10,000: each item went to exactly one thread"),
    )


@component
def shared_fan_out(props: SlideProps) -> Div:
    return stack(
        fan_out.fan_out(fan_out.SHARED, props.step, props.is_live),
        bullets(
            (plain("production stays serial: the lock is held across "), code("__next__")),
            "only the consumers' work runs in parallel",
        ),
    )


@component
def old_patterns(props: SlideProps) -> Div:
    return stack(
        side_by_side(
            labeled("a lock around next()", code_example(props, "concurrency/locked_iterator.py", start="class")),
            labeled("a feeder thread and a queue", code_example(props, "concurrency/feeder_queue.py", start="DONE")),
        ),
        bullets(
            (plain("now: "), code("threading.serialize_iterator(it)"), plain(", and friends")),
        ),
    )


@component
def free_threading(props: SlideProps) -> Div:
    return notes_beside_code_above_runs(
        props,
        code_example(props, "concurrency/abi_info.py"),
        bullets(
            (plain("PEP 803: one "), code("abi3t"), plain(" wheel for free-threaded 3.15 and later")),
            "so free-threaded wheels should arrive faster",
            "the python.org macOS installer includes it by default",
            "raw allocations use mimalloc",
        ),
    )


SLIDES = (
    Slide(title="Concurrency", content=section_title, is_title_card=True),
    Slide(
        title="TaskGroup.cancel()",
        content=first_wins,
        runs=(
            python(
                Interpreter.PY315,
                "concurrency/first_wins.py",
                expect=Expect(status=0, output="('eu', 'payload from eu')"),
            ),
        ),
    ),
    Slide(
        title="TaskGroup.cancel(): first mirror wins",
        content=first_wins_tree,
        steps=task_group.STEPS,
        ends_showing=task_group.ends_showing,
    ),
    Slide(
        title="TaskGroup.cancel(): how it was done before",
        content=first_wins_old,
        runs=(
            python(PY314, "concurrency/first_wins_old.py", expect=Expect(status=0, output="('eu', 'payload from eu')")),
        ),
    ),
    Slide(
        title="TaskGroup.cancel(): clean shutdown",
        content=shutdown,
        runs=(
            python(Interpreter.PY315, "concurrency/shutdown.py", expect=Expect(status=0, output="shut down cleanly")),
        ),
    ),
    Slide(
        title="Sharing a generator between threads",
        content=shared_generator,
        runs=on_both(
            "concurrency/shared_generator.py",
            old=Expect(status=0, output="generator already executing"),
            new=Expect(status=0, output="generator already executing"),
        ),
    ),
    Slide(
        title="One generator, three threads",
        content=broken_fan_out,
        steps=fan_out.steps(fan_out.BROKEN),
        ends_showing=partial(fan_out.ends_showing, fan_out.BROKEN),
    ),
    Slide(
        title="Sharing a hand-written iterator",
        content=shared_iterator,
        runs=(
            python(PY315, "concurrency/shared_iterator.py", expect=Expect(status=0, output="GIL=True\n0 duplicates")),
            python(
                Interpreter.PY314T,
                "concurrency/shared_iterator.py",
                label="3.14t",
                expect=Expect(status=0, output="GIL=False"),
            ),
            python(
                Interpreter.PY315T,
                "concurrency/shared_iterator.py",
                label="3.15t",
                expect=Expect(status=0, output="GIL=False"),
            ),
        ),
    ),
    Slide(title="Before: lock it yourself", content=old_patterns),
    Slide(
        title="threading.serialize_iterator and friends",
        content=serialize,
        runs=(
            python(
                PY315,
                "concurrency/serialize.py",
                expect=Expect(status=0, output="sum(counts)=10000"),
            ),
            python(
                Interpreter.PY315T,
                "concurrency/serialize.py",
                label="3.15t",
                expect=Expect(status=0, output="sum(counts)=10000"),
            ),
        ),
    ),
    Slide(
        title="serialize_iterator or concurrent_tee",
        content=shared_fan_out,
        steps=fan_out.steps(fan_out.SHARED),
        ends_showing=partial(fan_out.ends_showing, fan_out.SHARED),
    ),
    Slide(
        title="Free-threading in 3.15",
        content=free_threading,
        peps=(803,),
        runs=(
            python(PY315, "concurrency/abi_info.py", expect=Expect(status=0, output="free_threaded=False")),
            python(
                Interpreter.PY315T,
                "concurrency/abi_info.py",
                label="3.15t",
                expect=Expect(status=0, output="free_threaded=True"),
            ),
        ),
    ),
)
