"""
Animations, driven by the app's clock through counterweight's `use_progress` and `use_loop`, so the export's frozen
clock holds them still and its `AdvanceClock` moves them on deterministically.

Two kinds, which start differently:
- An explanatory animation plays once and holds its last frame (`use_explanation`). It starts when its component
  mounts, so a slide starts one from a key by keying the component on the reveal step: Space remounts it, which
  plays it.
- A decorative one loops for as long as its slide is the live one, from arrival: `use_loop` with `is_playing`.

Neither runs off the live slide: a thumbnail shows an explanatory animation's last frame and a decorative one's
first, and ticks no clock for either, since nine thumbnails animating at once would cost frame time for nothing.
The exceptions are a title card's turning border (see `title_card`), which turns in the slide grid too,
and the grid's selected thumbnail, whose border turns the same way (see `grid.thumbnail`).

Every animation counts from its component's mount, never the app's start, so a headless render of a slide
moved on by however long it has been mounted (see `crossing.photograph`) draws what the live slide does.
"""

from datetime import timedelta

from counterweight.hooks import use_progress


def use_explanation(duration: timedelta, is_live: bool) -> float:
    """
    How far through an explanatory animation `duration` long the calling component is: rising from 0 at mount to 1,
    where it holds, on the live slide, and 1 at once anywhere else, as an animation with no duration is.
    """
    return use_progress(duration if is_live else timedelta())
