"""0. Opening: the title, and the deck introducing itself as a Python 3.15 program."""

from counterweight.components import component
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles.utilities import *

from whats_new.components.code import code_example
from whats_new.components.look import bullets
from whats_new.components.look import centered
from whats_new.components.look import code
from whats_new.components.look import dim
from whats_new.components.look import em
from whats_new.components.look import plain
from whats_new.components.look import title_card
from whats_new.components.run_pane import run_pane
from whats_new.runs import Expect
from whats_new.runs import Interpreter
from whats_new.runs import python
from whats_new.slides import Slide
from whats_new.slides import SlideProps


@component
def title(props: SlideProps) -> Div:
    return centered(
        title_card("What's New in Python 3.15", "Josh Karpel"),
        Text(content="a whirlwind tour of how Python is getting better", style=dim),
    )


VERSION_RUNS = (
    python(Interpreter.PY315, "opening/version.py", expect=Expect(status=0, output="3.15.0")),
    python(Interpreter.PY314, "opening/version.py", expect=Expect(status=0, output="3.14.")),
)


@component
def this_deck(props: SlideProps) -> Div:
    return Div(
        style=col | fill(1) | gap(1),
        children=(
            bullets(
                (plain("This deck is a "), em("Python 3.15"), plain(" program, written with counterweight.")),
                (
                    plain("The code on screen is the code that runs: press "),
                    code("1"),
                    plain(", "),
                    code("2"),
                    plain(", ..."),
                ),
            ),
            code_example("opening/version.py"),
            run_pane(props),
        ),
    )


@component
def agenda(props: SlideProps) -> Div:
    return Div(
        style=col | fill(1) | gap(1),
        children=(
            bullets(
                "small things you'll use tomorrow",
                "startup and imports",
                "concurrency",
                "typing",
                "performance, and Tachyon",
                "before you upgrade",
                "a lightning round",
            ),
            Text(
                content=(
                    plain("Watch for features that arrive as "),
                    em("whole toolkits"),
                    plain(", not single functions."),
                ),
            ),
        ),
    )


SLIDES = (
    Slide(title="What's New in Python 3.15", content=title, has_heading=False),
    Slide(title="This deck is a Python 3.15 program", content=this_deck, runs=VERSION_RUNS),
    Slide(title="A whirlwind tour", content=agenda),
)
