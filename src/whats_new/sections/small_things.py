"""1. Small things you'll use tomorrow: frozendict, json's array_hook, unpacking in comprehensions, and friends."""

from counterweight.components import component
from counterweight.elements import Div
from counterweight.styles.utilities import *

from whats_new.components.code import code_example
from whats_new.components.layouts import code_above_runs
from whats_new.components.layouts import code_beside_runs
from whats_new.components.layouts import stack
from whats_new.components.look import bullets
from whats_new.components.look import centered
from whats_new.components.look import code
from whats_new.components.look import em
from whats_new.components.look import plain
from whats_new.components.look import title_card
from whats_new.components.run_pane import run_pane
from whats_new.diagrams import frozendict_hierarchy
from whats_new.diagrams.graphemes import family_code_points
from whats_new.diagrams.take_bytes import take_bytes_memory
from whats_new.runs import Expect
from whats_new.runs import Interpreter
from whats_new.runs import on_both
from whats_new.runs import python
from whats_new.slides import Slide
from whats_new.slides import SlideProps

PY315 = Interpreter.PY315


NO_FROZENDICT = Expect(status=1, output="NameError: name 'frozendict' is not defined")


@component
def section_title(props: SlideProps) -> Div:
    return centered(title_card("Small things you'll use tomorrow"))


@component
def frozendict_basics(props: SlideProps) -> Div:
    return code_beside_runs(
        props,
        code_example("small/frozendict_basics.py"),
        bullets(
            (plain("a builtin, immutable "), em("mapping")),
            (plain("hashable when its values are")),
            (plain("no literal syntax (yet)")),
        ),
    )


@component
def frozendict_default(props: SlideProps) -> Div:
    return code_beside_runs(
        props,
        code_example("small/frozendict_default.py"),
        bullets((plain("a default that can't be mutated by accident"),)),
    )


@component
def frozendict_cache(props: SlideProps) -> Div:
    return code_beside_runs(
        props,
        code_example("small/frozendict_cache.py"),
        bullets(
            (plain("a mapping argument that "), code("@cache"), plain(" can key on")),
        ),
    )


@component
def frozendict_subclass(props: SlideProps) -> Div:
    return stack(frozendict_hierarchy.frozendict_hierarchy(props.step))


@component
def json_immutable(props: SlideProps) -> Div:
    return code_beside_runs(
        props,
        code_example("small/json_immutable.py"),
        bullets(
            (plain("new: "), code("array_hook="), plain(" on "), code("load"), plain(", "), code("loads")),
            (plain("immutable all the way down")),
        ),
    )


@component
def unpacking(props: SlideProps) -> Div:
    return code_beside_runs(
        props,
        code_example("small/unpack.py"),
        bullets(
            (code("[*row for row in rows]"),),
            (plain("instead of "), code("list(chain.from_iterable(rows))")),
        ),
    )


UNPACK_FILES = ("small/unpack_pages.py", "small/unpack_sources.py", "small/unpack_sources_nested.py")


@component
def unpacking_async(props: SlideProps) -> Div:
    return code_beside_runs(props, code_example(UNPACK_FILES[props.step], start="async def"))


@component
def counter_xor(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example("small/counter_xor.py"),
        bullets(
            (code("c ^ d"), plain(" is "), code("|c[x] - d[x]|"), plain(" for every key: "), code("(c - d) + (d - c)")),
            (plain("unsigned, so for questions where direction doesn't matter")),
        ),
    )


@component
def take_bytes(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example("small/take_bytes.py"),
        bullets(
            (plain("the buffer becomes "), code("bytes"), plain(" without a copy")),
        ),
    )


@component
def take_bytes_peak(props: SlideProps) -> Div:
    return Div(
        style=row | fill(1) | gap(1),
        children=(
            Div(
                style=col | gap(1) | shrink(0),
                children=(code_example("small/take_bytes_memory.py"),),
            ),
            Div(
                style=col | fill(1) | gap(1),
                children=(take_bytes_memory(), run_pane(props)),
            ),
        ),
    )


@component
def graphemes(props: SlideProps) -> Div:
    return code_above_runs(props, code_example("small/graphemes.py"))


@component
def grapheme_picture(props: SlideProps) -> Div:
    return stack(
        family_code_points(),
        bullets(
            "counterweight segments text with iter_graphemes: this deck is the code under discussion",
            (
                plain("and still measures width with "),
                code("wcwidth"),
                plain(": the stdlib doesn't measure terminal cells"),
            ),
        ),
    )


SLIDES = (
    Slide(title="Small things you'll use tomorrow", content=section_title, has_heading=False),
    Slide(
        title="frozendict",
        content=frozendict_basics,
        peps=(814,),
        runs=on_both(
            "small/frozendict_basics.py",
            new=Expect(status=1, output="'frozendict' object does not support item assignment"),
            old=NO_FROZENDICT,
        ),
    ),
    Slide(
        title="frozendict: the mutable default, fixed",
        content=frozendict_default,
        peps=(814,),
        runs=on_both(
            "small/frozendict_default.py",
            new=Expect(status=0, output="frozendict({'retries': 3, 'timeout': 10.0})"),
            old=NO_FROZENDICT,
        ),
    ),
    Slide(
        title="frozendict: a cache key",
        content=frozendict_cache,
        peps=(814,),
        runs=on_both(
            "small/frozendict_cache.py",
            new=Expect(status=1, output="TypeError: unhashable type: 'dict'"),
            old=NO_FROZENDICT,
        ),
    ),
    Slide(
        title="Why isn't frozendict a dict?",
        content=frozendict_subclass,
        peps=(814,),
        steps=frozendict_hierarchy.STEPS,
    ),
    Slide(
        title="json: immutable all the way down",
        content=json_immutable,
        peps=(814,),
        runs=on_both(
            "small/json_immutable.py",
            new=Expect(status=0, output="frozendict({'name': 'Ada', 'tags': ('math', 'poetry')})"),
            old=NO_FROZENDICT,
        ),
    ),
    Slide(
        title="Unpacking in comprehensions",
        content=unpacking,
        peps=(798,),
        runs=on_both(
            "small/unpack.py",
            new=Expect(status=0, output="{'debug': True, 'port': 80}"),
            old=Expect(status=1, output="SyntaxError: iterable unpacking cannot be used in comprehension"),
        ),
    ),
    Slide(
        title="Unpacking in async comprehensions",
        content=unpacking_async,
        peps=(798,),
        steps=len(UNPACK_FILES),
        runs=(
            python(PY315, UNPACK_FILES[0], label="pages", expect=Expect(status=0, output="[1, 2, 3, 4, 5, 6]")),
            python(
                PY315,
                UNPACK_FILES[1],
                label="sources",
                expect=Expect(status=1, output="Value after * must be an iterable, not async_generator"),
            ),
            python(PY315, UNPACK_FILES[2], label="nested", expect=Expect(status=0, output="[0, 1, 0, 1, 2]")),
        ),
    ),
    Slide(
        title="Counter ^ Counter",
        content=counter_xor,
        runs=on_both(
            "small/counter_xor.py",
            new=Expect(status=0, output="4"),
            old=Expect(status=1, output="unsupported operand type(s) for ^: 'Counter' and 'Counter'"),
        ),
    ),
    Slide(
        title="bytearray.take_bytes",
        content=take_bytes,
        runs=on_both(
            "small/take_bytes.py",
            new=Expect(status=0, output="b'HTTP/1.1 200 OK\\r\\n'"),
            old=Expect(status=1, output="'bytearray' object has no attribute 'take_bytes'"),
        ),
    ),
    Slide(
        title="bytearray.take_bytes: half the peak",
        content=take_bytes_peak,
        runs=(python(PY315, "small/take_bytes_memory.py", expect=Expect(status=0, output="take: peak 50 MiB")),),
    ),
    Slide(
        title="unicodedata.iter_graphemes",
        content=graphemes,
        runs=on_both(
            "small/graphemes.py",
            new=Expect(status=0, output="7 1"),
            old=Expect(status=1, output="cannot import name 'iter_graphemes' from 'unicodedata'"),
        ),
    ),
    Slide(title="One grapheme, seven code points", content=grapheme_picture),
)
