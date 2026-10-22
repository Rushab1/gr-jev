"""Tests for grjev.annotators on examples written by hand."""

import math

from grjev.annotators import distance, figures, gap, is_split, shares_of

SPLIT = {"entailment": 0.58, "neutral": 0.41, "contradiction": 0.01}
CLEAR = {"entailment": 0.8, "neutral": 0.15, "contradiction": 0.05}


def test_the_shares_are_named_by_the_label_or_by_the_hypothesis() -> None:
    nli = {"example": {"premise": "p", "hypothesis": "h"}, "label_dist": [0.58, 0.41, 0.01]}
    alpha = {"example": {"hyp1": "It rained.", "hyp2": "Jo swam."}, "label_dist": [0.09, 0.91]}
    assert shares_of(nli) == SPLIT
    assert shares_of(alpha) == {"It rained.": 0.09, "Jo swam.": 0.91}


def test_the_gap_follows_the_order_of_the_annotators_and_is_negative_for_the_minority_label() -> None:
    assert math.isclose(gap(SPLIT, SPLIT), 0.17)
    assert math.isclose(gap(SPLIT, {"entailment": 0.03, "neutral": 0.97, "contradiction": 0.0}), -0.94)


def test_the_distance_is_half_the_sum_of_the_absolute_differences() -> None:
    assert math.isclose(distance(SPLIT, {"neutral": 1.0}), 0.59)
    assert distance(SPLIT, SPLIT) == 0


def test_an_example_is_split_when_two_labels_have_at_least_30_percent() -> None:
    assert is_split(SPLIT) and not is_split(CLEAR)


def test_figures_count_each_answer_to_each_order() -> None:
    answers = [{"entailment": 0.03, "neutral": 0.97, "contradiction": 0.0}, {"entailment": 0.6, "neutral": 0.4}]
    result = figures([(SPLIT, answers), (CLEAR, [{"entailment": 1.0}])])
    assert (result.examples, result.answers, result.split) == (2, 3, 1)
    assert math.isclose(result.model_gap, (0.94 + 0.2) / 2) and math.isclose(result.minority, 0.5)
    # 0.58 and 0.41 lie between 0.3 and 0.7. 0.97 and 0.03 are at the ends, 0.6 and 0.4 are not.
    assert result.middle_labels == 4 and math.isclose(result.middle_ends, 0.5)
    assert math.isclose(result.order_change, (0.57 + 0.57 + 0.0) / 6)
