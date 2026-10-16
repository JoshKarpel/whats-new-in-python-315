"""1. Small things you'll use tomorrow: frozendict, json's array_hook, unpacking in comprehensions, and friends."""

from counterweight.components import component
from counterweight.elements import Div
from counterweight.styles.utilities import *

from whats_new.components.code import code_example
from whats_new.components.layouts import code_above_runs
from whats_new.components.layouts import notes_beside_code_above_runs
from whats_new.components.layouts import stack
from whats_new.components.look import bullets
from whats_new.components.look import centered
from whats_new.components.look import code
from whats_new.components.look import em
from whats_new.components.look import plain
from whats_new.components.look import title_card
from whats_new.diagrams import frozendict_hierarchy
from whats_new.diagrams.graphemes import LAYER_STEPS
from whats_new.diagrams.graphemes import band_code_points
from whats_new.diagrams.graphemes import layers
from whats_new.diagrams.take_bytes import take_bytes_memory
from whats_new.runs import Expect
from whats_new.runs import Interpreter
from whats_new.runs import on_both
from whats_new.runs import python
from whats_new.slides import Slide
from whats_new.slides import SlideProps
from whats_new.slides import TitleCard

PY315 = Interpreter.PY315


@component
def section_title(props: SlideProps) -> Div:
    return centered(title_card("Small things you'll use tomorrow", is_live=props.is_live))


@component
def frozendict_basics(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "small/frozendict_basics.py"),
        bullets(
            (plain("a builtin, immutable "), em("mapping")),
            (plain("hashable when its values are")),
            (plain("no literal syntax (yet) 😭")),
        ),
    )


@component
def mutable_default(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "small/mutable_default.py"),
        bullets(
            (plain("the default is "), em("one"), plain(" dict, made once, shared by every call")),
        ),
    )


@component
def frozendict_default(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "small/frozendict_default.py"),
        bullets((plain("a default that can't be mutated by accident"),)),
    )


@component
def frozendict_cache(props: SlideProps) -> Div:
    return notes_beside_code_above_runs(
        props,
        code_example(props, "small/frozendict_cache.py"),
        bullets(
            (plain("a mapping argument that "), code("@cache"), plain(" can key on")),
        ),
    )


@component
def frozendict_subclass(props: SlideProps) -> Div:
    return stack(frozendict_hierarchy.frozendict_hierarchy(props.step))


@component
def json_immutable(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "small/json_immutable.py"),
        bullets(
            (plain("new: "), code("array_hook="), plain(" on "), code("load"), plain(", "), code("loads")),
            (plain("immutable all the way down")),
        ),
    )


@component
def unpacking(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "small/unpack.py"),
        bullets(
            (code("[*row for row in rows]"),),
            (plain("instead of "), code("list(chain.from_iterable(rows))")),
        ),
    )


@component
def unpacking_pages(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "small/unpack_pages.py", start="async def"),
        bullets("an async stream of sync batches: a paginated API"),
    )


@component
def unpacking_sources(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "small/unpack_sources.py", start="async def"),
        bullets(
            (plain("what's after "), code("*"), plain(" must be a "), em("sync"), plain(" iterable")),
        ),
    )


@component
def unpacking_nested(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "small/unpack_sources_nested.py", start="async def"),
        bullets("flattening async sources takes two async fors, as it did before 3.15"),
    )


@component
def counter_xor(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "small/counter_xor.py"),
        bullets(
            (code("c ^ d"), plain(" is "), code("|c[x] - d[x]|"), plain(" for every key: "), code("(c - d) + (d - c)")),
            (plain("unsigned, so for questions where direction doesn't matter")),
        ),
    )


@component
def take_bytes_peak(props: SlideProps) -> Div:
    return notes_beside_code_above_runs(props, code_example(props, "small/take_bytes_memory.py"), take_bytes_memory())


@component
def text_layers(props: SlideProps) -> Div:
    return stack(layers(props.step))


@component
def graphemes(props: SlideProps) -> Div:
    return code_above_runs(
        props,
        code_example(props, "small/graphemes.py"),
        bullets(
            (code("!a"), plain(" prints the umlaut as "), code("\\u0308"), plain(": see the next slide for why")),
        ),
    )


@component
def grapheme_picture(props: SlideProps) -> Div:
    return stack(
        band_code_points(),
        bullets(
            (
                plain("zellij, which this talk runs through, "),
                em("drops"),
                plain(" combining marks (zellij#5500): segmentation is hard"),
            ),
            (
                plain("counterweight, which draws this deck, segments with "),
                code("iter_graphemes"),
                plain(" and measures with "),
                code("wcwidth"),
            ),
        ),
    )


SLIDES = (
    Slide(title="Small things you'll use tomorrow", content=section_title, title_card=TitleCard.SECTION),
    Slide(
        title="frozendict",
        content=frozendict_basics,
        peps=(814,),
        runs=(
            python(
                Interpreter.PY315,
                "small/frozendict_basics.py",
                expect=Expect(status=1, output="'frozendict' object does not support item assignment"),
            ),
        ),
    ),
    Slide(
        title="The mutable default argument",
        content=mutable_default,
        runs=(
            python(
                PY315,
                "small/mutable_default.py",
                expect=Expect(status=0, output="DEFAULTS={'retries': 3, 'timeout': 10.0, 'url': 'https://python.org'}"),
            ),
        ),
    ),
    Slide(
        title="frozendict: the mutable default, fixed",
        content=frozendict_default,
        peps=(814,),
        runs=(
            python(
                Interpreter.PY315,
                "small/frozendict_default.py",
                expect=Expect(status=0, output="frozendict({'retries': 3, 'timeout': 10.0})"),
            ),
        ),
    ),
    Slide(
        title="frozendict: a cache key",
        content=frozendict_cache,
        peps=(814,),
        runs=(
            python(
                Interpreter.PY315,
                "small/frozendict_cache.py",
                expect=Expect(status=1, output="TypeError: unhashable type: 'dict'"),
            ),
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
        runs=(
            python(
                Interpreter.PY315,
                "small/json_immutable.py",
                expect=Expect(status=0, output="frozendict({'name': 'Ada', 'tags': ('math', 'poetry')})"),
            ),
        ),
    ),
    Slide(
        title="Unpacking in comprehensions",
        content=unpacking,
        peps=(798,),
        runs=on_both(
            "small/unpack.py",
            old=Expect(status=1, output="SyntaxError: iterable unpacking cannot be used in comprehension"),
            new=Expect(status=0, output="{'debug': True, 'port': 80}"),
        ),
    ),
    Slide(
        title="Unpacking in async comprehensions",
        content=unpacking_pages,
        peps=(798,),
        runs=(python(PY315, "small/unpack_pages.py", expect=Expect(status=0, output="[1, 2, 3, 4, 5, 6]")),),
    ),
    Slide(
        title="Unpacking async sources: not like that",
        content=unpacking_sources,
        peps=(798,),
        runs=(
            python(
                PY315,
                "small/unpack_sources.py",
                expect=Expect(status=1, output="Value after * must be an iterable, not async_generator"),
            ),
        ),
    ),
    Slide(
        title="Unpacking async sources: like this",
        content=unpacking_nested,
        peps=(798,),
        runs=(python(PY315, "small/unpack_sources_nested.py", expect=Expect(status=0, output="[0, 1, 0, 1, 2]")),),
    ),
    Slide(
        title="Counter ^ Counter",
        content=counter_xor,
        runs=(python(Interpreter.PY315, "small/counter_xor.py", expect=Expect(status=0, output="4")),),
    ),
    Slide(
        title="bytearray.take_bytes: half the peak",
        content=take_bytes_peak,
        runs=(python(PY315, "small/take_bytes_memory.py", expect=Expect(status=0, output="take_bytes: peak 50 MiB")),),
    ),
    Slide(title="Text, in layers", content=text_layers, steps=LAYER_STEPS),
    Slide(
        title="unicodedata.iter_graphemes",
        content=graphemes,
        runs=(
            python(
                Interpreter.PY315,
                "small/graphemes.py",
                expect=Expect(status=0, output="band[::-1]='paT la\\u0308nipS'"),
            ),
        ),
    ),
    Slide(title="One grapheme, two code points", content=grapheme_picture),
)
