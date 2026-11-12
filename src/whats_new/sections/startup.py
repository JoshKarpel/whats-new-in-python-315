"""2. Startup and imports: lazy imports, and .start files."""

from counterweight.components import component
from counterweight.elements import Div
from counterweight.styles.utilities import *

from whats_new.components.code import code_example
from whats_new.components.code import code_snippet
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
from whats_new.components.run_pane import run_pane
from whats_new.diagrams.site_startup import site_startup
from whats_new.runs import Expect
from whats_new.runs import Interpreter
from whats_new.runs import harness
from whats_new.runs import on_both
from whats_new.runs import python
from whats_new.slides import Slide
from whats_new.slides import SlideProps

PY315 = Interpreter.PY315
LAZY_SYNTAX_ERROR = Expect(status=1, output="SyntaxError: invalid syntax")


@component
def section_title(props: SlideProps) -> Div:
    return centered(title_card("Startup and imports", is_live=props.is_live))


@component
def lazy_basics(props: SlideProps) -> Div:
    return notes_beside_code_above_runs(
        props,
        code_example(props, "startup/lazy_basics.py"),
        bullets(
            (code("lazy import x"), plain(", "), code("lazy from x import y")),
            (plain("imported on "), em("first use")),
            (plain("module scope only")),
        ),
    )


@component
def lazy_startup(props: SlideProps) -> Div:
    return Div(
        style=col | fill(1) | gap(1),
        children=(
            labeled("cli_lazy.py (cli_eager.py is the same without lazy)", code_example(props, "startup/cli_lazy.py")),
            run_pane(props),
        ),
    )


@component
def lazy_everything(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_snippet(
            props,
            "python -X lazy_imports=all cli_eager.py  # the unmodified file\n"
            "PYTHON_LAZY_IMPORTS=all python cli_eager.py\n"
            'sys.set_lazy_imports("all")\n'
            "sys.set_lazy_imports_filter(lambda importer, name, fromlist: ...)",
            language="text",
        ),
        bullets(
            (plain("mostly a CLI win, but the switch makes it a "), em("one-flag experiment"), plain(" for any app")),
        ),
    )


@component
def lazy_typo(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "startup/lazy_typo.py"),
        bullets(
            (plain("a typo surfaces at first use, with a chained traceback pointing at both lines")),
            (plain("so do import-time side effects, like a plugin registering itself")),
            (plain("mypy catches the typo before anything runs")),
        ),
    )


@component
def lazy_not_allowed(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "startup/lazy_try.py"),
        bullets(
            (code("lazy"), plain(" inside "), code("try"), plain(" is a "), code("SyntaxError")),
            (plain("so is "), code("lazy from x import *")),
            (plain("under "), code("-X lazy_imports=all"), plain(", both stay eager")),
        ),
    )


@component
def lazy_compat(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "startup/lazy_compat.py"),
        bullets(
            (code("__lazy_modules__"), plain(" names the imports 3.15 makes lazy")),
            (plain("3.14 ignores it, and imports them eagerly")),
        ),
    )


@component
def start_files(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        side_by_side(
            labeled("greet.pth", code_snippet(props, 'import sys; print("hello from greet.pth")', language="text")),
            labeled("greet.start", code_snippet(props, "greet:hello", language="text")),
            labeled("greet/__init__.py", code_snippet(props, 'def hello():\n    print("hello from greet.start")')),
        ),
        bullets(
            (
                plain("bundled fix: 3.14 runs a venv's "),
                code(".pth"),
                plain(" files twice per start (gh-75723, open since 2017)"),
            ),
        ),
    )


@component
def start_flow(props: SlideProps) -> Div:
    return stack(
        site_startup(),
        bullets(
            (
                plain("narrows "),
                em("one"),
                plain(" vector: supply-chain "),
                code("exec()"),
                plain(" via "),
                code(".pth"),
            ),
            (plain("a malicious package can still run code at startup")),
        ),
    )


SLIDES = (
    Slide(title="Startup and imports", content=section_title, is_title_card=True),
    Slide(
        title="Lazy imports",
        content=lazy_basics,
        peps=(810,),
        runs=on_both(
            "startup/lazy_basics.py",
            old=LAZY_SYNTAX_ERROR,
            new=Expect(status=0, output='pathlib/imported\n"pathlib" in sys.modules=True'),
        ),
    ),
    Slide(
        title="Lazy imports: a CLI's --version",
        content=lazy_startup,
        peps=(810,),
        runs=(
            harness(
                "bench.py",
                "--interpreter",
                "python",
                PY315,
                "eager={python} {examples}/startup/cli_eager.py --version",
                "lazy={python} {examples}/startup/cli_lazy.py --version",
                "bare={python} -c pass",
                label="hyperfine",
                expect=Expect(status=0, output="bare"),
            ),
        ),
    ),
    Slide(
        title="Lazy imports, without touching the code",
        content=lazy_everything,
        peps=(810,),
        runs=(
            harness(
                "bench.py",
                "--interpreter",
                "python",
                PY315,
                "eager={python} {examples}/startup/cli_eager.py --version",
                "all lazy={python} -X lazy_imports=all {examples}/startup/cli_eager.py --version",
                "bare={python} -c pass",
                label="hyperfine",
                expect=Expect(status=0, output="all lazy"),
            ),
        ),
    ),
    Slide(
        title="Lazy imports: mistakes show up late",
        content=lazy_typo,
        peps=(810,),
        runs=(python(PY315, "startup/lazy_typo.py", expect=Expect(status=1, output="Did you mean: 'dump'?")),),
    ),
    Slide(
        title="Lazy imports: where they're not allowed",
        content=lazy_not_allowed,
        peps=(810,),
        runs=(
            python(
                PY315,
                "startup/lazy_try.py",
                expect=Expect(status=1, output="lazy import not allowed inside try/except blocks"),
            ),
        ),
    ),
    Slide(
        title="Lazy imports, and still running on 3.14",
        content=lazy_compat,
        peps=(810,),
        runs=on_both(
            "startup/lazy_compat.py",
            old=Expect(status=0, output='"json" in sys.modules=True'),
            new=Expect(status=0, output='"json" in sys.modules=False'),
        ),
    ),
    Slide(
        title=".start files",
        content=start_files,
        peps=(829,),
        runs=on_both(
            "startup/start_files.py",
            old=Expect(status=0, output="hello from greet.pth\n  hello from greet.pth"),
            new=Expect(status=0, output="suppressed due to matching greet.start file"),
        ),
    ),
    Slide(title=".start files: what site.py does", content=start_flow, peps=(829,)),
)
