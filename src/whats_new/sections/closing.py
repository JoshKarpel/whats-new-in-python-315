"""8. Closing: the features are unusually thorough, a question about why, and where to read more."""

from counterweight.components import component
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.styles.utilities import *

from whats_new.components.layouts import stack
from whats_new.components.look import bullets
from whats_new.components.look import centered
from whats_new.components.look import code
from whats_new.components.look import em
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
        Text(content="Features arrived as toolkits, not single functions:"),
        bullets(*TOOLKITS),
        Text(
            content=(
                plain("Do coding agents make this kind of completeness cheaper? "),
                em("A question, not a claim."),
            ),
        ),
    )


@component
def thanks(props: SlideProps) -> Div:
    return centered(
        title_card("Thanks!"),
        bullets(
            "docs.python.org/3.15/whatsnew/3.15.html",
            "github.com/JoshKarpel/whats-new-in-python-315",
            "github.com/JoshKarpel/counterweight",
        ),
    )


SLIDES = (
    Slide(title="Unusually thorough", content=thoroughness),
    Slide(title="Thanks", content=thanks, has_heading=False),
)
