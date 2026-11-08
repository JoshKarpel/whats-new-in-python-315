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
def asked(props: SlideProps) -> Div:
    return stack(
        bullets(
            (
                plain('"Until such a PEP is accepted, we ask that no new development on the JIT land on main" '),
                attributed(STEERING_COUNCIL, REQUEST),
            ),
            (
                plain('"five questions: who maintains this, how does it interact with the features and tools CPython '),
                plain("already supports, what are the measurable goals, how does it relate to other JITs, "),
                plain('and is the architecture stable" '),
                attributed("Pablo Galindo Salgado", PABLO),
            ),
            (
                plain('"how it will impact maintainers and contributors that don\'t directly contribute to the JIT" '),
                attributed(STEERING_COUNCIL, REQUEST),
            ),
            (
                plain('"collectively we (the Steering Council) have not been as strict about following the process '),
                plain('as a change of this complexity and reach deserves" '),
                attributed(STEERING_COUNCIL, REQUEST),
            ),
        ),
    )


THREAD = (
    (
        plain('"There is already murmur on the web that the SC killed the JIT by abusing the bureaucratic '),
        plain('PEP process" '),
        attributed("a post on the PEP's thread", f"{PEP_836_THREAD}/68"),
    ),
    (
        plain('"The SC has not killed the JIT. The SC has not rejected PEP 836." '),
        plain('"Holding that bar it\'s literally the damn job." '),
        attributed("Pablo Galindo Salgado", PABLO),
    ),
    (
        plain("\"Our bandwidths changed. It didn't feel reasonable to put up a PEP that we couldn't commit to.\" "),
        attributed("Savannah Ostrowski", f"{PEP_836_THREAD}/76"),
    ),
    (
        plain('"it feels like a funding decision reaching its natural consequence" '),
        attributed("Alyssa Coghlan", f"{PEP_836_THREAD}/79"),
    ),
)
"""
The PEP 836 thread after the withdrawal, in the order the posts came, revealed one per step.
The first poster isn't named on the slide: the point is the rumor, not who repeated it.
"""


@component
def thread(props: SlideProps) -> Div:
    return stack(bullets(*THREAD[: props.step + 1]))


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
    Slide(title="The JIT saga: what the Steering Council asked", content=asked),
    Slide(title="The JIT saga: the thread", content=thread, peps=(836,), steps=len(THREAD)),
    Slide(title="Three experiments", content=three_experiments, peps=(703, 744, 836, 848)),
)
