"""How `Shuffled` picks `random`'s transitions on stage: a shuffled deck per tuple of options, never repeating."""

import random
from collections.abc import Iterable
from itertools import batched
from itertools import pairwise

import pytest

from whats_new.components.transitions import Shuffled

OPTIONS = ("iris", "wipe", "melt", "rain", "cube")
SEEDS = range(40)


def cycles(dealt: Iterable[str], size: int) -> list[list[str]]:
    """`dealt` cut into runs of `size`, each sorted, so a run that deals every option once matches the options sorted."""
    return [sorted(cycle) for cycle in batched(dealt, size, strict=True)]


@pytest.mark.parametrize("seed", SEEDS)
def test_every_option_is_dealt_once_before_any_comes_round_again(seed: int) -> None:
    choose = Shuffled[str](random.Random(seed))

    dealt = [choose(OPTIONS) for _ in range(len(OPTIONS) * 6)]

    assert cycles(dealt, len(OPTIONS)) == [sorted(OPTIONS)] * 6


@pytest.mark.parametrize("seed", SEEDS)
def test_no_option_is_dealt_twice_in_a_row_across_a_reshuffle(seed: int) -> None:
    choose = Shuffled[str](random.Random(seed))

    dealt = [choose(OPTIONS) for _ in range(len(OPTIONS) * 20)]

    assert [(first, second) for first, second in pairwise(dealt) if first == second] == []


@pytest.mark.parametrize("seed", SEEDS)
def test_each_tuple_of_options_is_dealt_from_a_deck_of_its_own(seed: int) -> None:
    others = ("zoom", "deal", "fold")
    choose = Shuffled[str](random.Random(seed))

    dealt = [(choose(OPTIONS), choose(others)) for _ in range(len(OPTIONS) * len(others))]

    assert cycles((first for first, _ in dealt), len(OPTIONS)) == [sorted(OPTIONS)] * 3
    assert cycles((second for _, second in dealt), len(others)) == [sorted(others)] * 5


def test_a_lone_option_is_dealt_every_time() -> None:
    choose = Shuffled[str](random.Random(315))

    assert [choose(("swipe",)) for _ in range(4)] == ["swipe"] * 4
