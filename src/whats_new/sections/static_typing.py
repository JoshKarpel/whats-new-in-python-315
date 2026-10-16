"""4. Typing: sentinels, TypeForm, closed TypedDicts, and disjoint bases, with every checker run live."""

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

OLD_MYPY = Run(
    label="mypy 2.3.1",
    argv=(
        "uvx",
        "--from",
        "mypy==2.3.1",
        "mypy",
        "--config-file=",
        "--no-incremental",
        "--python-version=3.15",
        example("typing/sentinel.py"),
    ),
    expect=Expect(status=1, output='Variable "sentinel.MISSING" is not valid as a type'),
)


@component
def section_title(props: SlideProps) -> Div:
    return centered(
        title_card("Typing"),
        bullets("run live with mypy: pyright and ty agree, except where a slide says otherwise"),
    )


@component
def sentinel_runtime(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "typing/sentinel_runtime.py"),
        bullets(
            "the repr is the name, and it's always truthy",
            "copies are itself, and it pickles by name",
        ),
    )


@component
def sentinel_naive(props: SlideProps) -> Div:
    return notes_beside_code_above_runs(
        props,
        code_example(props, "typing/sentinel_naive.py"),
        bullets(
            (plain("narrowing is "), em("broken"), plain(": "), code("name"), plain(" is still "), code("object")),
            (code("greet(42)"), plain(" passes: everything is an object")),
        ),
    )


@component
def sentinel_enum(props: SlideProps) -> Div:
    return code_above_runs(props, code_example(props, "typing/sentinel_enum.py"))


@component
def sentinel_builtin(props: SlideProps) -> Div:
    return notes_beside_code_above_runs(
        props,
        code_example(props, "typing/sentinel.py"),
        bullets(
            (code("str | MISSING"), plain(": the sentinel is its own type")),
            (plain("3.14 and earlier: "), code("typing_extensions.Sentinel")),
        ),
    )


@component
def typeform(props: SlideProps) -> Div:
    name = ("typing/validate_type.py", "typing/validate_typeform.py")[props.step]
    return code_above_runs(
        props,
        code_example(props, name, stop="reveal_type"),
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
def closed_assignment(props: SlideProps) -> Div:
    return notes_beside_code_above_runs(
        props,
        code_example(props, "typing/closed_assign.py", start="class Book"),
        bullets(
            (plain("closed: a "), code("Hardback"), plain(" has an extra key, so it isn't a "), code("Book")),
            (plain('open TypedDicts allowed this "wider" assignment')),
        ),
    )


@component
def extra_items(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "typing/extra_items.py"),
        bullets(
            (code("extra_items=str"), plain(": any other key, as long as its value is a "), code("str")),
            "mypy doesn't support it yet, and rejects valid code; pyright and ty do",
        ),
    )


@component
def disjoint(props: SlideProps) -> Div:
    return notes_beside_code_above_runs(
        props,
        code_example(props, "typing/disjoint.py", start="@dataclass"),
        bullets(
            (code("slots=True"), plain(" classes can't share a subclass")),
            "pyright and ty flag the class, not the branch",
            (code("@disjoint_base"), plain(" is mostly for stubs")),
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
                expect=Expect(status=1, output="type 'sentinel' is not an acceptable base type"),
            ),
        ),
    ),
    Slide(
        title="Sentinels, before: object()",
        content=sentinel_naive,
        peps=(661,),
        runs=(checkers("typing/sentinel_naive.py", expect=Expect(status=0, output='has no attribute "upper"')),),
    ),
    Slide(
        title="Sentinels, before: the enum trick",
        content=sentinel_enum,
        peps=(661,),
        runs=(checkers("typing/sentinel_enum.py", expect=Expect(status=0, output="Literal[42]")),),
    ),
    Slide(
        title="Sentinels, now",
        content=sentinel_builtin,
        peps=(661,),
        runs=(OLD_MYPY, checkers("typing/sentinel.py", expect=Expect(status=0, output='expected "str | MISSING"'))),
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
        title="Closed TypedDicts: no extra keys",
        content=closed_assignment,
        peps=(728,),
        runs=(
            checkers(
                "typing/closed_assign.py",
                expect=Expect(status=0, output='expression has type "Hardback", variable has'),
            ),
        ),
    ),
    Slide(
        title="TypedDict extra_items",
        content=extra_items,
        peps=(728,),
        runs=(
            checkers(
                "typing/extra_items.py", expect=Expect(status=0, output='Unexpected keyword argument "extra_items"')
            ),
            checkers(
                "typing/extra_items.py",
                tools=("pyright",),
                expect=Expect(status=0, output="Could not assign item in TypedDict"),
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
            checkers(
                "typing/disjoint.py",
                "--warn-unreachable",
                label="mypy --warn-unreachable",
                expect=Expect(status=0, output="Statement is unreachable"),
            ),
            checkers(
                "typing/disjoint_control.py",
                "--warn-unreachable",
                label="without slots=True",
                expect=Expect(status=0, output="no issues"),
            ),
        ),
    ),
)
