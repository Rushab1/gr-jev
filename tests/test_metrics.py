"""Tests for grjev.metrics."""

import pytest

from grjev.constants import BOOTSTRAP_SEED, CONFIDENT_PROBABILITY, NONE_NAME, PLACEMENTS, RELEASED_ORDER
from grjev.examples import Example, Option
from grjev.metrics import compared_groups, difference, figures, interval, list_groups, list_names, row_groups
from grjev.placement import length_orders, orders_of
from grjev.runs import ListAnswer, Row

LENGTHS = (5, 10)
TOOLS = [Option(name=f"tool_{tool}", description=f"Does thing {tool}.") for tool in range(1, 11)]


def answer(choice: str, correct: bool, probabilities: dict[str, float] | None = None) -> ListAnswer:
    probabilities = probabilities or {choice: 1.0}
    candidates = list(probabilities)
    return ListAnswer(
        candidates=candidates, choice=choice, probabilities=probabilities, confidence=1.0, correct=correct
    )


def row(test_file: str, labels: list[str], answers: dict[str, ListAnswer]) -> Row:
    return Row(id="set/file/0", test_file=test_file, labels=labels, answers=answers, input_tokens=10)


def one_tool(first: bool, last: bool) -> Row:
    """An example with one correct tool, answered correctly or not with the tool first and with it last."""
    answers = {"first": answer("a" if first else "b", first), "last": answer("a" if last else "b", last)}
    return row("similar_tools", ["a"], answers)


def test_an_interval_cuts_the_resampled_means_at_both_ends_and_depends_only_on_the_values_and_the_seed() -> None:
    correct_in_38_of_50 = [1.0] * 38 + [0.0] * 12
    # Pins the method: 2,000 resamples of the examples from seed 1, and the 51st and 1,951st of the sorted means.
    assert interval(correct_in_38_of_50, seed=1) == pytest.approx((0.64, 0.88))
    assert interval(correct_in_38_of_50, seed=1) == interval(correct_in_38_of_50, seed=1)
    assert interval([0.5] * 10, seed=1) == (0.5, 0.5)


def test_figures_count_the_answers_to_the_named_lists() -> None:
    rows = [
        row(
            "similar_tools",
            ["a"],
            {
                "first": answer("a", True, {"a": 0.95, "b": 0.05, NONE_NAME: 0.0}),
                "last": answer(NONE_NAME, False, {"a": 0.4, "b": 0.0, NONE_NAME: 0.6}),
            },
        ),
        row(
            "similar_tools",
            ["a"],
            {
                "first": answer("b", False, {"a": 0.08, "b": 0.92, NONE_NAME: 0.0}),
                "last": answer("b", False, {"a": 0.5, "b": 0.5, NONE_NAME: 0.0}),
            },
        ),
    ]
    found = figures(rows, ["first", "last"], BOOTSTRAP_SEED, confident_from=0.9)
    assert (found.examples, found.answers, found.correct, found.csr) == (2, 4, 1, 25.0)
    assert (found.none, found.confident, found.confident_wrong) == (1, 2, 1)
    assert found.zero_probabilities == pytest.approx(100 * 4 / 12)
    assert (found.one_choice, found.all_correct, found.none_correct) == (1, 0, 1)
    assert (found.second_wrong, found.second_tied, found.top_wrong) == (0, 0, 0)
    assert 0 <= found.low <= found.csr <= found.high <= 50
    first_only = figures(rows, ["first"], BOOTSTRAP_SEED, confident_from=0.9)
    assert (first_only.answers, first_only.correct, first_only.csr, first_only.none) == (2, 1, 50.0, 0)


def test_a_probability_at_the_threshold_is_confident() -> None:
    rows = [row("similar_tools", ["a"], {"first": answer("a", True, {"a": CONFIDENT_PROBABILITY, "b": 0.1})})]
    assert figures(rows, ["first"], BOOTSTRAP_SEED, CONFIDENT_PROBABILITY).confident == 1
    assert figures(rows, ["first"], BOOTSTRAP_SEED, 0.95).confident == 0


def test_an_answer_that_misses_two_correct_tools_is_counted_once_by_how_it_misses() -> None:
    answers = {
        RELEASED_ORDER: answer("a", True, {"a": 0.6, "b": 0.4, "c": 0.0}),
        "adjacent_first": answer("a", False, {"a": 0.6, "c": 0.3, "b": 0.1}),
        "adjacent_quarter": answer("a", False, {"a": 0.5, "c": 0.5, "b": 0.0}),
        "adjacent_middle": answer("a", False, {"a": 0.9, "b": 0.05, "c": 0.05}),
        "adjacent_last": answer("c", False, {"a": 0.3, "b": 0.2, "c": 0.5}),
    }
    found = figures([row("multi_tool", ["a", "b"], answers)], list(answers), BOOTSTRAP_SEED, confident_from=0.9)
    assert (found.answers, found.correct) == (5, 1)
    # A wrong tool is second twice, once after a tie for first place between a correct tool and a wrong one.
    assert (found.second_wrong, found.second_tied, found.top_wrong) == (2, 1, 1)


def test_an_example_without_one_of_the_lists_is_left_out() -> None:
    placed = row("live_multiple", ["a"], {RELEASED_ORDER: answer("a", True), "first": answer("a", True)})
    no_correct_tool = row("live_multiple", [], {RELEASED_ORDER: answer("a", False)})
    assert figures([placed, no_correct_tool], [RELEASED_ORDER], BOOTSTRAP_SEED, 0.9).examples == 2
    assert figures([placed, no_correct_tool], [RELEASED_ORDER, "first"], BOOTSTRAP_SEED, 0.9).examples == 1
    assert difference([placed, no_correct_tool], [RELEASED_ORDER], ["first"], BOOTSTRAP_SEED) == (0.0, 0.0, 0.0)


def test_a_difference_is_taken_within_each_example() -> None:
    rows = [one_tool(True, False), one_tool(True, True), one_tool(False, False), one_tool(True, False)]
    points, low, high = difference(rows, ["first"], ["last"], BOOTSTRAP_SEED)
    assert points == pytest.approx(50.0)
    assert 0 <= low <= points <= high <= 100
    assert difference(rows, ["last"], ["first"], BOOTSTRAP_SEED)[0] == pytest.approx(-50.0)


def test_one_correct_tool_has_a_group_for_each_list_for_the_placements_and_for_every_list() -> None:
    one_correct = Example(id="set/file/0", query="Do the thing.", options=TOOLS, labels=["tool_4"], raw={})
    names = list(orders_of(one_correct, seed=7))
    groups = list_groups(names, LENGTHS)
    assert list(groups) == [RELEASED_ORDER, *PLACEMENTS, "5 placements", "every list"]
    assert groups["first"] == ["first"] and groups["5 placements"] == list(PLACEMENTS)
    assert groups["every list"] == names
    assert compared_groups(groups, LENGTHS) == {
        "first minus last": ("first", "last"),
        "released minus 5 placements": (RELEASED_ORDER, "5 placements"),
    }
    assert list(list_groups([RELEASED_ORDER], LENGTHS)) == [RELEASED_ORDER]
    assert compared_groups(list_groups([RELEASED_ORDER], LENGTHS), LENGTHS) == {}


def test_two_correct_tools_have_a_group_for_the_adjacent_and_for_the_separated_orders() -> None:
    two_correct = Example(id="set/file/0", query="Do the thing.", options=TOOLS, labels=["tool_7", "tool_8"], raw={})
    groups = list_groups(list(orders_of(two_correct, seed=7)), LENGTHS)
    assert [len(groups[name]) for name in ("adjacent", "separated", "every list")] == [5, 3, 9]
    assert groups["separated"][0] == "separated_first_last"
    assert compared_groups(groups, LENGTHS) == {"adjacent minus separated": ("adjacent", "separated")}


def test_a_length_run_has_a_group_for_each_list_length_and_for_each_placement() -> None:
    one_correct = Example(id="set/file/0", query="Do the thing.", options=TOOLS, labels=["tool_4"], raw={})
    names = list(length_orders(one_correct, TOOLS, LENGTHS, seed=7))
    groups = list_groups(names, LENGTHS)
    assert groups["5 tools"] == [f"5_{name}" for name in PLACEMENTS]
    assert groups["last, every length"] == ["5_last", "10_last"]
    assert len(groups) == len(names) + len(LENGTHS) + len(PLACEMENTS) + 1
    assert compared_groups(groups, LENGTHS) == {
        "5 tools minus 10 tools": ("5 tools", "10 tools"),
        "first minus last, every length": ("first, every length", "last, every length"),
    }


def test_the_wordings_of_a_wording_run_are_not_pooled_and_each_is_compared_with_the_one_before() -> None:
    groups = list_groups(["one", "all", "equal", "every"], [])
    assert groups == {"one": ["one"], "all": ["all"], "equal": ["equal"], "every": ["every"]}
    assert compared_groups(groups, []) == {
        "all minus one": ("all", "one"),
        "equal minus all": ("equal", "all"),
        "every minus equal": ("every", "equal"),
    }
    assert compared_groups(list_groups(["every"], []), []) == {}


def test_examples_are_grouped_by_test_file_and_pooled_when_all_have_the_same_lists() -> None:
    similar = row("similar_tools", ["a"], {"5_first": answer("a", True)})
    scenario = row("scenario", ["a"], {"5_first": answer("a", True)})
    reliability = row("reliability", [], {RELEASED_ORDER: answer(NONE_NAME, True)})
    assert list(row_groups([similar, scenario, similar])) == ["every test file", "similar_tools", "scenario"]
    assert row_groups([similar, scenario, similar])["similar_tools"] == [similar, similar]
    assert list(row_groups([similar, reliability])) == ["similar_tools", "reliability"]
    assert list(row_groups([similar])) == ["similar_tools"]
    assert list_names([similar, reliability]) == ["5_first", RELEASED_ORDER]
