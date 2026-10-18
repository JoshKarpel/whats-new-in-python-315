"""
The lazy import, after PEP 810: the slide being left dissolves away, and the arriving slide's regions show first
as proxies, dim `░` where their characters will be under a label like `<lazy_import 'defaults'>`, the repr a lazily
imported module has until it's first used. Then, one region at a time in an order of their own, each is "used" and
resolves into its real content, swept in from its left edge.

A region is a block of the arriving slide's content: its characters, and any cells whose background stands out from
the slide's, joined across gaps of a single blank (the spaces between words) and down to the cells straight below
when those are drawn in the same colors, so a heading over a code box's border stays apart from it while a box's
sides, or the lines of a bulleted list, hold together. A region's label is named after its first word that would do
for a module name, and sits on its top row. The direction plays no part.
"""

import random
import re
from collections import Counter
from dataclasses import dataclass

from counterweight.elements import StyledGrapheme
from counterweight.styles import CellStyle
from counterweight.styles import Color

from whats_new.components.crossing import Frames
from whats_new.components.crossing import Grid
from whats_new.components.crossing import dimensions
from whats_new.components.effects.characters import Backgrounds
from whats_new.components.effects.characters import backgrounds
from whats_new.components.effects.masks import scattered
from whats_new.components.swipe import Direction

type Point = tuple[int, int]

CLEARED = 0.2
"""Where every cell of the leaving slide has dissolved away."""
APPEARING = (0.15, 0.3)
"""When the placeholders appear, each region's at its own moment, though only over cells already cleared."""
RESOLVING = (0.35, 1.0)
"""When the regions resolve, one after another."""
SWEEP = 0.12
"""How much of the progress one region's resolving takes, swept in from its left edge."""
SEED = 810

PLACEHOLDER = "░"
PROXY = CellStyle(foreground=Color.from_hex("#334155"))
"""The placeholders' dim `░`, Tailwind's slate 700."""
LABEL = CellStyle(foreground=Color.from_hex("#64748b"), italic=True)
"""The proxies' labels, Tailwind's slate 500."""
MODULE_NAME = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*")
SHORTEST_NAME = 4
"""How long a word has to be to name a region: shorter ones are mostly the likes of "the" and "a"."""


@dataclass(frozen=True, slots=True)
class Region:
    """
    One block of the arriving slide, the `cells` it takes, and its label, `name` the module it stands in for,
    or `None` when it has no word to name it by, as a box's border doesn't.
    """

    cells: frozenset[Point]
    name: str | None
    top: int

    @classmethod
    def of(cls, cells: set[Point], name: str | None) -> Region:
        """The region taking `cells`, which mustn't be empty, with its top row worked out once."""
        return cls(cells=frozenset(cells), name=name, top=min(y for _, y in cells))


def is_content(glyph: StyledGrapheme | None, backdrop: object) -> bool:
    """Whether a cell is part of a region: a character, the right half of one, or a background of its own."""
    return glyph is None or bool(glyph.grapheme.strip()) or glyph.style.background != backdrop


def regions(picture: Grid) -> tuple[Region, ...]:
    """
    The blocks of `picture`'s content, in reading order of their top left cells. Content cells join the next to
    their right across up to one blank, and the one straight below when the two have the same colors, or are both
    the right halves of graphemes.
    """
    backdrop = Counter(glyph.style.background for row in picture for glyph in row if glyph is not None).most_common(1)
    common = backdrop[0][0] if backdrop else None
    content = {(x, y) for y, row in enumerate(picture) for x, glyph in enumerate(row) if is_content(glyph, common)}

    def colors(point: Point) -> tuple[object, object] | None:
        glyph = picture[point[1]][point[0]]
        return None if glyph is None else (glyph.style.foreground, glyph.style.background)

    def neighbors(point: Point) -> list[Point]:
        x, y = point
        joined = [(x + step, y) for step in (1, 2) if (x + step, y) in content][:1]
        joined += [(x - step, y) for step in (1, 2) if (x - step, y) in content][:1]
        joined += [
            (x, y + step) for step in (-1, 1) if (x, y + step) in content and colors((x, y + step)) == colors(point)
        ]
        return joined

    found: list[Region] = []
    unvisited = set(content)
    for start in sorted(content, key=lambda point: (point[1], point[0])):
        if start not in unvisited:
            continue
        unvisited.discard(start)
        block, frontier = {start}, [start]
        while frontier:
            for neighbor in neighbors(frontier.pop()):
                if neighbor in unvisited:
                    unvisited.discard(neighbor)
                    block.add(neighbor)
                    frontier.append(neighbor)
        found.append(Region.of(block, name_of(picture, block)))
    return tuple(found)


def name_of(picture: Grid, block: set[Point]) -> str | None:
    """The first word in `block`, reading row by row, long enough to name a module after, lowercased."""
    for y in sorted({y for _, y in block}):
        text = "".join(
            glyph.grapheme if (x, y) in block and glyph is not None else " " for x, glyph in enumerate(picture[y])
        )
        for word in MODULE_NAME.findall(text):
            if len(word) >= SHORTEST_NAME:
                return word.lower()
    return None


def label_of(name: str, room: int) -> str | None:
    """
    The proxy's label for a module called `name`, cutting the name short to fit in `room` cells,
    or `None` if there isn't room for the label with a name at least `SHORTEST_NAME` long.
    """
    framing = len("<lazy_import ''>")
    if room < framing + SHORTEST_NAME:
        return None
    return f"<lazy_import '{name[: room - framing]}'>"


def labelled(region: Region, owners: dict[Point, Region], width: int) -> tuple[int, str] | None:
    """
    Where along its top row `region`'s label starts, and the label: from the row's first cell if it fits, or as far
    left of that as it needs, over the run of cells no other region takes, so a title inside a box keeps its label
    inside the box. `None` when the region has no name or the run is too short for a label.
    """
    if region.name is None:
        return None
    y = region.top
    columns = sorted(x for x, row in region.cells if row == y)

    def is_free(x: int) -> bool:
        return 0 <= x < width and owners.get((x, y), region) is region

    start, stop = columns[0], columns[-1] + 1
    while is_free(start - 1):
        start -= 1
    while is_free(stop):
        stop += 1
    label = label_of(region.name, stop - start)
    if label is None:
        return None
    return max(start, min(columns[0], stop - len(label))), label


def proxies(
    picture: Grid, behind: Backgrounds, found: tuple[Region, ...]
) -> dict[Point, tuple[StyledGrapheme, Region]]:
    """
    Each region's placeholder cells, and which region each belongs to: `░` over its characters, with its label
    written over its top row and the blanks either side. A two-cell-wide grapheme's right half gets a `░` of its own,
    so the placeholder has no gaps. A region's blanks aren't placeholders: they show their background, as they will
    once it resolves.
    """
    width = len(picture[0]) if picture else 0
    owners = {point: region for region in found for point in region.cells}
    placed: dict[Point, tuple[StyledGrapheme, Region]] = {}
    for region in found:
        for x, y in region.cells:
            if (glyph := picture[y][x]) is not None and not glyph.grapheme.strip():
                continue
            backdrop = CellStyle(background=behind[y][x].style.background)
            placed[x, y] = StyledGrapheme(grapheme=PLACEHOLDER, style=PROXY | backdrop), region
        if (label := labelled(region, owners, width)) is None:
            continue
        start, text = label
        for x, character in enumerate(text, start):
            backdrop = CellStyle(background=behind[region.top][x].style.background)
            placed[x, region.top] = StyledGrapheme(grapheme=character, style=LABEL | backdrop), region
    return placed


@dataclass(frozen=True, slots=True)
class Cell:
    """
    What one cell shows at each stage, and when it moves to the next: the leaving slide's cell until `cleared`,
    then the arriving slide's background until `appeared`, then its `proxy` until `resolved`, then the arriving cell.
    """

    leaving: StyledGrapheme | None
    background: StyledGrapheme
    proxy: StyledGrapheme
    arriving: StyledGrapheme | None
    cleared: float
    appeared: float
    resolved: float

    def at(self, progress: float) -> StyledGrapheme | None:
        """What the cell shows `progress` of the way through the transition."""
        if progress <= self.cleared:
            return self.leaving
        if progress <= self.appeared:
            return self.background
        if progress <= self.resolved:
            return self.proxy
        return self.arriving


def lazy_import(leaving: Grid, arriving: Grid, direction: Direction) -> Frames:
    """
    The lazy import's frames, cell by cell along the progress: the leaving slide dissolving, the proxies
    appearing over the arriving slide's backgrounds, and each region resolving in its turn.
    """
    width, height = dimensions(leaving)
    behind = backgrounds(arriving)
    found = regions(arriving)
    placed = proxies(arriving, behind, found)
    chance = random.Random(SEED)
    order = list(found)
    chance.shuffle(order)
    resolve_start, resolve_stop = RESOLVING
    turns = {
        region: resolve_start + (resolve_stop - SWEEP - resolve_start) * index / max(len(order) - 1, 1)
        for index, region in enumerate(order)
    }
    appear_start, appear_stop = APPEARING
    appearances = {region: appear_start + (appear_stop - appear_start) * chance.random() for region in found}
    # A label can stick out past its region's characters, so each region sweeps across every cell it shows a proxy in.
    spans: dict[Region, tuple[int, int]] = {}
    for (x, _), (_, region) in placed.items():
        left, right = spans.get(region, (x, x + 1))
        spans[region] = min(left, x), max(right, x + 1)
    dissolving = scattered(width, height, direction)

    def cell(x: int, y: int) -> Cell:
        # A grapheme's right half clears with its left, so the two never show from different slides.
        column = x - 1 if leaving[y][x] is None and x > 0 else x
        cleared = dissolving[y][column] * CLEARED
        if (x, y) not in placed:
            # Nothing to resolve: the arriving cell is only its background, so it shows as soon as it's clear.
            return Cell(leaving[y][x], behind[y][x], behind[y][x], arriving[y][x], cleared, cleared, cleared)
        proxy, region = placed[x, y]
        # Resolve column by column, a right half with its left, so a grapheme never shows split.
        column = x - 1 if arriving[y][x] is None and x > 0 else x
        left, right = spans[region]
        resolved = turns[region] + (column - left) / (right - left) * SWEEP
        appeared = max(appearances[region], cleared)
        return Cell(leaving[y][x], behind[y][x], proxy, arriving[y][x], cleared, appeared, resolved)

    cells = tuple(tuple(cell(x, y) for x in range(width)) for y in range(height))

    def frame(t: float) -> Grid:
        return tuple(tuple(each.at(t) for each in row) for row in cells)

    return frame
