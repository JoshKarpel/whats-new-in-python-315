"""The recording's walk through the deck: a chapter per slide, and only the runs this machine can do."""

import json
from pathlib import Path

from counterweight.controls import Marker
from counterweight.events import KeyPressed
from counterweight.keys import Key

from whats_new.deck import SLIDES
from whats_new.host import Host
from whats_new.recording import presented
from whats_new.recording import record
from whats_new.runs import Capability
from whats_new.runs import Expect
from whats_new.runs import Run
from whats_new.slides import Slide
from whats_new.slides import TitleCard


async def test_the_recording_marks_a_chapter_per_slide_in_order(host: Host, tmp_path: Path) -> None:
    # Title cards, which run nothing, so this records in the time it takes to render.
    slides = tuple(slide for slide in SLIDES if slide.title_card is TitleCard.SECTION)[:3]
    path = tmp_path / "deck.cast"

    await record(slides, host, frozenset(), path)

    events = [json.loads(line) for line in path.read_text().splitlines()[1:]]
    assert [data for _, code, data in events if code == "m"] == [
        f"{index + 1}. {slide.title}" for index, slide in enumerate(slides)
    ]


async def test_the_recording_ends_with_the_deck_quitting(host: Host, tmp_path: Path) -> None:
    path = tmp_path / "deck.cast"

    await record(SLIDES[:1], host, frozenset(), path)

    assert json.loads(path.read_text().splitlines()[-1])[1:] == ["x", "0"]


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
