"""Tests for grjev.reliability."""

import pytest

from grjev.distribution import YesBin
from grjev.reliability import yes_ece

# 80 answers near 0 that are calibrated, and 20 answers at 0.15 of which 0.45 are about a correct choice.
BINS = [YesBin(0.0, 0.1, 80, 0.02, 0.02), YesBin(0.1, 0.2, 20, 0.15, 0.45), None]


def test_yes_ece_weights_each_bin_by_its_answers() -> None:
    assert yes_ece(BINS) == pytest.approx(0.2 * 0.30)


def test_yes_ece_without_the_first_bin_weights_the_other_bins_by_their_own_answers() -> None:
    assert yes_ece(BINS, 1) == pytest.approx(0.30)
