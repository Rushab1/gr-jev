"""Tests for grjev.distribution."""

import pytest

from grjev.constants import NONE_NAME
from grjev.distribution import (
    Kind,
    correct_names,
    distribution,
    ece,
    kind_of,
    parted,
    positions,
    rounded,
    second_after_removal,
    yes_figures,
)
from grjev.runs import ListAnswer, Row


def answer(probabilities: dict[str, float], correct: bool = False, choice: str | None = None) -> ListAnswer:
    """An answer whose prediction is the first option with the highest probability, unless a choice is given."""
    selected = choice or max(probabilities, key=lambda name: probabilities[name])
    return ListAnswer(
        candidates=list(probabilities), choice=selected, probabilities=probabilities, confidence=1.0, correct=correct
    )


def row(labels: list[str], answers: dict[str, ListAnswer], yes: dict[str, float] | None = None) -> Row:
    return Row(id="set/file/0", test_file="file", labels=labels, answers=answers, input_tokens=10, yes=yes or {})


def test_the_calibration_error_weights_the_distance_of_each_bin_by_its_answers() -> None:
    pairs = [(0.95, True), (0.95, False), (0.55, True), (0.0, False)]
    # 0.9 to 1.0: confidence 0.95, accuracy 0.50. 0.5 to 0.6: confidence 0.55, accuracy 1.00. The first bin holds 0.
    assert ece(pairs) == pytest.approx(2 / 4 * 0.45 + 1 / 4 * 0.45 + 1 / 4 * 0.0)
    assert ece([(1.0, True)] * 3) == 0.0
    # A confidence on an edge is in the bin below it: 0.1 is in the first bin with 0.05.
    assert ece([(0.1, False), (0.05, False)], bins=10) == pytest.approx(0.075)
    assert ece([(0.1, False), (0.05, False)], bins=1) == pytest.approx(0.075)


def test_the_correct_options_of_a_list_are_the_labels_it_holds_or_none_when_it_holds_no_label() -> None:
    full = answer({"a": 0.6, "b": 0.3, "c": 0.1})
    assert correct_names(row(["a", "b"], {}), full) == ["a", "b"]
    assert correct_names(row(["a", "d"], {}), full) == ["a"]
    # No label is held: a list with "None" has it as its correct option, and a list without it has none.
    assert correct_names(row([], {}), answer({"a": 0.6, NONE_NAME: 0.4})) == [NONE_NAME]
    assert correct_names(row(["d"], {}), full) == []
    # "None" is a distractor of a list that holds a label.
    assert correct_names(row(["a"], {}), answer({"a": 0.6, NONE_NAME: 0.4})) == ["a"]


def test_an_answer_is_parted_into_correct_options_and_distractors_from_the_highest_down() -> None:
    part = parted(row(["b", "d"], {}), answer({"a": 0.1, "b": 0.2, "c": 0.3, "d": 0.4}))
    assert (part.correct, part.distractors, part.hit) == ((0.4, 0.2), (0.3, 0.1), True)
    assert not parted(row(["b"], {}), answer({"a": 0.5, "b": 0.5})).hit
    # The prediction is the field `choice`, also where another option has a higher probability.
    assert parted(row(["b"], {}), answer({"a": 0.51, "b": 0.49}, choice="b")).hit


def test_the_kind_of_some_lists_follows_their_correct_options_and_distractors() -> None:
    one = parted(row(["a"], {}), answer({"a": 0.6, "b": 0.4}))
    two = parted(row(["a", "b"], {}), answer({"a": 0.6, "b": 0.3, "c": 0.1}))
    only = parted(row(["a", "b"], {}), answer({"a": 0.6, "b": 0.4}))
    none = parted(row([], {}), answer({"a": 0.6, "b": 0.4}))
    assert [kind_of([part]) for part in (one, two, only, none)] == [Kind.ONE, Kind.SEVERAL, Kind.ALL, Kind.NONE]
    assert kind_of([two, only]) == kind_of([one, two]) == kind_of([two, none]) == Kind.SEVERAL


def test_the_figures_of_lists_with_several_correct_options_leave_out_a_list_without_a_distractor() -> None:
    split = (row(["a", "b"], {}), answer({"a": 0.6, "c": 0.3, "b": 0.1}))
    exact = (row(["a", "b"], {}), answer({"c": 0.1, "b": 0.4, "a": 0.5}, correct=True))
    only = (row(["a", "b"], {}), answer({"a": 0.9, "b": 0.1}, correct=True))
    found = distribution([split, exact, only])
    assert (found.kind, found.answers, found.measured) == (Kind.SEVERAL, 3, 2)
    assert (found.options, found.correct_options) == ((2, 3), (2, 2))
    assert (found.accuracy, found.exact_match) == (1.0, pytest.approx(2 / 3))
    assert found.confidence == pytest.approx(2.0 / 3)
    assert found.overconfidence == pytest.approx(2.0 / 3 - 1.0)
    assert found.runner_up == pytest.approx((0.3 + 0.1 + 0.8) / 3)
    # The two lists with a distractor: 0.6 and 0.1 against 0.3, then 0.5 and 0.4 against 0.1.
    assert found.spread == pytest.approx((0.5 + 0.1) / 2)
    assert found.lowest_margin == pytest.approx((-0.2 + 0.3) / 2)
    assert found.highest_margin == pytest.approx((0.3 + 0.4) / 2)
    assert found.ranked_correct == pytest.approx((0.55, 0.25))
    assert (found.highest_correct, found.lowest_correct) == (pytest.approx(0.55), pytest.approx(0.25))
    assert found.highest_distractor == pytest.approx(0.2)
    # The lowest correct option is above 0.25 in one of the two lists with a distractor: 0.1 and 0.4.
    assert found.every_correct_above == 0.5
    assert found.by_position is None and found.predicted_at is None


def test_the_correct_options_are_not_ranked_when_their_number_differs() -> None:
    two = (row(["a", "b"], {}), answer({"a": 0.6, "b": 0.3, "c": 0.1}))
    three = (row(["a", "b", "c"], {}), answer({"a": 0.4, "b": 0.3, "c": 0.2, "d": 0.1}))
    found = distribution([two, three])
    assert found.ranked_correct is None and found.correct_options == (2, 3)
    assert (found.highest_correct, found.lowest_correct) == (pytest.approx(0.5), pytest.approx(0.25))


def test_lists_of_duplicates_have_no_accuracy_and_give_the_probability_at_each_position() -> None:
    first = (row(["a", "b", "c"], {}), answer({"a": 0.7, "b": 0.2, "c": 0.1}))
    second = (row(["a", "b", "c"], {}), answer({"b": 0.5, "c": 0.1, "a": 0.4}))
    found = distribution([first, second])
    assert found.kind is Kind.ALL and found.measured == 2
    assert (found.accuracy, found.overconfidence, found.ece, found.exact_match) == (None, None, None, None)
    assert (found.lowest_margin, found.highest_margin, found.highest_distractor) == (None, None, None)
    assert found.every_correct_above is None
    assert found.spread == pytest.approx((0.6 + 0.4) / 2)
    assert found.ranked_correct == pytest.approx((0.6, 0.3, 0.1))
    assert found.by_position == pytest.approx((0.6, 0.15, 0.25))
    assert found.predicted_at == (2, 0, 0)


def test_lists_with_no_correct_option_have_accuracy_0_and_only_distractors() -> None:
    found = distribution([(row([], {}), answer({"a": 0.7, "b": 0.3})), (row(["d"], {}), answer({"a": 0.5, "b": 0.5}))])
    assert (found.kind, found.accuracy, found.exact_match) == (Kind.NONE, 0.0, None)
    assert found.confidence == found.overconfidence == found.highest_distractor == pytest.approx(0.6)
    assert found.ece == pytest.approx(0.6)
    assert (found.spread, found.lowest_margin, found.ranked_correct, found.highest_correct) == (None,) * 4


def test_none_is_the_correct_option_of_a_list_that_holds_no_label() -> None:
    selected = (row([], {}), answer({"a": 0.2, NONE_NAME: 0.8}))
    missed = (row([], {}), answer({"a": 0.7, NONE_NAME: 0.3}))
    found = distribution([selected, missed])
    assert (found.kind, found.accuracy, found.correct_options) == (Kind.ONE, 0.5, (1, 1))
    assert found.lowest_margin == found.highest_margin == pytest.approx((0.6 - 0.4) / 2)
    assert (found.spread, found.exact_match) == (pytest.approx(0.0), None)


def test_positions_are_given_only_when_every_list_has_the_same_length() -> None:
    short, long = answer({"a": 0.6, "b": 0.4}), answer({"a": 0.5, "b": 0.3, "c": 0.2})
    assert positions([short, long]) is None
    assert positions([short, answer({"b": 0.1, "a": 0.9})]) == (pytest.approx((0.35, 0.65)), (1, 1))


def test_rounding_removes_the_float_noise_of_a_probability() -> None:
    noisy = row(["a"], {"own": answer({"a": 0.33999999999999997, "b": 0.34, "c": 0.32})})
    assert rounded(noisy).answers["own"].probabilities == {"a": 0.34, "b": 0.34, "c": 0.32}
    assert noisy.answers["own"].probabilities["a"] != 0.34


def test_the_second_correct_option_is_followed_into_the_list_without_the_top_one() -> None:
    answers = {
        "full": answer({"a": 0.2, "b": 0.7, "c": 0.1}),
        "without_1": answer({"b": 0.8, "c": 0.2}),
        "without_2": answer({"a": 0.6, "c": 0.4}),
    }
    refused = {name: given for name, given in answers.items() if name != "without_2"}
    one_label = row(["a"], {"full": answers["full"]})
    # The top correct option is b, the second label, so the list without it is `without_2`.
    found = second_after_removal([row(["a", "b"], answers), one_label])
    assert found is not None and (found.before, found.after, found.examples) == (0.2, 0.6, 1)
    # The options other than b hold 0.3 of the full list, and a holds 0.2 of it.
    assert found.renormalised == pytest.approx(2 / 3) and found.shared == 1
    assert second_after_removal([row(["a", "b"], refused), one_label]) is None


def test_an_example_whose_top_correct_option_has_all_the_probability_has_no_renormalised_value() -> None:
    answers = {"full": answer({"a": 0.0, "b": 1.0, "c": 0.0}), "without_2": answer({"a": 0.6, "c": 0.4})}
    found = second_after_removal([row(["a", "b"], answers)])
    assert found is not None and (found.before, found.after, found.examples) == (0.0, 0.6, 1)
    assert found.renormalised is None and found.shared == 0


def test_yes_no_answers_are_counted_for_correct_options_and_for_distractors() -> None:
    rows = [
        row(["a", "b"], {}, yes={"a": 0.9, "b": 0.5, "c": 0.1}),
        row(["a"], {}, yes={"a": 0.2, "c": 0.7}),
    ]
    found = yes_figures(rows)
    assert (found.correct, found.correct_mean, found.correct_yes) == (3, pytest.approx(1.6 / 3), 2)
    assert (found.distractors, found.distractor_mean, found.distractor_yes) == (2, pytest.approx(0.4), 1)
    empty = yes_figures([row(["a"], {})])
    assert (empty.correct, empty.correct_mean, empty.distractors, empty.distractor_mean) == (0, None, 0, None)
