"""
F4's code theme picker, F6's transition picker, F7's grid transition picker and F8's speed picker,
the themes F4 offers,
the checkpoint that remembers each choice across a restart,
and the Tachyon stage's workload and mode pickers.
"""

import asyncio
from dataclasses import replace

import pytest
from counterweight import app
from counterweight.controls import AnyControl
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.events import AnyEvent
from counterweight.events import KeyPressed
from counterweight.keys import Key
from counterweight.paint import Frame
from counterweight.styles import Style

from whats_new.checkpoint import Checkpoint
from whats_new.components.code import CODE_THEME
from whats_new.components.code import CODE_THEMES
from whats_new.components.code import has_dark_background
from whats_new.components.picker import SHOWN_OPTIONS
from whats_new.components.picker import Choice
from whats_new.components.picker import bar_row
from whats_new.components.picker import matches
from whats_new.components.transitions import GRID_GROUPS
from whats_new.components.transitions import GRID_OFFERED
from whats_new.components.transitions import OFF
from whats_new.components.transitions import OFFERED
from whats_new.components.transitions import RANDOM
from whats_new.deck import SLIDES
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import GRID_TRANSITION
from whats_new.presenter import PACE
from whats_new.presenter import THEME
from whats_new.presenter import TRANSITION
from whats_new.presenter import root
from whats_new.size import PRESENTING
from whats_new.tachyon import MODE_CHOICE
from whats_new.tachyon import NO_WORKLOAD
from whats_new.tachyon import WORKLOAD_CHOICE


@pytest.mark.parametrize(("theme", "expected"), [("monokai", True), ("zenburn", True), ("solarized-light", False)])
def test_has_dark_background_tells_dark_themes_from_light(theme: str, expected: bool) -> None:
    assert has_dark_background(theme) is expected


def test_the_default_theme_is_offered() -> None:
    assert CODE_THEME in CODE_THEMES


@pytest.mark.parametrize(
    ("text", "expected"),
    [("", CODE_THEMES), ("nrdd", ("nord-darker",)), ("GRUV", ("gruvbox-dark",)), ("[", ())],
    ids=["nothing typed", "letters in order", "any case", "a glob character matches itself"],
)
def test_matches_finds_themes_with_the_typed_letters_in_order(text: str, expected: tuple[str, ...]) -> None:
    assert matches(text, CODE_THEMES) == expected


def test_matches_puts_the_option_named_exactly_first() -> None:
    assert matches("ab", ("a-b", "cab", "AB", "abc")) == ("AB", "a-b", "cab", "abc")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            '{"slide": 12, "code_theme": "monokai", "transition": "morph", "speed": "0.5x", "grid_transition": "zoom"}',
            Checkpoint(slide=12, code_theme="monokai", transition="morph", speed="0.5x", grid_transition="zoom"),
        ),
        ('{"slide": 12, "code_theme": "monokai"}', Checkpoint(slide=12, code_theme="monokai", transition=OFF)),
        ('{"slide": 12, "code_theme": "solarized-light"}', Checkpoint(slide=12, code_theme=CODE_THEME)),
        ('{"slide": 12, "code_theme": "monokai", "transition": "zoom"}', Checkpoint(slide=12, code_theme="monokai")),
        (
            '{"slide": 12, "code_theme": "monokai", "transition": "wipe", "easing": "spring"}',
            Checkpoint(slide=12, code_theme="monokai", transition="wipe"),
        ),
        (
            '{"slide": 12, "code_theme": "monokai", "speed": "11x", "grid_transition": "swipe"}',
            Checkpoint(slide=12, code_theme="monokai"),
        ),
        (
            '{"slide": 12, "code_theme": "monokai", "ghost_overrides": {"Tachyon": true, "Thanks": false}}',
            Checkpoint(slide=12, code_theme="monokai", ghost_overrides=frozendict({"Tachyon": True, "Thanks": False})),
        ),
        (
            '{"slide": 12, "code_theme": "monokai", "ghost_overrides": {"Tachyon": "yes"}}',
            Checkpoint(slide=12, code_theme="monokai"),
        ),
        ("12", Checkpoint(slide=0)),
        ("", Checkpoint(slide=0)),
    ],
    ids=[
        "a checkpoint",
        "one from before transitions",
        "a theme the picker doesn't offer",
        "a transition the picker doesn't offer",
        "a field the deck doesn't read",
        "a speed and a grid transition the pickers don't offer",
        "ghost overrides",
        "ghost overrides that aren't booleans",
        "not an object",
        "not JSON",
    ],
)
def test_checkpoint_parse(text: str, expected: Checkpoint) -> None:
    assert Checkpoint.parse(text) == expected


def test_checkpoint_round_trips() -> None:
    checkpoint = Checkpoint(
        slide=7,
        code_theme="nord",
        transition="morph",
        speed="2x",
        grid_transition="zoom",
        ghost_overrides=frozendict({"Tachyon": True}),
    )

    assert Checkpoint.parse(checkpoint.serialized()) == checkpoint


async def test_choosing_a_theme_checkpoints_it_and_gives_the_slide_its_keys_back(host: Host) -> None:
    index = next(index for index, slide in enumerate(SLIDES) if slide.title == "frozendict: the mutable default, fixed")
    checkpoints: list[Checkpoint] = []
    frames: list[Frame] = []

    async def settle(frame: Frame) -> None:
        await asyncio.sleep(0.05)

    autopilot: tuple[AnyEvent | AnyControl, ...] = (
        KeyPressed(key=Key.F4),
        *(KeyPressed(key=character) for character in "mono"),
        KeyPressed(key=Key.Enter),
        # Only reaches the slide's editor if closing the picker gave focus back to the slide.
        KeyPressed(key=Key.Tab),
        KeyPressed(key="Q"),
        Screenshot(handler=frames.append),
        # The checkpoint is written from an effect, which runs once the autopilot yields to it.
        Screenshot(handler=settle),
        Quit(),
    )
    await app(
        root(SLIDES, host, Checkpoint(slide=index), checkpoints.append),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=autopilot,
        clock=EXPORT_CLOCK,
    )

    assert checkpoints[-1] == Checkpoint(slide=index, code_theme="monokai")
    text = frames[0].text(ansi=False)
    assert "code theme" not in text
    assert 'print(f"{DEFAULTS=}")Q' in text


@pytest.mark.parametrize(
    ("key", "typed", "expected", "label"),
    [
        (Key.F6, "mor", Checkpoint(slide=0, transition="morph"), "slide transition"),
        (Key.F8, "0.2", Checkpoint(slide=0, speed="0.25x"), "transition speed"),
        (Key.F7, "zoo", Checkpoint(slide=0, grid_transition="zoom"), "grid transition"),
        (Key.F7, "grid eff", Checkpoint(slide=0, grid_transition="grid effects"), "grid transition"),
    ],
    ids=["a transition", "a speed", "a grid transition", "a group of grid transitions, by its bar"],
)
async def test_choosing_a_transition_setting_checkpoints_it_and_gives_the_slide_its_keys_back(
    host: Host, key: Key, typed: str, expected: Checkpoint, label: str
) -> None:
    index = next(index for index, slide in enumerate(SLIDES) if slide.title == "frozendict: the mutable default, fixed")
    checkpoints: list[Checkpoint] = []
    frames: list[Frame] = []

    async def settle(frame: Frame) -> None:
        await asyncio.sleep(0.05)

    autopilot: tuple[AnyEvent | AnyControl, ...] = (
        KeyPressed(key=key),
        *(KeyPressed(key=character) for character in typed),
        KeyPressed(key=Key.Enter),
        KeyPressed(key=Key.Tab),
        KeyPressed(key="Q"),
        Screenshot(handler=frames.append),
        Screenshot(handler=settle),
        Quit(),
    )
    await app(
        root(SLIDES, host, Checkpoint(slide=index), checkpoints.append),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=autopilot,
        clock=EXPORT_CLOCK,
    )

    assert checkpoints[-1] == replace(expected, slide=index)
    text = frames[0].text(ansi=False)
    assert label not in text
    assert 'print(f"{DEFAULTS=}")Q' in text


async def test_each_function_key_opens_its_own_picker_in_place_of_the_other(host: Host) -> None:
    frames: list[Frame] = []
    autopilot: tuple[AnyEvent | AnyControl, ...] = (
        KeyPressed(key=Key.F4),
        KeyPressed(key=Key.F6),
        Screenshot(handler=frames.append),
        Quit(),
    )
    await app(
        root(SLIDES, host, Checkpoint(slide=0), lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=autopilot,
        clock=EXPORT_CLOCK,
    )

    text = frames[0].text(ansi=False)
    assert "slide transition" in text
    assert "code theme" not in text
    assert all(option in text for option in OFFERED[:SHOWN_OPTIONS])


async def test_a_picker_opened_in_place_of_another_takes_the_keys(host: Host) -> None:
    checkpoints: list[Checkpoint] = []
    frames: list[Frame] = []

    async def settle(frame: Frame) -> None:
        await asyncio.sleep(0.05)

    autopilot: tuple[AnyEvent | AnyControl, ...] = (
        KeyPressed(key=Key.F4),
        KeyPressed(key=Key.F6),
        KeyPressed(key=Key.Down),
        KeyPressed(key=Key.Enter),
        Screenshot(handler=frames.append),
        Screenshot(handler=settle),
        Quit(),
    )
    await app(
        root(SLIDES, host, Checkpoint(slide=0), checkpoints.append),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=autopilot,
        clock=EXPORT_CLOCK,
    )

    assert "slide transition" not in frames[0].text(ansi=False)
    assert checkpoints[-1] == Checkpoint(slide=0, transition=OFFERED[1])


@pytest.mark.parametrize(
    "choice",
    [THEME, TRANSITION, PACE, GRID_TRANSITION, MODE_CHOICE, WORKLOAD_CHOICE],
    ids=lambda choice: choice.label,
)
def test_a_picker_fits_inside_the_slide(choice: Choice) -> None:
    # The slide body has a column of padding either side, and the picker sits one more in from the right.
    assert choice.width <= PRESENTING.columns - 3


def test_f7_lists_every_name_the_grid_transition_can_be_set_to_in_order() -> None:
    assert GRID_TRANSITION.names == GRID_OFFERED


def test_f7_lists_off_and_random_first_under_no_bar() -> None:
    first, *grouped = GRID_TRANSITION.sections

    assert (first.title, tuple(option.name for option in first.options)) == (None, (OFF, RANDOM))
    assert [section.title for section in grouped] == [group.title for group in GRID_GROUPS]


@pytest.mark.parametrize("name", [name for group in GRID_GROUPS for name in group.transitions])
def test_typing_a_grid_transitions_name_matches_it_and_not_its_bar(name: str) -> None:
    assert matches(name, GRID_TRANSITION.names)[0] == name


def test_a_bar_runs_across_the_picker() -> None:
    section = GRID_TRANSITION.bars["slide effects"]

    (title, rule) = bar_row(section, Style(), GRID_TRANSITION.inner_width, is_current=False)

    assert (title.content.startswith("─── slide effects ─ "), len(title.content + rule.content)) == (
        True,
        GRID_TRANSITION.inner_width,
    )


@pytest.mark.parametrize(
    ("choice", "name"),
    [(choice, name) for choice in (MODE_CHOICE, WORKLOAD_CHOICE) for name in choice.names],
    ids=lambda value: value if isinstance(value, str) else value.label,
)
def test_typing_an_option_s_whole_name_matches_it_first(choice: Choice, name: str) -> None:
    # The tour picks by typing a name and pressing Enter, which chooses the first match.
    assert matches(name, choice.names)[0] == name


async def test_the_tachyon_pickers_start_a_workload_and_change_the_mode(host: Host) -> None:
    index = next(index for index, slide in enumerate(SLIDES) if slide.title == "Tachyon, live")
    frames: list[Frame] = []

    async def settle(frame: Frame) -> None:
        await asyncio.sleep(0.05)

    autopilot: tuple[AnyEvent | AnyControl, ...] = (
        KeyPressed(key="w"),
        *(KeyPressed(key=character) for character in "blo"),
        KeyPressed(key=Key.Enter),
        KeyPressed(key="m"),
        *(KeyPressed(key=character) for character in "gil"),
        KeyPressed(key=Key.Enter),
        # The workload starts from an effect, which runs once the autopilot yields to it.
        Screenshot(handler=settle),
        Screenshot(handler=frames.append),
        Quit(),
    )
    await app(
        root(SLIDES, host, Checkpoint(slide=index), lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=autopilot,
        clock=EXPORT_CLOCK,
    )

    text = frames[0].text(ansi=False)
    assert "mode: gil" in text
    assert "running: blocking I/O" in text
    assert "profiler mode" not in text


@pytest.mark.parametrize(
    "stop",
    [
        (KeyPressed(key="c"),),
        (KeyPressed(key="w"), *(KeyPressed(key=character) for character in NO_WORKLOAD), KeyPressed(key=Key.Enter)),
    ],
    ids=["c", "none in the picker"],
)
async def test_the_tachyon_workload_stops(host: Host, stop: tuple[KeyPressed, ...]) -> None:
    index = next(index for index, slide in enumerate(SLIDES) if slide.title == "Tachyon, live")
    frames: list[Frame] = []

    async def settle(frame: Frame) -> None:
        await asyncio.sleep(0.05)

    autopilot: tuple[AnyEvent | AnyControl, ...] = (
        KeyPressed(key="w"),
        *(KeyPressed(key=character) for character in "blo"),
        KeyPressed(key=Key.Enter),
        Screenshot(handler=settle),
        *stop,
        Screenshot(handler=settle),
        Screenshot(handler=frames.append),
        Quit(),
    )
    await app(
        root(SLIDES, host, Checkpoint(slide=index), lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=autopilot,
        clock=EXPORT_CLOCK,
    )

    assert "running: idle" in frames[0].text(ansi=False)


@pytest.mark.parametrize(
    ("key", "start", "current"),
    [
        (Key.F4, Checkpoint(slide=0, code_theme="zenburn"), "zenburn"),
        (Key.F6, Checkpoint(slide=0, transition="rain"), "rain"),
    ],
    ids=["code theme", "slide transition"],
)
async def test_a_picker_opens_showing_its_current_option_past_the_rows_it_shows(
    host: Host, key: Key, start: Checkpoint, current: str
) -> None:
    """In the frame it opens in, with no pause for an effect to run, as when the recordings drive the deck."""
    frames: list[Frame] = []
    await app(
        root(SLIDES, host, start, lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(KeyPressed(key=key), Screenshot(handler=frames.append), Quit()),
        clock=EXPORT_CLOCK,
    )

    assert f"▸ {current}" in frames[0].text(ansi=False)
