"""The whole deck, in running order."""

from whats_new.sections import closing
from whats_new.sections import concurrency
from whats_new.sections import lightning
from whats_new.sections import opening
from whats_new.sections import performance
from whats_new.sections import small_things
from whats_new.sections import startup
from whats_new.sections import static_typing
from whats_new.sections import upgrade
from whats_new.slides import Slide

SLIDES: tuple[Slide, ...] = (
    *opening.SLIDES,
    *small_things.SLIDES,
    *startup.SLIDES,
    *concurrency.SLIDES,
    *static_typing.SLIDES,
    *performance.SLIDES,
    *upgrade.SLIDES,
    *lightning.SLIDES,
    *closing.SLIDES,
)
