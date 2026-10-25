"""Tests for grjev.annotators on examples written by hand."""

import math

from grjev.annotators import (
    Answer,
    annotator_ece,
    binned,
    entropy,
    figures,
    gap,
    gap_bins,
    jensen_shannon,
    original_label,
    reliability_bins,
    shares_of,
)

NLI = {"example": {"premise": "p", "hypothesis": "h"}, "label_dist": [0.58, 0.41, 0.01], "old_label": "n"}
ALPHA = {"example": {"hyp1": "It rained.", "hyp2": "Jo swam."}, "label_dist": [0.09, 0.91], "old_label": 2}
SHARES = {"entailment": 0.58, "neutral": 0.41, "contradiction": 0.01}


def answer(probabilities: dict[str, float], example: str = "a") -> Answer:
    return Answer(example, SHARES, probabilities, "neutral")


def test_the_shares_are_named_by_the_label_or_by_the_hypothesis() -> None:
    assert shares_of(NLI) == SHARES
    assert shares_of(ALPHA) == {"It rained.": 0.09, "Jo swam.": 0.91}


def test_the_original_label_is_named_the_way_it_is_sent_to_the_model() -> None:
    assert original_label(NLI) == "neutral"
    assert original_label(ALPHA) == "Jo swam."


def test_the_entropy_is_in_bits() -> None:
    assert entropy({"a": 1.0}) == 0
    assert math.isclose(entropy({"a": 0.5, "b": 0.5}), 1.0)


def test_the_jensen_shannon_distance_is_zero_for_the_same_distribution_and_one_for_disjoint_ones() -> None:
    assert math.isclose(jensen_shannon(SHARES, SHARES), 0, abs_tol=1e-9)
    assert math.isclose(jensen_shannon({"a": 1.0, "b": 0.0}, {"a": 0.0, "b": 1.0}), math.sqrt(math.log(2)))


def test_the_gap_follows_the_order_of_the_annotators_and_is_negative_for_the_minority_label() -> None:
    assert math.isclose(gap(SHARES, SHARES), 0.17)
    assert math.isclose(gap(SHARES, {"entailment": 0.03, "neutral": 0.97, "contradiction": 0.0}), -0.94)


def test_figures_count_each_answer_to_each_order_and_every_example_once() -> None:
    answers = [answer({"entailment": 0.03, "neutral": 0.97}), answer({"entailment": 0.6, "neutral": 0.4})]
    result = figures([*answers, answer({"entailment": 1.0}, "b")])
    assert (result.examples, result.answers) == (2, 3)
    # The annotators' label is entailment, which two answers choose. The original label is neutral, which one chooses.
    assert math.isclose(result.majority, 2 / 3) and math.isclose(result.original, 1 / 3)
    assert math.isclose(result.annotator_top, 0.58) and math.isclose(result.model_top, (0.97 + 0.6 + 1.0) / 3)


def test_a_bin_holds_the_pairs_whose_first_value_falls_in_it_and_empty_bins_are_left_out() -> None:
    bins = binned([(0.05, 0.2), (0.15, 0.4), (0.15, 0.6)])
    assert [(part.low, part.count) for part in bins] == [(0.0, 1), (0.1, 2)]
    assert math.isclose(bins[1].mean, 0.15) and math.isclose(bins[1].observed, 0.5)


def test_the_last_bin_holds_a_value_of_one() -> None:
    assert [part.low for part in binned([(1.0, 1.0)])] == [0.9]


def test_the_reliability_bins_hold_one_pair_per_label_and_the_gap_bins_one_per_answer() -> None:
    held = [answer({"entailment": 0.03, "neutral": 0.97, "contradiction": 0.0})]
    assert sum(part.count for part in reliability_bins(held)) == 3
    gaps = gap_bins(held)
    assert [part.count for part in gaps] == [1]
    assert math.isclose(gaps[0].mean, 0.17) and math.isclose(gaps[0].observed, 0.94)


def test_the_ece_weights_each_bin_by_its_labels() -> None:
    bins = binned([(0.05, 0.25), (0.95, 0.65), (0.95, 0.65), (0.95, 0.65)])
    assert math.isclose(annotator_ece(bins), (0.2 + 3 * 0.3) / 4)


def test_a_uniform_distribution_is_at_zero_distance_from_equal_shares() -> None:
    equal = {"entailment": 1 / 3, "neutral": 1 / 3, "contradiction": 1 / 3}
    found = figures([Answer("a", equal, equal, "neutral")])
    assert (
        math.isclose(found.uniform_jsd, 0.0, abs_tol=1e-9) and found.uniform_jsd < figures([answer(SHARES)]).uniform_jsd
    )
