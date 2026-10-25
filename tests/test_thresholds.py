"""Tests for grjev.thresholds."""

import math

import pytest

from grjev.constants import JEV_MODEL
from grjev.runs import ListAnswer, Row
from grjev.thresholds import (
    best,
    detail_cells,
    embolden,
    exact,
    f1,
    other_recall,
    paired,
    paper_table,
    precision,
    ranked,
    recall,
)

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
    listed, asked = paired(lists, ("full",), [row(["a", "b"], {}, yes, [])])
    assert listed == [[[(0.9, True), (0.07, True), (0.03, False)]]] and asked == [
        [[(0.95, True), (0.6, True), (0.1, False)]]
    ]
    assert paired(lists, ("full",), [row(["a", "b"], {}, yes, ["c"])]) == ([], [])
    one = [row(["a"], {"full": answer(probabilities)}, {}, [])]
    assert paired(one, ("full",), [row(["a"], {}, yes, [])]) == ([], [])
    with pytest.raises(ValueError, match="options of its lists"):
        paired(lists, ("full",), [row(["a", "b"], {}, {"a": 0.9, "z": 0.1}, [])])


def test_without_names_every_answered_list_of_an_example_is_kept_together_and_its_yes_no_questions_once() -> None:
    orders = {"r0": answer({"a": 0.9, "b": 0.07, "c": 0.03}), "r1": answer({"c": 0.2, "a": 0.5, "b": 0.3})}
    lists = [row(["a", "b"], orders, {}, ["r2"])]
    listed, asked = paired(lists, None, [row(["a", "b"], {}, {"a": 0.95, "b": 0.6, "c": 0.1}, [])])
    assert listed == [[[(0.9, True), (0.07, True), (0.03, False)], [(0.2, False), (0.5, True), (0.3, True)]]]
    assert asked == [[[(0.95, True), (0.6, True), (0.1, False)]]]


def test_the_table_of_the_paper_gives_the_best_exact_set_accuracy_of_the_list_and_of_the_yes_no_questions() -> None:
    # Only the first example of FOUND can have every correct choice selected and its distractor rejected.
    lines = paper_table({("Set", JEV_MODEL): ([FOUND], [FOUND[:1]])}).splitlines()
    assert lines[2:5] == [r" & \multicolumn{2}{c}{Set} \\", r"\cmidrule(lr){2-3}", r"Model & List & Yes/no \\"]
    assert lines[6] == r"Jev & 0.50 & 1.00 \\"


# An example whose distractor is above one of its correct choices.
UNRANKED = [[(0.6, True), (0.1, True), (0.3, False)]]


def test_an_example_is_ranked_when_every_correct_choice_is_above_every_distractor() -> None:
    assert ranked(UNRANKED + FOUND) == FOUND
    assert ranked([[(0.4, True), (0.3, True), (0.3, False)]]) == []


def test_the_detail_cells_are_read_at_the_threshold_with_the_highest_exact_set_accuracy() -> None:
    # At 0.04 only the first example of FOUND is exact. 8 choices are selected, 6 of them correct.
    assert detail_cells(UNRANKED + FOUND) == ["0.04", "0.67", "0.50", "0.75", "1.00", "0.86 (0.04)"]


def test_the_highest_and_the_lowest_value_of_a_bold_column_are_in_bold() -> None:
    rows = [["0.02", "0.70", "0.50"], ["0.05", "0.80", "0.40"], ["0.02", "0.90", "0.45"]]
    embolden(rows)
    assert [row[0] for row in rows] == [r"\textbf{0.02}", r"\textbf{0.05}", r"\textbf{0.02}"]
    assert [row[1] for row in rows] == ["0.70", "0.80", "0.90"]
    assert [row[2] for row in rows] == [r"\textbf{0.50}", r"\textbf{0.40}", "0.45"]
