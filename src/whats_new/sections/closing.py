"""11. Closing: the features are unusually thorough, and where to read more."""

from counterweight.components import component
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles.utilities import *

from whats_new.components.layouts import stack
from whats_new.components.look import bullets
from whats_new.components.look import centered
from whats_new.components.look import claude_mascot
from whats_new.components.look import code
from whats_new.components.look import link
from whats_new.components.look import made_with_claude
from whats_new.components.look import plain
from whats_new.components.look import title_card
from whats_new.slides import Slide
from whats_new.slides import SlideProps

TOOLKITS = (
    (code("threading"), plain(": serialize_iterator, synchronized_iterator, concurrent_tee")),
    (code("unicodedata"), plain(": iter_graphemes and five related property functions")),
    (code("base64"), plain(": C rewrites, and padded=, canonical=, wrapcol=, alphabet=")),
    (plain("lazy imports: syntax, -X/env/sys switches, a filter hook, "), code("__lazy_modules__")),
    "Tachyon: a dozen output formats, a live TUI, async awareness, attach, dump, replay",
    (code("frozendict"), plain(": copy, json, pickle, pprint, marshal, eval globals, type() all accept it")),
    "color in about 20 command-line interfaces",
)


@component
def thoroughness(props: SlideProps) -> Div:
    return stack(
        Text(content="Features arrived as complete toolkits:"),
        bullets(*TOOLKITS),
    )


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


SLIDES = (
    Slide(title="Unusually thorough", content=thoroughness),
    Slide(title="Thanks", content=thanks, is_title_card=True),
)
