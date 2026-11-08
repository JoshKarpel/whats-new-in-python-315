"""10. Lightning round: one runnable line each, where there is one."""

from counterweight.components import component
from counterweight.elements import Div
from counterweight.styles.utilities import *

from whats_new.components.code import code_example
from whats_new.components.layouts import code_above_runs
from whats_new.components.layouts import notes_beside_code_above_runs
from whats_new.components.layouts import side_by_side
from whats_new.components.layouts import stack
from whats_new.components.look import bullets
from whats_new.components.look import centered
from whats_new.components.look import code
from whats_new.components.look import plain
from whats_new.components.look import title_card
from whats_new.components.repl import repl_pane
from whats_new.components.repl import repl_tour
from whats_new.runs import Expect
from whats_new.runs import Interpreter
from whats_new.runs import on_both
from whats_new.runs import python
from whats_new.slides import Slide
from whats_new.slides import SlideProps


@component
def section_title(props: SlideProps) -> Div:
    return centered(title_card("Lightning round", is_live=props.is_live))


@component
def did_you_mean(props: SlideProps) -> Div:
    return code_above_runs(props, code_example(props, "lightning/did_you_mean.py", start="hint("))


@component
def repl(props: SlideProps) -> Div:
    return stack(
        bullets(
            "completions colored by kind of object",
            (code("from x import <Tab>"), plain(" completes the module's names")),
            "pdb uses the new REPL",
        ),
        repl_pane(props),
    )


@component
def context_managers(props: SlideProps) -> Div:
    return notes_beside_code_above_runs(
        props,
        code_example(props, "lightning/contextmanager_generator.py"),
        bullets("as a decorator on a generator, it stays open across the iteration"),
    )


@component
def odds_and_ends(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        side_by_side(
            code_example(props, "lightning/namedtuple_slots.py", start="class Point"),
            code_example(props, "lightning/pprint_expand.py", start="config"),
        ),
    )


@component
def quickfire(props: SlideProps) -> Div:
    return stack(
        bullets(
            (
                code("re.prefixmatch"),
                plain(": "),
                code("re.match"),
                plain(' is soft-deprecated; "match" means "search" elsewhere'),
            ),
            (code("math.integer"), plain(": comb, factorial, gcd, isqrt, lcm, perm")),
            "tomllib speaks TOML 1.1",
            (
                code("-W"),
                plain(" accepts regexes; "),
                code("http.server -H"),
                plain("; "),
                code("timeit --target-time"),
            ),
            "argparse suggests fixes for typos, and about 20 CLIs got color",
            "Windows builds use the tail-calling interpreter: 15-20% on pyperformance, as cited",
            (code("Popen.wait(timeout=)"), plain(" waits on an event, not a sleep loop")),
            (plain("the "), code("pkg.sub"), plain(" / "), code("pkg.sub.mod"), plain(" import deadlock is fixed")),
        ),
        code_above_runs(props, code_example(props, "lightning/broken_pool.py", start="def crash")),
    )


SLIDES = (
    Slide(title="Lightning round", content=section_title, is_title_card=True),
    Slide(
        title="Lightning: did you mean?",
        content=did_you_mean,
        runs=on_both(
            "lightning/did_you_mean.py",
            new=Expect(status=0, output="Did you mean '.append'?"),
            old=Expect(status=0, output="has no attribute 'push'"),
        ),
    ),
    Slide(title="Lightning: the REPL", content=repl, tour=repl_tour),
    Slide(
        title="Lightning: context managers on generators",
        content=context_managers,
        runs=on_both(
            "lightning/contextmanager_generator.py",
            new=Expect(status=0, output="  yielding 2\n</numbers>"),
            old=Expect(status=0, output="</numbers>\n  yielding 1"),
        ),
    ),
    Slide(
        title="Lightning: odds and ends",
        content=odds_and_ends,
        runs=(
            *on_both(
                "lightning/namedtuple_slots.py",
                new=Expect(status=0, output="point=Point(x=1, y=2) point.label='origin-ish'"),
                old=Expect(status=1, output="nonempty __slots__ not supported"),
            ),
            python(Interpreter.PY315, "lightning/pprint_expand.py", expect=Expect(status=0, output="'counterweight',")),
        ),
    ),
    Slide(
        title="Lightning: and more",
        content=quickfire,
        runs=on_both(
            "lightning/broken_pool.py",
            new=Expect(status=0, output="terminated abruptly with exit code 3"),
            old=Expect(status=0, output="error.__cause__=None"),
        ),
    ),
)
