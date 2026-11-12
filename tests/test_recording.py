"""The recording's walk through the deck: a chapter per slide, and only the runs this machine can do."""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from counterweight import app
from counterweight.autopilot import WaitFor
from counterweight.controls import AdvanceClock
from counterweight.controls import Marker
from counterweight.controls import Quit
from counterweight.controls import Screenshot
from counterweight.events import KeyPressed
from counterweight.keys import Key

from whats_new.checkpoint import Checkpoint
from whats_new.components.code import CODE_THEMES
from whats_new.components.transitions import OFFERED
from whats_new.deck import SLIDES
from whats_new.export import EXPORT_CLOCK
from whats_new.export import SETTLE
from whats_new.host import Host
from whats_new.presenter import root
from whats_new.recording import START
from whats_new.recording import presented
from whats_new.recording import record
from whats_new.runs import Capability
from whats_new.runs import Expect
from whats_new.runs import Run
from whats_new.size import PRESENTING
from whats_new.slides import Slide


async def test_the_recording_marks_a_chapter_per_slide_in_order(host: Host, tmp_path: Path) -> None:
    # Title cards, which run nothing, so this records in the time it takes to render.
    slides = tuple(slide for slide in SLIDES if slide.is_title_card)[:3]
    path = tmp_path / "deck.cast"

    await record(slides, host, frozenset(), path)

    events = [json.loads(line) for line in path.read_text().splitlines()[1:]]
    assert [data for _, code, data in events if code == "m"] == [
        f"{index + 1}. {slide.title}" for index, slide in enumerate(slides)
    ]


async def test_the_recording_leaves_out_ghosts(host: Host, tmp_path: Path) -> None:
    first, second, third = tuple(slide for slide in SLIDES if slide.is_title_card)[:3]
    path = tmp_path / "deck.cast"

    await record((first, replace(second, is_ghost=True), third), host, frozenset(), path)

    events = [json.loads(line) for line in path.read_text().splitlines()[1:]]
    assert [data for _, code, data in events if code == "m"] == [f"1. {first.title}", f"2. {third.title}"]


async def test_the_recording_ends_with_the_deck_quitting(host: Host, tmp_path: Path) -> None:
    path = tmp_path / "deck.cast"

    await record(SLIDES[:1], host, frozenset(), path)

    assert json.loads(path.read_text().splitlines()[-1])[1:] == ["x", "0"]


def test_the_recording_presents_in_a_theme_and_transition_the_pickers_offer() -> None:
    assert (START.code_theme in CODE_THEMES, START.transition in OFFERED) == (True, True)


def slide_with_a_perf_run() -> Slide:
    run = Run(label="perf", argv=("perf",), expect=Expect(status=0, output=""), needs=frozenset({Capability.PERF}))
    return Slide(title="Frame pointers", content=lambda props: SLIDES[0].content(props), runs=(run,))


def test_a_run_this_machine_cant_do_is_left_out() -> None:
    steps = list(presented((slide_with_a_perf_run(),), capabilities=frozenset()))

    assert KeyPressed(key="1") not in steps


def test_a_run_this_machine_can_do_is_run() -> None:
    steps = list(presented((slide_with_a_perf_run(),), capabilities=frozenset({Capability.PERF})))

    assert KeyPressed(key="1") in steps


def test_a_slides_chapter_starts_once_the_deck_arrives_on_it() -> None:
    steps = list(presented(SLIDES[:2], capabilities=frozenset()))

    assert steps.index(Marker(label=f"2. {SLIDES[1].title}")) == steps.index(KeyPressed(key=Key.Right)) + 1


ANIMATED = [
    (index, step)
    for index, slide in enumerate(SLIDES)
    for step in range(slide.steps)
    if slide.ends_showing(step) is not None
]


@pytest.mark.parametrize(("index", "step"), ANIMATED, ids=[f"{SLIDES[i].title}, step {s}" for i, s in ANIMATED])
async def test_an_animation_shows_its_end_only_once_it_has_played(host: Host, index: int, step: int) -> None:
    frames: list[str] = []
    await app(
        root(SLIDES, host, Checkpoint(slide=index), lambda checkpoint: None),
        headless=True,
        dimensions=PRESENTING.dimensions,
        autopilot=(
            *(key for _ in range(step) for key in (AdvanceClock(by=SETTLE), KeyPressed(key=Key.Space))),
            Screenshot(handler=lambda frame: frames.append(frame.text(ansi=False))),
            AdvanceClock(by=SETTLE),
            Screenshot(handler=lambda frame: frames.append(frame.text(ansi=False))),
            Quit(),
        ),
        clock=EXPORT_CLOCK,
    )

    end = SLIDES[index].ends_showing(step)
    assert end is not None
    assert (end in frames[0], end in frames[1]) == (False, True)


def test_the_recording_waits_for_each_animation_to_end_before_holding_on_it() -> None:
    # Animated on every step after the first, and without runs, whose waits would count too.
    slide = next(slide for slide in SLIDES if slide.title == "serialize_iterator or concurrent_tee")
    steps = list(presented((slide,), capabilities=frozenset()))

    after_space = [steps[i + 1] for i, step in enumerate(steps) if step == KeyPressed(key=Key.Space)]
    assert [isinstance(step, WaitFor) for step in after_space] == [True] * (slide.steps - 1)
