"""Tests for grjev.stats."""

import pytest

from grjev.constants import EXTREMES_SHOWN
from grjev.examples import Example, Option
from grjev.stats import (
    best_position,
    chance_accuracy,
    content_words,
    correct_option_names,
    dataset_stats,
    input_words,
    integer_bins,
    label_description_words,
    label_positions,
    option_names,
    overlap_accuracy,
    tool_usage,
    words,
)


def example(query: str, options: dict[str, str], labels: list[str]) -> Example:
    listed = [Option(name=name, description=description) for name, description in options.items()]
    return Example(id="test/0", query=query, options=listed, labels=labels, raw={})


def test_words_are_lower_case_and_stop_words_can_be_dropped() -> None:
    assert words("Find the Weather, don't wait!") == ["find", "the", "weather", "don't", "wait"]
    assert content_words("Find the Weather, don't wait!") == ["find", "weather", "wait"]


def test_input_words_and_label_positions() -> None:
    row = example(
        "weather in Paris", {"mail": "send email", "maps": "find places", "forecast": "weather"}, ["forecast"]
    )
    assert input_words(row) == 3 + 3 + 3 + 2
    assert label_positions(row) == [3]
    assert label_description_words([row]) == ([1], [2, 2])


def test_overlap_accuracy_splits_ties_and_skips_examples_without_a_choice() -> None:
    clear = example("weather forecast", {"a": "weather forecast", "b": "send email"}, ["a"])
    tied = example("weather", {"a": "weather today", "b": "weather maps"}, ["b"])
    wrong = example("email", {"a": "weather", "b": "send email"}, ["a"])
    two_correct = example("weather email", {"a": "weather", "b": "email", "c": "weather email maps"}, ["a", "c"])
    no_label = example("email", {"a": "weather", "b": "send email"}, [])
    no_distractor = example("email", {"a": "weather", "b": "send email"}, ["a", "b"])
    assert overlap_accuracy([clear, tied, wrong, two_correct, no_label, no_distractor]) == pytest.approx(
        (1 + 0.5 + 0 + 1) / 4
    )
    assert overlap_accuracy([no_label, no_distractor]) is None


def test_best_position_counts_examples_with_a_choice_and_the_lowest_position_wins_a_tie() -> None:
    first = example("q", {"a": "", "b": "", "c": ""}, ["a"])
    second = example("q", {"a": "", "b": "", "c": ""}, ["b"])
    both = example("q", {"a": "", "b": "", "c": ""}, ["a", "b"])
    no_label = example("q", {"a": "", "b": ""}, [])
    no_distractor = example("q", {"a": ""}, ["a"])
    assert best_position([first, second, both, no_label, no_distractor]) == {"position": 1, "percent": 66.7}
    assert best_position([no_label, no_distractor]) is None
    assert chance_accuracy([first, second, both, no_label, no_distractor]) == pytest.approx((1 / 3 + 1 / 3 + 2 / 3) / 3)
    assert chance_accuracy([no_label, no_distractor]) is None


def test_a_small_range_gets_one_bin_per_value() -> None:
    assert integer_bins([5, 5, 7]) == [
        {"from": 5, "to": 5, "count": 2},
        {"from": 6, "to": 6, "count": 0},
        {"from": 7, "to": 7, "count": 1},
    ]


@pytest.mark.parametrize("values", [list(range(1, 500)), [2, 3, 3, 4, 5, 967], [1] * 50 + [9000]])
def test_bins_cover_every_value_once_and_do_not_overlap(values: list[int]) -> None:
    bins = integer_bins(values)
    assert sum(one["count"] for one in bins) == len(values)
    assert bins[0]["from"] == min(values) and bins[-1]["to"] >= max(values)
    assert all(left["to"] + 1 == right["from"] for left, right in zip(bins, bins[1:], strict=False))


def test_tool_usage_names_the_tools_at_both_ends_and_counts_a_repeated_query_once() -> None:
    tools = [Option(name=name, description="") for name in ("forecast", "mail", "maps")]
    first = example("weather in Paris", {"forecast": "", "mail": ""}, ["forecast"])
    second = example("weather in Paris", {"forecast": "", "maps": ""}, ["forecast"])
    third = example("email Ana", {"forecast": "", "mail": ""}, ["mail"])
    no_list = example("is a tool needed?", {}, ["yes"])
    dataset = {"a": [first, second], "b": [third, no_list], "c": [no_list]}
    listed = tool_usage(dataset, tools, option_names)
    assert (listed["examples"], listed["queries"]) == (3, 2)
    assert listed["highest"][0] == {"name": "forecast", "examples": 3, "queries": 2, "by_file": {"a": 2, "b": 1}}
    assert (listed["lowest"], listed["tools_at_lowest"], listed["lowest_names"]) == (1, 1, ["maps"])
    correct = tool_usage(dataset, tools, correct_option_names)
    assert (correct["examples"], correct["queries"]) == (3, 2)
    assert [(row["name"], row["examples"]) for row in correct["highest"]] == [("forecast", 2), ("mail", 1), ("maps", 0)]


def test_an_example_whose_label_is_not_an_option_counts_for_its_list_only() -> None:
    labelled = example("weather in Paris", {"forecast": "weather", "mail": "send email"}, ["forecast"])
    none_right = example("weather in Paris", {"mail": "send email"}, [])
    text_answer = example("who wrote Hamlet?", {"search": "search the web"}, ["forecast"]).model_copy(
        update={"labels": None}
    )
    yes_no = example("is a tool needed?", {}, ["yes"])
    stats = dataset_stats({"a": [labelled, none_right, text_answer, yes_no]}, [Option(name="search", description="")])
    file = stats["files"]["a"]
    assert (file["with_choice"], file["none_correct"], file["no_label"], file["all_correct"]) == (1, 1, 1, 0)
    assert file["correct_options"]["bins"] == [{"from": 0, "to": 0, "count": 1}, {"from": 1, "to": 1, "count": 1}]
    assert (stats["listed"]["examples"], stats["correct"]["examples"]) == (3, 1)
    assert (file["correct_description_words"], file["other_description_words"]) == (1.0, 2.0)


def test_a_tool_name_with_two_descriptions_is_one_tool() -> None:
    tools = [Option(name="forecast", description="today"), Option(name="forecast", description="this week")]
    row = example("weather in Paris", {"forecast": "today"}, ["forecast"])
    stats = dataset_stats({"a": [row]}, tools)
    assert (stats["tools"], len(stats["listed"]["highest"])) == (1, 1)
    assert sum(one["count"] for one in stats["tool_description_words"]["bins"]) == 2


def test_tools_at_the_lowest_count_are_not_named_when_there_are_many() -> None:
    tools = [Option(name=f"tool{number}", description="") for number in range(EXTREMES_SHOWN + 1)]
    row = example("weather in Paris", {tool.name: "" for tool in tools}, [])
    listed = tool_usage({"a": [row]}, tools, option_names)
    assert (listed["lowest"], listed["tools_at_lowest"], listed["lowest_names"]) == (1, EXTREMES_SHOWN + 1, [])


def test_dataset_stats_describes_each_file_and_each_tool() -> None:
    first = example("weather in Paris", {"forecast": "weather report", "mail": "send email"}, ["forecast"])
    second = example("weather in Paris", {"mail": "send email", "forecast": "weather report"}, ["forecast"])
    stats = dataset_stats({"a": [first], "b": [second]}, [Option(name="forecast", description="weather report")])
    assert stats["files"]["a"]["examples"] == 1
    assert stats["files"]["a"]["options"] == {
        "median": 2,
        "min": 2,
        "max": 2,
        "bins": [{"from": 2, "to": 2, "count": 1}],
    }
    assert stats["files"]["b"]["position"]["bins"] == [{"from": 2, "to": 2, "count": 1}]
    assert (stats["files"]["b"]["all_correct"], stats["files"]["b"]["with_choice"]) == (0, 1)
    assert stats["files"]["b"]["best_position"] == {"position": 2, "percent": 100.0}
    assert (stats["tools"], stats["tool_description_words"]["median"]) == (1, 2)
    assert stats["correct"]["highest"] == [
        {"name": "forecast", "examples": 2, "queries": 1, "by_file": {"a": 1, "b": 1}}
    ]
    assert stats["listed"]["per_tool"]["max"] == 2
