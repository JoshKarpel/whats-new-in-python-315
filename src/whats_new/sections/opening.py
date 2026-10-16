"""0. Opening: the title, and the tour ahead."""

from counterweight.components import component
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles.utilities import *

from whats_new.components.layouts import stack
from whats_new.components.look import bullets
from whats_new.components.look import centered
from whats_new.components.look import dim
from whats_new.components.look import em
from whats_new.components.look import made_with_claude
from whats_new.components.look import plain
from whats_new.components.look import title_card
from whats_new.slides import Slide
from whats_new.slides import SlideProps
from whats_new.slides import TitleCard


@component
def title(props: SlideProps) -> Div:
    return centered(
        title_card("What's New in Python 3.15", "Josh Karpel", "MadPy, November 2026", is_live=props.is_live),
        Text(content="a whirlwind tour of how Python is getting better", style=dim),
        # Further down than the rest, set apart as a footnote to the title rather than part of it.
        Div(style=margin_top(2), children=(made_with_claude(props.is_live),)),
    )


@component
def agenda(props: SlideProps) -> Div:
    return stack(
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
    )


SLIDES = (
    Slide(title="What's New in Python 3.15", content=title, title_card=TitleCard.SECTION),
    Slide(title="A whirlwind tour", content=agenda),
)
