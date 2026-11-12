"""11. Closing: thanks, and where to read more."""

from counterweight.components import component
from counterweight.elements import Div
from counterweight.styles.utilities import *

from whats_new.components.look import bullets
from whats_new.components.look import centered
from whats_new.components.look import claude_mascot
from whats_new.components.look import link
from whats_new.components.look import made_with_claude
from whats_new.components.look import plain
from whats_new.components.look import title_card
from whats_new.slides import Slide
from whats_new.slides import SlideProps


@component
def thanks(props: SlideProps) -> Div:
    return centered(
        title_card("Thanks!", is_live=props.is_live),
        bullets(
            (plain("what's new:     "), link("https://docs.python.org/3.15/whatsnew/3.15.html")),
            (plain("this talk:      "), link("https://github.com/JoshKarpel/whats-new-in-python-315")),
            (plain("counterweight:  "), link("https://github.com/JoshKarpel/counterweight")),
        ),
        Div(
            style=row | gap_width(2) | align_children_center | margin_top(2),
            children=(claude_mascot(), made_with_claude(props.is_live)),
        ),
    )


SLIDES = (Slide(title="Thanks", content=thanks, is_title_card=True),)
