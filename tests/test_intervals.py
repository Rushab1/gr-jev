"""Tests for grjev.intervals."""

from grjev.intervals import exact_pairs, gap_pairs, ranked_pairs, ratio, ratio_interval
from grjev.runs import ListAnswer, Row
from grjev.thresholds import exact, top
from grjev.uniform import counted


def answer(probabilities: dict[str, float]) -> ListAnswer:
    return ListAnswer(
        candidates=list(probabilities), choice="a", probabilities=probabilities, confidence=1.0, correct=True
    )


def row(number: int, labels: list[str], answers: dict[str, ListAnswer]) -> Row:
    return Row(id=f"set/file/{number}", test_file="file", labels=labels, answers=answers, input_tokens=10)


def test_the_interval_of_equal_pairs_is_their_ratio_and_a_mixed_interval_holds_the_ratio() -> None:
    assert ratio_interval([(0.5, 1.0)] * 20) == (0.5, 0.5)
    pairs = [(float(number % 3 == 0), 1.0) for number in range(60)]
    low, high = ratio_interval(pairs)
    assert low < ratio(pairs) < high
    assert ratio_interval(pairs) == (low, high)


def test_the_gaps_of_an_example_are_summed_over_its_answers_and_lists_without_a_distractor_are_left_out() -> None:
    first = row(0, ["a", "b"], {})
    second = row(1, ["a", "b"], {})
    answers = [
        (first, answer({"a": 0.7, "b": 0.2, "c": 0.1})),
        (first, answer({"a": 0.5, "b": 0.4, "c": 0.1})),
        (second, answer({"a": 0.6, "b": 0.3, "c": 0.1})),
        (second, answer({"a": 0.9, "b": 0.1})),
    ]
    found = gap_pairs(answers)
    assert [(round(above, 2), below) for above, below in found] == [(0.6, 2), (0.3, 1)]
    assert round(ratio(found), 2) == 0.3


def test_a_list_of_copies_with_no_distractor_counts_every_answer() -> None:
    copies = row(0, ["a", "b", "c"], {})
    found = gap_pairs([(copies, answer({"a": 0.6, "b": 0.3, "c": 0.1}))])
    assert [(round(above, 2), below) for above, below in found] == [(0.5, 1)]


def test_the_ranked_shares_are_those_of_the_counts_below_one_over_n() -> None:
    rows = [
        row(0, ["a", "b"], {"full": answer({"a": 0.9, "b": 0.06, "c": 0.04})}),
        row(1, ["a", "b"], {"full": answer({"a": 0.4, "b": 0.4, "c": 0.2})}),
        row(2, ["a", "b"], {"full": answer({"a": 0.5, "b": 0.1, "c": 0.4})}),
        row(3, ["a", "b"], {"full": answer({"a": 0.9, "b": 0.1})}),
    ]
    good, low = ranked_pairs(rows, "full")
    found = counted(rows, "full")
    assert ratio(good) == found.ranked / found.lists
    assert ratio(low) == found.ranked_below / found.ranked


def test_the_exact_sets_use_the_best_threshold_of_all_the_examples() -> None:
    found = [
        [(0.6, True), (0.3, True), (0.1, False)],
        [(0.8, True), (0.15, True), (0.05, False)],
        [(0.5, True), (0.5, False)],
    ]
    t, best = top(found, exact)
    assert ratio(exact_pairs(found)) == best == exact(found, t)
