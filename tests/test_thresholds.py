"""Tests for grjev.thresholds."""

import math

import pytest

from grjev.constants import JEV_MODEL
from grjev.runs import ListAnswer, Row
from grjev.thresholds import best, exact, f1, other_recall, paired, paper_table, precision, recall

# Two examples with two correct choices each: a list that puts most of its probability on one correct choice, and
# one that gives both correct choices more than a distractor.
FOUND = [
    [(0.9, True), (0.07, True), (0.03, False)],
    [(0.5, True), (0.3, True), (0.2, False)],
]


def row(labels: list[str], answers: dict[str, ListAnswer], yes: dict[str, float], refused: list[str]) -> Row:
    return Row(
        id="set/file/0", test_file="file", labels=labels, answers=answers, input_tokens=10, yes=yes, refused=refused
    )


def answer(probabilities: dict[str, float]) -> ListAnswer:
    return ListAnswer(
        candidates=list(probabilities), choice="a", probabilities=probabilities, confidence=1.0, correct=True
    )


def test_exact_set_accuracy_needs_every_correct_choice_at_or_above_t_and_every_distractor_below() -> None:
    assert exact(FOUND, 0.0) == 0.0
    assert exact(FOUND, 0.05) == 0.5
    assert exact(FOUND, 0.25) == 0.5
    assert exact(FOUND, 0.31) == 0.0


def test_precision_recall_and_f1_pool_the_choices_of_all_examples() -> None:
    # At 0.25: 0.9, 0.5 and 0.3 are selected, all correct, of 4 correct choices.
    assert (precision(FOUND, 0.25), recall(FOUND, 0.25)) == (1.0, 0.75)
    assert f1(FOUND, 0.25) == pytest.approx(2 * 0.75 / 1.75)
    assert math.isnan(precision(FOUND, 0.95)) and f1(FOUND, 0.95) == 0.0


def test_the_recall_of_the_other_correct_choices_leaves_out_the_highest_correct_choice() -> None:
    assert recall(FOUND, 0.5) == 0.5 and other_recall(FOUND, 0.5) == 0.0
    assert other_recall(FOUND, 0.25) == 0.5


def test_the_best_value_is_given_with_the_lowest_threshold_that_reaches_it() -> None:
    assert best(FOUND, exact) == "0.50 (0.04)"


def test_an_example_counts_with_two_labels_a_distractor_and_every_yes_no_question_answered() -> None:
    probabilities = {"a": 0.9, "b": 0.07, "c": 0.03}
    yes = {"a": 0.95, "b": 0.6, "c": 0.1}
    lists = [row(["a", "b"], {"full": answer(probabilities)}, {}, [])]
    listed, asked = paired(lists, "full", [row(["a", "b"], {}, yes, [])])
    assert listed == [[(0.9, True), (0.07, True), (0.03, False)]] and asked == [
        [(0.95, True), (0.6, True), (0.1, False)]
    ]
    assert paired(lists, "full", [row(["a", "b"], {}, yes, ["c"])]) == ([], [])
    one = [row(["a"], {"full": answer(probabilities)}, {}, [])]
    assert paired(one, "full", [row(["a"], {}, yes, [])]) == ([], [])
    with pytest.raises(ValueError, match="options of its list"):
        paired(lists, "full", [row(["a", "b"], {}, {"a": 0.9, "z": 0.1}, [])])


def test_the_table_of_the_paper_gives_the_best_exact_set_accuracy_of_the_list_and_of_the_yes_no_questions() -> None:
    # Only the first example of FOUND can have every correct choice selected and its distractor rejected.
    lines = paper_table({("Set", JEV_MODEL): (FOUND, FOUND[:1])}).splitlines()
    assert lines[2:5] == [r" & \multicolumn{2}{c}{Set} \\", r"\cmidrule(lr){2-3}", r"Model & List & Yes/no \\"]
    assert lines[6] == r"Jev & 0.50 & 1.00 \\"
