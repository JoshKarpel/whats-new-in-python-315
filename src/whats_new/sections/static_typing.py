"""4. Typing: sentinels, TypeForm, closed TypedDicts, and disjoint bases, with mypy run live."""

from importlib.metadata import version

from counterweight.components import component
from counterweight.elements import Div
from counterweight.styles.utilities import *

from whats_new.components.code import code_example
from whats_new.components.layouts import code_above_runs
from whats_new.components.layouts import notes_beside_code_above_runs
from whats_new.components.look import bullets
from whats_new.components.look import centered
from whats_new.components.look import code
from whats_new.components.look import em
from whats_new.components.look import plain
from whats_new.components.look import title_card
from whats_new.runs import Expect
from whats_new.runs import Interpreter
from whats_new.runs import Run
from whats_new.runs import checkers
from whats_new.runs import example
from whats_new.runs import python
from whats_new.slides import Slide
from whats_new.slides import SlideProps

MYPY = f"mypy {version('mypy')}"
"""The deck's own environment's mypy, which `checkers` runs, so a label naming it names the version that runs."""


def old_mypy(release: str, name: str, *mypy_flags: str, expect: Expect) -> Run:
    """
    An older mypy release on the example `name`, fetched by uvx (the image prefetches each one, so it runs offline),
    with the same flags `checkers` passes and `mypy_flags`.
    """
    return Run(
        label=f"mypy {release}",
        argv=(
            "uvx",
            "--from",
            f"mypy=={release}",
            "mypy",
            "--config-file=",
            "--no-incremental",
            "--python-version=3.15",
            *mypy_flags,
            example(name),
        ),
        expect=expect,
    )


@component
def section_title(props: SlideProps) -> Div:
    return centered(title_card("Typing", is_live=props.is_live))


@component
def sentinel_runtime(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "typing/sentinel_runtime.py"),
        bullets(
            "the repr is the name, and it's always truthy",
            (plain("equal only to itself, so never mistaken for "), code("None")),
        ),
    )


@component
def sentinel_naive(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "typing/sentinel_naive.py"),
        bullets(
            (plain("narrowing is "), em("broken"), plain(": "), code("timeout"), plain(" is still "), code("object")),
            (code("timeout=30"), plain(" passes: everything is an object")),
            (plain("and "), code("None"), plain(' already means "wait forever"')),
        ),
    )


@component
def sentinel_enum(props: SlideProps) -> Div:
    return code_above_runs(props, code_example(props, "typing/sentinel_enum.py"))


@component
def sentinel_builtin(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "typing/sentinel.py"),
        bullets(
            (code("timedelta | None | MISSING"), plain(": the sentinel is its own type")),
            (plain("3.14 and earlier: "), code("typing_extensions.Sentinel")),
        ),
    )


@component
def typeform(props: SlideProps) -> Div:
    name = ("typing/validate_type.py", "typing/validate_typeform.py")[props.step]
    return code_above_runs(
        props,
        code_example(props, name),
        bullets(
            (
                code("type[T]"),
                plain(" only accepts classes: not "),
                code("int | None"),
                plain(", "),
                code("Literal[...]"),
            ),
        ),
    )


@component
def closed_typeddict(props: SlideProps) -> Div:
    return notes_beside_code_above_runs(
        props,
        code_example(props, "typing/closed.py", start="class Book"),
        bullets(
            (code("closed=True"), plain(": no keys but the ones declared")),
            (plain("so "), code('"isbn" in item'), plain(" narrows the union "), em("soundly")),
        ),
    )


@component
def extra_items(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "typing/extra_items.py"),
        bullets(
            (code("extra_items=str"), plain(": any other key, as long as its value is a "), code("str")),
            "mypy doesn't support it yet, and rejects valid code",
        ),
    )


@component
def disjoint(props: SlideProps) -> Div:
    return notes_beside_code_above_runs(
        props,
        code_example(props, "typing/disjoint.py"),
        bullets(
            (code("__slots__"), plain(" classes can't share a subclass: their layouts conflict")),
            "mypy 1.17 doesn't know, so it calls the branch reachable",
            (code("@disjoint_base"), plain(": the same, for classes written in C, in stubs")),
        ),
    )


SLIDES = (
    Slide(title="Typing", content=section_title, is_title_card=True),
    Slide(
        title="Sentinels",
        content=sentinel_runtime,
        peps=(661,),
        runs=(
            python(
                Interpreter.PY315,
                "typing/sentinel_runtime.py",
                expect=Expect(status=0, output="MISSING is None=False MISSING == None=False"),
            ),
        ),
    ),
    Slide(
        title="Sentinels, before: object()",
        content=sentinel_naive,
        peps=(661,),
        runs=(
            checkers("typing/sentinel_naive.py", expect=Expect(status=0, output='has no attribute "total_seconds"')),
        ),
    ),
    Slide(
        title="Sentinels, before: the enum trick",
        content=sentinel_enum,
        peps=(661,),
        runs=(checkers("typing/sentinel_enum.py", expect=Expect(status=0, output='"Literal[30]"')),),
    ),
    Slide(
        title="Sentinels, now",
        content=sentinel_builtin,
        peps=(661,),
        runs=(
            old_mypy(
                "2.3.1",
                "typing/sentinel.py",
                expect=Expect(status=1, output='Variable "sentinel.MISSING" is not valid as a type'),
            ),
            checkers(
                "typing/sentinel.py",
                label=MYPY,
                expect=Expect(status=0, output='expected "timedelta | MISSING | None"'),
            ),
        ),
    ),
    Slide(
        title="TypeForm",
        content=typeform,
        peps=(747,),
        steps=2,
        runs=(
            checkers(
                "typing/validate_type.py", label="type[T]", expect=Expect(status=0, output='Revealed type is "Never"')
            ),
            checkers(
                "typing/validate_typeform.py",
                label="TypeForm[T]",
                expect=Expect(status=0, output='Revealed type is "int | None"'),
            ),
        ),
    ),
    Slide(
        title="Closed TypedDicts",
        content=closed_typeddict,
        peps=(728,),
        runs=(checkers("typing/closed.py", expect=Expect(status=0, output='Revealed type is "TypedDict(closed.Book')),),
    ),
    Slide(
        title="TypedDict extra_items",
        content=extra_items,
        peps=(728,),
        runs=(
            checkers(
                "typing/extra_items.py", expect=Expect(status=0, output='Unexpected keyword argument "extra_items"')
            ),
        ),
    ),
    Slide(
        title="Disjoint bases",
        content=disjoint,
        peps=(800,),
        runs=(
            python(
                Interpreter.PY315,
                "typing/disjoint.py",
                label="at runtime",
                expect=Expect(status=1, output="multiple bases have instance lay-out conflict"),
            ),
            old_mypy(
                "1.17.1", "typing/disjoint.py", "--warn-unreachable", expect=Expect(status=0, output="no issues found")
            ),
            checkers(
                "typing/disjoint.py",
                "--warn-unreachable",
                label=MYPY,
                expect=Expect(status=0, output="have distinct disjoint bases"),
            ),
        ),
    ),
)
