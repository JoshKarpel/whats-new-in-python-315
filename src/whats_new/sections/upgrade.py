"""6. Before you upgrade: what bites, run on 3.14 and 3.15 side by side."""

from counterweight.components import component
from counterweight.elements import Div
from counterweight.styles.utilities import *

from whats_new.components.code import code_example
from whats_new.components.layouts import code_above_runs
from whats_new.components.layouts import code_beside_runs
from whats_new.components.look import bullets
from whats_new.components.look import code
from whats_new.components.look import em
from whats_new.components.look import plain
from whats_new.runs import Expect
from whats_new.runs import Interpreter
from whats_new.runs import Run
from whats_new.runs import example
from whats_new.runs import on_both
from whats_new.slides import Slide
from whats_new.slides import SlideProps


@component
def breakage(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        bullets(
            (
                plain("every "),
                code("TypeError"),
                plain(" and "),
                code("ValueError"),
                plain(" here was a "),
                code("DeprecationWarning"),
                plain(" on 3.14"),
            ),
            (plain("so run your tests on 3.14 with "), em("-W error::DeprecationWarning"), plain(" first")),
        ),
    )


@component
def assert_warns(props: SlideProps) -> Div:
    return code_beside_runs(
        props,
        code_example("upgrade/assert_warns.py", start="class Test"),
        bullets(
            (code("assertWarns"), plain(" no longer swallows warnings that don't match")),
            "so a test suite can start leaking warnings it used to hide",
        ),
    )


@component
def utf8(props: SlideProps) -> Div:
    return code_beside_runs(
        props,
        code_example("upgrade/encoding.py"),
        bullets(
            "UTF-8 by default: the change most likely to alter behavior silently, especially on Windows",
            (code("PYTHONUTF8=0"), plain(" or "), code("-X utf8=0"), plain(" for the old behavior")),
            (code('encoding="locale"'), plain(" asks for the locale explicitly")),
            (code("-X warn_default_encoding"), plain(" finds every call relying on the default")),
        ),
    )


@component
def smaller_changes(props: SlideProps) -> Div:
    return code_beside_runs(
        props,
        code_example("upgrade/argparse_dest.py"),
        bullets(
            (
                code("urlsafe_b64decode"),
                plain(" no longer requires padding: "),
                code("padded=True"),
                plain(" for strictness"),
            ),
            (code("importlib.metadata.metadata()"), plain(" raises "), code("MetadataNotFound")),
            (
                plain("coming: "),
                code("profile"),
                plain(" removed in 3.17 (use "),
                code("profiling.tracing"),
                plain(")"),
            ),
            (plain("coming: about 25 "), code("__version__"), plain(" attributes deprecated for 3.20")),
        ),
    )


def latin1(interpreter: Interpreter, expected: str) -> Run:
    return Run(
        label=f"{interpreter.install_request}, LC_ALL=en_US",
        argv=(interpreter, example("upgrade/encoding.py")),
        env=frozendict(LC_ALL="en_US", LANG="en_US"),
        expect=Expect(status=0, output=expected),
    )


SLIDES = (
    Slide(
        title="Before you upgrade",
        content=breakage,
        runs=on_both(
            "upgrade/breakage.py",
            new=Expect(status=0, output='strptime("29", "%d")       ValueError'),
            old=Expect(status=0, output="(DeprecationWarning)"),
        ),
    ),
    Slide(
        title="Before you upgrade: assertWarns",
        content=assert_warns,
        runs=on_both(
            "upgrade/assert_warns.py",
            new=Expect(status=0, output="leaked: ['unrelated']"),
            old=Expect(status=0, output="leaked: []"),
        ),
    ),
    Slide(
        title="Before you upgrade: UTF-8 by default",
        content=utf8,
        peps=(686,),
        runs=(
            latin1(Interpreter.PY315, "open() encoding: utf-8"),
            latin1(Interpreter.PY314, "open() encoding: ISO-8859-1"),
        ),
    ),
    Slide(
        title="Before you upgrade: and also",
        content=smaller_changes,
        runs=on_both(
            "upgrade/argparse_dest.py",
            new=Expect(status=0, output="Namespace(foo='bar')"),
            old=Expect(status=0, output="Namespace(f='bar')"),
        ),
    ),
)
