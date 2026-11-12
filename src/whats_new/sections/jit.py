"""
8. The JIT saga: the experimental JIT's years on main behind a build flag, the Steering Council's request for a PEP,
and the PEP's withdrawal, ending beside the garbage collector and free-threading.
What the performance section shows the JIT doing, this tells the story of.

Like the garbage collector saga, what went wrong comes only from what core developers and the Steering Council
said in public, quoted and attributed.
"""

from counterweight.components import component
from counterweight.elements import Div

from whats_new.components.layouts import stack
from whats_new.components.look import attributed
from whats_new.components.look import bullets
from whats_new.components.look import centered
from whats_new.components.look import code
from whats_new.components.look import plain
from whats_new.components.look import title_card
from whats_new.diagrams import jit
from whats_new.slides import Slide
from whats_new.slides import SlideProps

STEERING_COUNCIL = "the Steering Council"
REQUEST = "https://discuss.python.org/t/an-announcement-from-the-steering-council-regarding-the-jit-project/107638"
"""The Steering Council's request for a PEP, 2026-06-05, and its thread."""
PEP_836_THREAD = (
    "https://discuss.python.org/t/pep-836-jit-go-brrr-the-path-to-a-supported-jit-compiler-for-cpython/108010"
)
PABLO = f"{PEP_836_THREAD}/75"
"""Pablo Galindo Salgado's answer to the rumor that the Steering Council killed the JIT."""


@component
def section_title(props: SlideProps) -> Div:
    return centered(title_card("The JIT saga", is_live=props.is_live))


@component
def on_main(props: SlideProps) -> Div:
    return stack(
        jit.designs(props.step, props.is_live),
        bullets(
            (plain("behind a build flag: built in and off, "), code("PYTHON_JIT=1"), plain(" opts in")),
            "the speedups are PEP 836's own account",
            (
                plain('"Every one of those reached into the interpreter that every core developer, tool author and '),
                plain('distributor depends on, none of it went through a PEP" '),
                attributed("Pablo Galindo Salgado", PABLO),
            ),
        ),
    )


@component
def request(props: SlideProps) -> Div:
    return stack(
        jit.request(props.step, props.is_live),
        bullets(
            (
                plain('"experiments should not be done on the main branch of CPython without a backing PEP" '),
                attributed(STEERING_COUNCIL, REQUEST),
            ),
            (
                plain('3.15 ships it: "we wanted to be clear that we\'re okay with the status quo for 3.15" '),
                attributed("Thomas Wouters", f"{REQUEST}/4"),
            ),
        ),
    )


@component
def three_experiments(props: SlideProps) -> Div:
    return stack(
        jit.experiments(),
        bullets(
            "all three reached into the interpreter everyone works on",
            "only free-threading agreed what that would cost everyone else first, in a PEP",
        ),
    )


SLIDES = (
    Slide(title="The JIT saga", content=section_title, is_title_card=True),
    Slide(
        title="The JIT saga: on main",
        content=on_main,
        peps=(744, 836),
        steps=jit.DESIGN_STEPS,
        ends_showing=jit.designs_ends_showing,
    ),
    Slide(
        title="The JIT saga: a PEP, or out",
        content=request,
        peps=(836,),
        steps=jit.REQUEST_STEPS,
        ends_showing=jit.request_ends_showing,
    ),
    Slide(title="Three experiments", content=three_experiments, peps=(703, 744, 836, 848)),
)
