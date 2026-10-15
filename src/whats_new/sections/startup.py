"""2. Startup and imports: lazy imports, and .start files."""

from counterweight.components import component
from counterweight.elements import Div
from counterweight.styles.utilities import *

from whats_new.components.code import code_example
from whats_new.components.code import code_snippet
from whats_new.components.code import labeled
from whats_new.components.layouts import code_above_runs
from whats_new.components.layouts import code_beside_runs
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
PY314 = Interpreter.PY314
LAZY_SYNTAX_ERROR = Expect(status=1, output="SyntaxError: invalid syntax")


@component
def section_title(props: SlideProps) -> Div:
    return centered(title_card("Startup and imports"))


@component
def lazy_basics(props: SlideProps) -> Div:
    return code_beside_runs(
        props,
        code_example("startup/lazy_basics.py"),
        bullets(
            (code("lazy import x"), plain(", "), code("lazy from x import y")),
            (plain("module scope only")),
            (plain("imported on "), em("first use")),
        ),
    )


@component
def lazy_startup(props: SlideProps) -> Div:
    return Div(
        style=col | fill(1) | gap(1),
        children=(
            labeled("cli_lazy.py (cli_eager.py is the same without lazy)", code_example("startup/cli_lazy.py")),
            run_pane(props),
        ),
    )


@component
def lazy_everything(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_snippet(
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
        code_example("startup/lazy_typo.py"),
        bullets(
            (plain("a typo surfaces at first use, with a chained traceback pointing at both lines")),
        ),
    )


@component
def lazy_gotchas(props: SlideProps) -> Div:
    return Div(
        style=row | fill(1) | gap(1),
        children=(
            Div(
                style=col | gap(1) | shrink(0),
                children=(
                    code_example("startup/lazy_try.py"),
                    code_example("startup/lazy_compat.py"),
                    bullets(
                        (plain("a plain import in "), code("try"), plain(" stays eager, even in "), code("all")),
                        (code("lazy from x import *"), plain(" is a "), code("SyntaxError")),
                        (plain("import-time side effects (plugin registration) break")),
                    ),
                ),
            ),
            run_pane(props, vertical=True),
        ),
    )


@component
def start_files(props: SlideProps) -> Div:
    return Div(
        style=col | fill(1) | gap(1),
        children=(
            Div(
                style=row | gap(1),
                children=(
                    labeled("greet.pth", code_snippet('import sys; print("hello from greet.pth")', language="text")),
                    labeled("greet.start", code_snippet("greet:hello", language="text")),
                    labeled("greet/__init__.py", code_snippet('def hello():\n    print("hello from greet.start")')),
                ),
            ),
            run_pane(props),
        ),
    )


@component
def start_flow(props: SlideProps) -> Div:
    return Div(
        style=col | fill(1) | gap(1),
        children=(
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
        ),
    )


SLIDES = (
    Slide(title="Startup and imports", content=section_title, has_heading=False),
    Slide(
        title="Lazy imports",
        content=lazy_basics,
        peps=(810,),
        runs=on_both(
            "startup/lazy_basics.py", new=Expect(status=0, output="<lazy_import 'json'>"), old=LAZY_SYNTAX_ERROR
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
            harness(
                "import_count.py",
                PY315,
                "startup/cli_eager.py",
                "startup/cli_lazy.py",
                label="-X importtime",
                expect=Expect(status=0, output="cli_eager.py:"),
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
        title="Lazy imports: gotchas",
        content=lazy_gotchas,
        peps=(810,),
        runs=(
            python(
                PY315,
                "startup/lazy_try.py",
                label="try",
                expect=Expect(status=1, output="lazy import not allowed inside try/except blocks"),
            ),
            python(
                PY315,
                "startup/lazy_compat.py",
                label="compat 3.15",
                expect=Expect(status=0, output="json loaded: False"),
            ),
            python(
                PY314,
                "startup/lazy_compat.py",
                label="compat 3.14",
                expect=Expect(status=0, output="json loaded: True"),
            ),
        ),
    ),
    Slide(
        title=".start files",
        content=start_files,
        peps=(829,),
        runs=on_both(
            "startup/start_files.py",
            new=Expect(status=0, output="suppressed due to matching greet.start file"),
            old=Expect(status=0, output="hello from greet.pth"),
        ),
    ),
    Slide(title=".start files: what site.py does", content=start_flow, peps=(829,)),
)
