"""Tests for grjev.uniform."""

import pytest

from grjev.runs import ListAnswer, Row
from grjev.uniform import by_labels, correct_below, counted, ranked_correctly


def answer(probabilities: dict[str, float]) -> ListAnswer:
    return ListAnswer(
        candidates=list(probabilities), choice="a", probabilities=probabilities, confidence=1.0, correct=True
    )


def row(labels: list[str], answers: dict[str, ListAnswer], refused: list[str] | None = None) -> Row:
    return Row(
        id="set/file/0", test_file="file", labels=labels, answers=answers, input_tokens=10, refused=refused or []
    )


def test_a_correct_option_counts_when_its_probability_is_strictly_below_one_over_the_number_of_options() -> None:
    # 4 options: 1/n is 0.25. "b" at 0.25 is not below it, "c" at 0.05 is.
    found = answer({"a": 0.7, "b": 0.25, "c": 0.05, "d": 0.0})
    assert correct_below(["a", "b", "c"], found) == ["c"]
    # A float a step below 0.1 is 0.1.
    ten = {name: 0.1 for name in "abcdefghi"} | {"j": 0.09999999999999999}
    assert correct_below(["j"], answer(ten)) == []


def test_a_list_without_a_label_or_without_a_probability_raises() -> None:
    with pytest.raises(ValueError, match="labels"):
        correct_below(["z"], answer({"a": 0.5, "b": 0.5}))
    broken = ListAnswer(
        candidates=["a", "b", "c"], choice="a", probabilities={"a": 1.0, "b": 0.0}, confidence=1.0, correct=True
    )
    with pytest.raises(ValueError, match="probabilities"):
        correct_below(["a"], broken)


def test_the_counts_keep_lists_with_two_labels_and_a_distractor_and_count_refusals() -> None:
    rows = [
        row(["a", "b"], {"full": answer({"a": 0.9, "b": 0.06, "c": 0.04})}),
        row(["a", "b"], {"full": answer({"a": 0.4, "b": 0.4, "c": 0.2})}),
        # No distractor, one label, and a refusal.
        row(["a", "b"], {"full": answer({"a": 0.9, "b": 0.1})}),
        row(["a"], {"full": answer({"a": 0.9, "b": 0.05, "c": 0.05})}),
        row(["a", "b"], {}, refused=["full"]),
    ]
    found = counted(rows, "full")
    assert (found.lists, found.refused, found.correct, found.below, found.lists_below) == (2, 1, 4, 1, 1)
    assert (found.ranked, found.ranked_below) == (2, 1)


def test_a_list_is_ranked_correctly_when_every_label_is_strictly_above_every_distractor() -> None:
    assert ranked_correctly(["a", "b"], answer({"a": 0.6, "b": 0.3, "c": 0.1}))
    assert not ranked_correctly(["a", "b"], answer({"a": 0.6, "b": 0.2, "c": 0.2}))
    assert not ranked_correctly(["a", "b"], answer({"a": 0.6, "b": 0.1, "c": 0.3}))


def test_a_list_with_no_answer_and_no_refusal_raises() -> None:
    with pytest.raises(ValueError, match="no answer"):
        counted([row(["a", "b"], {})], "full")


def test_the_rows_are_grouped_by_their_number_of_labels() -> None:
    rows = [row(["a", "b", "c"], {}), row(["a", "b"], {}), row(["a", "b", "d"], {})]
    assert {number: len(own) for number, own in by_labels(rows).items()} == {2: 1, 3: 2}
