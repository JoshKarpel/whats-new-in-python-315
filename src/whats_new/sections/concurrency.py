"""3. Concurrency: TaskGroup.cancel, iterator synchronization, and the state of free-threading."""

from counterweight.components import component
from counterweight.elements import Div
from counterweight.styles.utilities import *

from whats_new.components.code import code_example
from whats_new.components.layouts import code_beside_runs
from whats_new.components.layouts import stack
from whats_new.components.look import bullets
from whats_new.components.look import centered
from whats_new.components.look import code
from whats_new.components.look import em
from whats_new.components.look import plain
from whats_new.components.look import title_card
from whats_new.components.run_pane import run_pane
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
NO_CANCEL = Expect(status=1, output="'TaskGroup' object has no attribute 'cancel'")


@component
def section_title(props: SlideProps) -> Div:
    return centered(title_card("Concurrency"))


@component
def first_wins(props: SlideProps) -> Div:
    return code_beside_runs(props, code_example("concurrency/first_wins.py", start="async def first_wins"))


@component
def first_wins_tree(props: SlideProps) -> Div:
    return stack(task_group.task_group(props.step))


@component
def first_wins_old(props: SlideProps) -> Div:
    return code_beside_runs(
        props,
        code_example("concurrency/first_wins_old.py", start="class Done"),
    )


@component
def shutdown(props: SlideProps) -> Div:
    return code_beside_runs(
        props,
        code_example("concurrency/shutdown.py", start="async def worker"),
    )


@component
def shared_iterators(props: SlideProps) -> Div:
    return Div(
        style=row | fill(1) | gap(1),
        children=(
            Div(
                style=col | gap(1) | shrink(0),
                children=(
                    code_example("concurrency/shared_generator.py", start="def rows"),
                    bullets(
                        "never safe to share one generator between threads",
                        (plain("and on a free-threaded build, a hand-written "), code("__next__")),
                        (plain("hands out "), em("duplicates"), plain(", silently")),
                    ),
                ),
            ),
            run_pane(props, vertical=True),
        ),
    )


@component
def serialize(props: SlideProps) -> Div:
    return code_beside_runs(
        props,
        code_example("concurrency/serialize.py", start="def consume"),
    )


@component
def fan_outs(props: SlideProps) -> Div:
    return stack(
        fan_out.fan_out(props.step),
        bullets(
            (plain("production stays serial: the lock is held across "), code("__next__")),
            "only the consumers' work runs in parallel",
        ),
    )


@component
def old_patterns(props: SlideProps) -> Div:
    return stack(
        Div(
            style=row | gap(2),
            children=(
                code_example("concurrency/locked_iterator.py", start="class LockedIterator"),
                bullets(
                    "before: a lock-wrapping iterator class,",
                    "or a feeder thread and a queue.Queue",
                    (plain("now: "), code("threading.serialize_iterator(it)")),
                ),
            ),
        ),
    )


@component
def free_threading(props: SlideProps) -> Div:
    return code_beside_runs(
        props,
        code_example("concurrency/abi_info.py"),
        bullets(
            (plain("PEP 803: one "), code("abi3t"), plain(" wheel for free-threaded 3.15 and later")),
            "so free-threaded wheels should arrive faster",
            "the python.org macOS installer includes it by default",
            "raw allocations use mimalloc",
        ),
    )


SLIDES = (
    Slide(title="Concurrency", content=section_title, has_heading=False),
    Slide(
        title="TaskGroup.cancel()",
        content=first_wins,
        runs=on_both(
            "concurrency/first_wins.py", new=Expect(status=0, output="('eu', 'payload from eu')"), old=NO_CANCEL
        ),
    ),
    Slide(title="TaskGroup.cancel(): first mirror wins", content=first_wins_tree, steps=task_group.STEPS),
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
        runs=on_both("concurrency/shutdown.py", new=Expect(status=0, output="shut down cleanly"), old=NO_CANCEL),
    ),
    Slide(
        title="Sharing an iterator between threads",
        content=shared_iterators,
        runs=(
            python(
                PY315,
                "concurrency/shared_generator.py",
                label="generator, 3.15",
                expect=Expect(status=0, output="generator already executing"),
            ),
            python(
                Interpreter.PY315T,
                "concurrency/shared_iterator.py",
                label="__next__, 3.15t",
                expect=Expect(status=0, output="free-threaded"),
            ),
            python(
                Interpreter.PY314T,
                "concurrency/shared_iterator.py",
                label="__next__, 3.14t",
                expect=Expect(status=0, output="free-threaded"),
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
                expect=Expect(status=0, output="concurrent_tee:     [10000, 10000, 10000, 10000]"),
            ),
            python(
                Interpreter.PY315T,
                "concurrency/serialize.py",
                label="3.15t",
                expect=Expect(status=0, output="concurrent_tee:     [10000, 10000, 10000, 10000]"),
            ),
        ),
    ),
    Slide(title="One source, four threads", content=fan_outs, steps=fan_out.STEPS),
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
