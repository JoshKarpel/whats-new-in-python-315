"""The deck's palette and the small styled pieces every section uses: headings, bullets, title cards."""

from datetime import timedelta

from counterweight.components import Component
from counterweight.components import component
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
from counterweight.gradients import ConicGradient
from counterweight.gradients import LinearGradient
from counterweight.gradients import conic_gradient
from counterweight.gradients import linear_gradient
from counterweight.styles import CellStyle
from counterweight.styles import Color
from counterweight.styles import Style
from counterweight.styles.utilities import *

from whats_new.components.animation import use_loop

PYTHON_BLUE = Color.from_hex("#4B8BBE")
PYTHON_YELLOW = Color.from_hex("#FFD43B")
CLAUDE_ORANGE = Color.from_hex("#D77757")
"""The orange Claude Code draws its spark and mascot in."""
CLAUDE_SHIMMER = Color.from_hex("#EB9F7F")
"""The lighter orange of the shimmer Claude Code sweeps across its spinner's message."""

CLAUDE_SPARK = "✻"
SPARK_CYCLE = ("·", "✢", "*", "✶", "✻", "✽", "✽", "✻", "✶", "*", "✢", "·")
"""The glyphs Claude Code's spinner steps through, out to the full spark and back."""
SPARK_STEP = timedelta(milliseconds=120)
SHIMMER_WIDTH = 4
"""How many cells either side of the shimmer's center it lightens, fading out."""
CREDIT = "built with help from Claude Code"
CREDIT_PERIOD = SPARK_STEP * len(SPARK_CYCLE) * 2
"""Two turns of the spark to one sweep of the shimmer, so one loop drives both."""
CLAUDE_MASCOT = " ▐▛███▜▌\n▝▜█████▛▘\n  ▘▘ ▝▝"
"""Claude Code's mascot, as its welcome screen draws it."""

bold = Style(text_style=CellStyle(bold=True))
dim = text_color("slate", 400)
emphasis = text_color("amber", 300)
heading_style = bold | Style(text_style=CellStyle(foreground=PYTHON_YELLOW))
code_border = border | border_heavy | Style(border_style=CellStyle(foreground=PYTHON_BLUE))


SHADOW = linear_gradient((gray_700, 0.5), (gray_400, 1), to="bottom right")
"""
The drop shadow's colors: strongest at its far corner, fading toward its two ends, where it meets the slide.
Pointing to a corner puts the gradient's halfway line through the other two corners, which are the shadow's ends.
"""


def drop_shadow(*children: Text | Div) -> Div:
    """
    `children` in a light-shade shadow: an outer box bordered only right and bottom,
    contracted by a cell so the shadow starts one cell in from the top and left.
    """
    return Div(
        style=border_right | border_bottom | border_lightshade | border_contract(1) | border_gradient(SHADOW),
        children=children,
    )


CARD_EDGE = Color.from_hex("#cbd5e1")
"""Tailwind's slate 300, which the title card's border passes through between its blue and its yellow."""
TURN_PERIOD = timedelta(seconds=6)
"""
One turn of the title card's border.
It divides the export's `SETTLE`, so every exported frame catches the border where it starts.
"""
SHINE_PERIOD = timedelta(seconds=5)
SHINE_SWEEP = 0.3
"""The part of each shine period the shine spends crossing the title; it rests for the rest."""
SHINE_WIDTH = 3
"""How many cells either side of the shine's center it lightens, fading out."""
SHINE = Color.from_hex("#FFF6D5")


def turning_edge(phase: float) -> ConicGradient:
    """
    The title card's border `phase` of the way through a turn: Python's blue and yellow on opposite sides,
    through slate between them, turned clockwise from blue at the top and yellow at the bottom.
    """
    return conic_gradient(PYTHON_BLUE, CARD_EDGE, PYTHON_YELLOW, CARD_EDGE, PYTHON_BLUE, start=360 * phase)


def light_across(length: int, center: float, width: float, base: Color, light: Color) -> LinearGradient:
    """
    `base`, lit up to `light` at `center` cells along a text `length` cells long, fading back to `base` `width` cells
    either side, for a text style or chunk whose element's content box is the text, which the gradient maps over.
    The light can be off either end, where the text is all `base`.
    """
    # A gradient spans the centers of its box's first and last cells, so a cell's position is its index over this.
    span = max(length - 1, 1)
    return linear_gradient(
        (base, (center - width) / span), (light, center / span), (base, (center + width) / span), to="right"
    )


@component
def title_card(title: str, *subtitles: str, is_live: bool) -> Div:
    """
    A centered, heavily bordered card in a drop shadow, for section and talk titles, with a line per subtitle.

    Its border turns, Python's blue and yellow chasing each other around it through slate, wherever the card is drawn,
    the slide grid's thumbnails included: there are few enough title cards in view at once that it's cheap.
    Its turn starts from the same place when it mounts, so cards mounted at different times turn out of step.
    While its slide is live, a shine also crosses the title every few seconds.
    """
    border_phase = use_loop(TURN_PERIOD, is_playing=True)
    shine_phase = use_loop(SHINE_PERIOD, is_live)
    # Off the title's left edge at the start of each period, so a still frame (phase 0) has no shine.
    shine = -SHINE_WIDTH + shine_phase / SHINE_SWEEP * (len(title) + 2 * SHINE_WIDTH)
    # The title is a text of its own, so its content box is the title, which the shine maps over,
    # rather than the widest of its subtitles.
    return drop_shadow(
        Div(
            style=col
            | align_children_center
            | border
            | border_heavy
            | border_gradient(turning_edge(border_phase))
            | pad_x(4)
            | pad_y(1),
            children=(
                Text(
                    content=title,
                    style=bold | text_gradient(light_across(len(title), shine, SHINE_WIDTH, PYTHON_YELLOW, SHINE)),
                ),
                *(
                    (
                        Text(
                            content="\n".join(subtitles),
                            style=Style(text_style=CellStyle(foreground=PYTHON_BLUE))
                            | text_justify_center
                            | align_self_stretch,
                        ),
                    )
                    if subtitles
                    else ()
                ),
            ),
        )
    )


def centered(*children: Component | Text | Div) -> Div:
    """`children` stacked in the middle of the slide."""
    return Div(style=col | fill(1) | center_children | gap_height(1), children=children)


def bullets(*items: str | Chunk | tuple[Chunk, ...]) -> Text:
    """A bulleted list, one item per line, each plain text, one chunk, or several."""
    chunks: list[Chunk] = []
    for item in items:
        if chunks:
            chunks.append(Chunk.newline())
        chunks.append(Chunk(content="• ", style=CellStyle(foreground=PYTHON_BLUE)))
        match item:
            case str():
                chunks.append(Chunk(content=item))
            case Chunk():
                chunks.append(item)
            case tuple():
                chunks.extend(item)
    return Text(content=tuple(chunks), style=text_wrap_pretty)


def code(text: str) -> Chunk:
    """Inline code in prose."""
    return Chunk(content=text, style=CellStyle(foreground=Color.from_hex("#79c0ff")))


def plain(text: str) -> Chunk:
    return Chunk(content=text)


def em(text: str) -> Chunk:
    return Chunk(content=text, style=CellStyle(foreground=PYTHON_YELLOW, bold=True))


def link(url: str) -> Chunk:
    """`url` without its scheme, as an OSC 8 hyperlink to it, for a terminal that opens links."""
    return Chunk(
        content=url.removeprefix("https://"),
        style=CellStyle(foreground=PYTHON_BLUE, underline=True, link=url),
    )


@component
def made_with_claude(is_live: bool) -> Div:
    """
    The disclosure that this deck was built with help from Claude Code, under Claude's spark, in its orange.
    While its slide is live it animates as Claude Code's spinner does, the spark turning and a shimmer sweeping
    across the words: the title and closing slides stay up for minutes, so they're the ones with something moving.
    Still, it's the spark at full size and no shimmer.
    """
    phase = use_loop(CREDIT_PERIOD, is_live)
    turns = len(SPARK_CYCLE) * 2
    spark = SPARK_CYCLE[(SPARK_CYCLE.index(CLAUDE_SPARK) + int(phase * turns)) % len(SPARK_CYCLE)]
    # From fully off the left edge to fully off the right, so a still frame (phase 0) has no shimmer.
    center = -SHIMMER_WIDTH + phase * (len(CREDIT) + 2 * SHIMMER_WIDTH)
    # The words are a text of their own, so their content box is the words, which the shimmer maps over.
    return Div(
        style=row | shrink(0),
        children=(
            Text(content=f"{spark} ", style=bold | Style(text_style=CellStyle(foreground=CLAUDE_ORANGE))),
            Text(
                content=CREDIT,
                style=text_gradient(light_across(len(CREDIT), center, SHIMMER_WIDTH, CLAUDE_ORANGE, CLAUDE_SHIMMER)),
            ),
        ),
    )


def claude_mascot() -> Text:
    return Text(
        content=CLAUDE_MASCOT, style=Style(text_style=CellStyle(foreground=CLAUDE_ORANGE)) | text_wrap_none | shrink(0)
    )
