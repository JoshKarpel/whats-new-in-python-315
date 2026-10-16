"""F4's code theme picker, the themes it offers, and the checkpoint that remembers the choice across a restart."""

import asyncio

import pytest
from counterweight.app import app
from counterweight.controls import AnyControl
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.events import AnyEvent
from counterweight.events import KeyPressed
from counterweight.keys import Key
from counterweight.output import Frame

from whats_new.checkpoint import Checkpoint
from whats_new.components.code import CODE_THEME
from whats_new.components.code import CODE_THEMES
from whats_new.components.code import has_dark_background
from whats_new.components.theme_picker import matches
from whats_new.deck import SLIDES
from whats_new.export import EXPORT_CLOCK
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.size import PRESENTING


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


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('{"slide": 12, "code_theme": "monokai"}', Checkpoint(slide=12, code_theme="monokai")),
        ('{"slide": 12, "code_theme": "solarized-light"}', Checkpoint(slide=12, code_theme=CODE_THEME)),
        ("12", Checkpoint(slide=0)),
        ("", Checkpoint(slide=0)),
    ],
    ids=["a checkpoint", "a theme the picker doesn't offer", "not an object", "not JSON"],
)
def test_checkpoint_parse(text: str, expected: Checkpoint) -> None:
    assert Checkpoint.parse(text) == expected


def test_checkpoint_round_trips() -> None:
    checkpoint = Checkpoint(slide=7, code_theme="nord")

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
