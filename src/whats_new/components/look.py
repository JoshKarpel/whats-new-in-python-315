"""The deck's palette and the small styled pieces every section uses: headings, bullets, title cards."""

import math
from datetime import timedelta

from counterweight.components import Component
from counterweight.components import component
from counterweight.elements import Chunk
from counterweight.elements import Div
from counterweight.elements import Text
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


def drop_shadow(*children: Text | Div) -> Div:
    """
    `children` in a light-shade shadow: an outer box bordered only right and bottom,
    contracted by a cell so the shadow starts one cell in from the top and left.
    """
    return Div(
        style=border_right | border_bottom | border_lightshade | border_contract(1) | border_color("gray", 400),
        children=children,
    )


CARD_EDGE = Color.from_hex("#cbd5e1")
"""The title card's border at rest, Tailwind's slate 300, which its pulse passes through between colors."""
PULSE_PERIOD = timedelta(seconds=6)
"""
One round of the border's pulse: slate, to blue, to slate, to yellow, and back to slate.
It divides the export's `SETTLE`, so every exported frame catches the pulse at rest.
"""
SHINE_PERIOD = timedelta(seconds=5)
SHINE_SWEEP = 0.3
"""The part of each shine period the shine spends crossing the title; it rests for the rest."""
SHINE = Color.from_hex("#FFF6D5")


def pulse(phase: float) -> Color:
    """
    The border's color `phase` of the way through its pulse: easing from slate out to Python's blue,
    back through slate to its yellow, and back to slate, so phase 0 (a still frame) is the plain card.
    """
    swing = math.sin(2 * math.pi * phase)
    return CARD_EDGE.blend(PYTHON_BLUE if swing > 0 else PYTHON_YELLOW, abs(swing))


def glow(distance: float, width: float) -> float:
    """How lit a cell `distance` either side of a moving light is, fading to nothing at `width`."""
    return max(0.0, 1 - abs(distance) / width)


@component
def title_card(title: str, *subtitles: str, is_live: bool) -> Div:
    """
    A centered, heavily bordered card in a drop shadow, for section and talk titles, with a line per subtitle.

    Its border pulses between Python's blue and yellow, through slate, wherever the card is drawn,
    the slide grid's thumbnails included: there are few enough title cards in view at once that it's cheap.
    Its pulse starts at rest when it mounts, so cards mounted at different times pulse out of step.
    While its slide is live, a shine also crosses the title every few seconds.
    """
    border_phase = use_loop(PULSE_PERIOD, is_playing=True)
    shine_phase = use_loop(SHINE_PERIOD, is_live)
    # Off the title's left edge at the start of each period, so a still frame (phase 0) has no shine.
    shine = -3 + shine_phase / SHINE_SWEEP * (len(title) + 6)
    lines: tuple[Chunk, ...] = tuple(
        Chunk(content=letter, style=CellStyle(bold=True, foreground=PYTHON_YELLOW.blend(SHINE, glow(index - shine, 3))))
        for index, letter in enumerate(title)
    )
    for subtitle in subtitles:
        lines = (*lines, Chunk.newline(), Chunk(content=subtitle, style=CellStyle(foreground=PYTHON_BLUE)))
    return drop_shadow(
        Text(
            content=lines,
            style=border
            | border_heavy
            | Style(border_style=CellStyle(foreground=pulse(border_phase)))
            | pad_x(4)
            | pad_y(1)
            | text_justify_center,
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
def made_with_claude(is_live: bool) -> Text:
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
    return Text(
        content=(
            Chunk(content=f"{spark} ", style=CellStyle(foreground=CLAUDE_ORANGE, bold=True)),
            *(
                Chunk(
                    content=letter,
                    style=CellStyle(
                        foreground=CLAUDE_ORANGE.blend(
                            CLAUDE_SHIMMER, max(0.0, 1 - abs(index - center) / SHIMMER_WIDTH)
                        )
                    ),
                )
                for index, letter in enumerate(CREDIT)
            ),
        ),
    )


def claude_mascot() -> Text:
    return Text(
        content=CLAUDE_MASCOT, style=Style(text_style=CellStyle(foreground=CLAUDE_ORANGE)) | text_wrap_none | shrink(0)
    )
