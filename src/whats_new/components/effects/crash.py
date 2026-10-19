"""
The crash: the slide being left glitches, worse and worse (rows torn sideways, runs of text in the wrong colors,
stray escape codes printed raw, blocks of noise), then the screen squashes to a line and goes dark the way an old
tube's picture does when it's switched off. A crash report and a reboot print on the dark screen a line at a time,
and the arriving slide switches on, opening out from a line across the middle.

The glitches are drawn afresh at each of `GLITCH_STEPS` steps of the transition, from a random seeded by the step,
so the picture jitters as it plays and plays the same way every time. Only parts of the screen ever glitch at once,
and nothing flashes: the darkness comes in and goes out by squashing, never by a cut to a bright screen.
The phases keep their own timing, since a crash isn't a movement to ease. The direction plays no part.
"""

import random
from dataclasses import dataclass

from counterweight.animation import between
from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color

from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.look import PYTHON_BLUE
from whats_new.components.look import PYTHON_YELLOW
from whats_new.components.swipe import Direction

type Cells = list[list[StyledGrapheme | None]]

GLITCHING = 0.42
"""Where the glitching stops and the picture starts to squash down."""
DARK = 0.5
"""Where the picture has squashed away to nothing."""
SWITCHING_ON = 0.84
"""Where the arriving slide starts to open out, the crash report and reboot printed by then."""
SQUASHED = 0.7
"""How far through the squash the picture is down to a line, which then shrinks to nothing."""

GLITCH_STEPS = 64
"""How many times over the transition the glitches are drawn afresh: about once a frame, over three seconds."""
SEED = 315

BLACK = Color.from_hex("#000000")
DARKNESS = StyledGrapheme(grapheme=" ", style=CellStyle(background=BLACK))
TRACE = StyledGrapheme(grapheme="━", style=CellStyle(foreground=Color.from_hex("#e2e8f0"), background=BLACK))
"""The line a picture squashes down to, and opens out from."""

WRONG_COLORS = tuple(Color.from_hex(color) for color in ("#ff4fd8", "#2ee6d6", "#7dff6a", "#ff6a3d", "#8b7bff"))
GARBAGE = (
    "^[[31m",
    "^[[0;1;33m",
    "^[[2J",
    "^[[?25l",
    "^[[H",
    "^[[38;5;196m",
    "^[(B",
    "^@^@^@^@",
    "\\x1b[0m",
    "~~~~",
    "^[]8;;",
)
"""Escape codes as a terminal shows them when they arrive mangled: printed, rather than obeyed."""
GARBAGE_COLORS = (Color.from_hex("#f87171"), Color.from_hex("#94a3b8"), PYTHON_YELLOW)
NOISE = "░▒▓█▀▄▌▐"
NOISE_COLORS = (Color.from_hex("#475569"), Color.from_hex("#94a3b8"), PYTHON_BLUE)

RED = CellStyle(foreground=Color.from_hex("#f85149"), background=BLACK)
GRAY = CellStyle(foreground=Color.from_hex("#8b949e"), background=BLACK)
WHITE = CellStyle(foreground=Color.from_hex("#e6edf3"), background=BLACK)
YELLOW = CellStyle(foreground=PYTHON_YELLOW, background=BLACK)
REPORT: tuple[tuple[str, CellStyle], ...] = (
    ("Fatal Python error: Segmentation fault", RED),
    ("", GRAY),
    ("Current thread 0x00007f3a1c2b5740 (most recent call first):", GRAY),
    ('  File "whats_new/presenter.py", line 315 in next_slide', GRAY),
    ("", GRAY),
    ("$ python3.15 -m whats_new", WHITE),
    ("Python 3.15.0 (main) on linux", YELLOW),
    ("rebooting the deck... ok", WHITE),
)
"""What prints on the dark screen: `faulthandler`'s report of the crash, then the deck starting again."""


@dataclass(frozen=True, slots=True)
class Printed:
    """One line of the report, `text` in `style`, printed once the darkness is `at` of the way through."""

    text: str
    style: CellStyle
    at: float


def printed(report: tuple[tuple[str, CellStyle], ...]) -> tuple[Printed, ...]:
    """The report's lines, printed one after another over the first part of the darkness, leaving the last a moment."""
    return tuple(
        Printed(text=text, style=style, at=0.75 * index / len(report)) for index, (text, style) in enumerate(report)
    )


def written(cells: Cells, x: int, y: int, text: str, style: CellStyle) -> None:
    """`text` over `cells` from `x` along row `y`, one cell per character, as much of it as fits."""
    if not 0 <= y < len(cells):
        return
    row = cells[y]
    for offset, character in enumerate(text):
        if 0 <= x + offset < len(row):
            row[x + offset] = StyledGrapheme(grapheme=character, style=style)


def glitched(picture: Grid, severity: float, chance: random.Random) -> Grid:
    """
    `picture` with glitches drawn over it, as many and as large as `severity` says, from none at 0.
    Rows are torn sideways (one alone, or a band of them by the same amount), runs of text change color,
    escape codes print raw, and blocks of noise land on it.
    """
    width, height = dimensions(picture)
    if severity <= 0 or width == 0:
        return picture
    cells: Cells = [list(row) for row in picture]
    for _ in range(round(severity * 7)):
        y, shift = chance.randrange(height), chance.randint(1, 1 + round(severity * 14)) * chance.choice((-1, 1))
        cells[y] = cells[y][-shift:] + cells[y][:-shift]
    if chance.random() < severity / 2:
        top, shift = chance.randrange(height), chance.randint(2, 4 + round(severity * 10))
        for y in range(top, min(top + chance.randint(2, 6), height)):
            cells[y] = cells[y][shift:] + cells[y][:shift]
    for _ in range(round(severity * 5)):
        y, start, color = chance.randrange(height), chance.randrange(width), chance.choice(WRONG_COLORS)
        for x in range(start, min(start + chance.randint(4, 30), width)):
            if (glyph := cells[y][x]) is not None:
                cells[y][x] = StyledGrapheme(grapheme=glyph.grapheme, style=glyph.style | CellStyle(foreground=color))
    for _ in range(round(severity * 6)):
        style = CellStyle(foreground=chance.choice(GARBAGE_COLORS), background=BLACK)
        written(cells, chance.randrange(width), chance.randrange(height), chance.choice(GARBAGE), style)
    for _ in range(round(severity * 3)):
        top, left = chance.randrange(height), chance.randrange(width)
        style = CellStyle(foreground=chance.choice(NOISE_COLORS), background=BLACK)
        for y in range(top, min(top + chance.randint(1, 3), height)):
            noise = "".join(chance.choice(NOISE) for _ in range(chance.randint(4, 16)))
            written(cells, left, y, noise, style)
    return tuple(tuple(row) for row in cells)


def squashed(picture: Grid, opened: float) -> Grid:
    """
    `picture` squashed toward its middle row, `opened` of the way from nothing to its full height, as a tube draws
    it switching off or on: down to a line across the middle, then the line shrinking to nothing.
    Fully open, it's `picture` itself.
    """
    width, height = dimensions(picture)
    if opened >= 1:
        return picture
    middle = height / 2
    tall = between(opened, 1 - SQUASHED, 1)
    if tall > 0:
        return tuple(
            picture[min(int(middle + (y + 0.5 - middle) / tall), height - 1)]
            if abs(y + 0.5 - middle) < middle * tall
            else (DARKNESS,) * width
            for y in range(height)
        )
    reach = round(width / 2 * between(opened, 0, 1 - SQUASHED))
    line = tuple(TRACE if abs(x + 0.5 - width / 2) < reach else DARKNESS for x in range(width))
    return tuple(line if y == int(middle) else (DARKNESS,) * width for y in range(height))


def report_on(width: int, height: int, lines: tuple[Printed, ...], progress: float) -> Grid:
    """The dark screen with the report's lines printed by `progress` of the way through the darkness."""
    cells: Cells = [[DARKNESS] * width for _ in range(height)]
    for y, line in enumerate(lines):
        if line.at <= progress:
            written(cells, 2, y + 1, line.text, line.style)
    return tuple(tuple(row) for row in cells)


def crash(leaving: Grid, arriving: Grid, direction: Direction) -> Frames:
    """The crash's frames: glitching, switching off, the report on the dark, and switching on."""
    width, height = dimensions(leaving)
    lines = printed(REPORT)

    def frame(t: float) -> Grid:
        if t >= SWITCHING_ON:
            return squashed(arriving, between(t, SWITCHING_ON, 1))
        if t >= DARK:
            return report_on(width, height, lines, between(t, DARK, SWITCHING_ON))
        chance = random.Random(SEED * GLITCH_STEPS + int(t * GLITCH_STEPS))
        broken = glitched(leaving, between(t, 0, GLITCHING), chance)
        return squashed(broken, 1 - between(t, GLITCHING, DARK))

    return frame
