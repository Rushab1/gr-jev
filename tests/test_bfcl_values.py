"""Tests for grjev.bfcl_values."""

import pytest

from grjev.bfcl_values import descriptions_in, example_sources, number_in_text, value_in_text, value_source, value_stats
from grjev.constants import BFCL_SINGLE_TURN_FILES
from grjev.examples import Example, Option

QUERY = "Find the area of a triangle with a base of 1,000 units and a height of 5.5 units in New York."
NUMBERS = [(1000, True), (100, False), (5.5, True), (5, False), (5.0, False), (7, False)]


@pytest.mark.parametrize(("number", "found"), NUMBERS)
def test_a_number_matches_in_digits_and_not_inside_a_longer_number(number: float, found: bool) -> None:
    assert number_in_text(QUERY, number) is found


def test_a_whole_number_given_as_a_float_matches_its_digits() -> None:
    assert number_in_text("a base of 10 units", 10.0)


def test_text_matches_in_any_case_and_a_list_needs_every_element() -> None:
    assert value_in_text(QUERY, "new york") and not value_in_text(QUERY, "New York, NY")
    assert value_in_text(QUERY, [1000, "units"]) and not value_in_text(QUERY, [1000, "metres"])
    assert not value_in_text(QUERY, "") and not value_in_text(QUERY, []) and not value_in_text(QUERY, True)


def test_a_nested_parameter_needs_every_key_in_the_text_or_left_out() -> None:
    assert value_in_text(QUERY, {"base": [1000], "unit": ["", "metres"]})
    assert not value_in_text(QUERY, {"base": [1000], "unit": ["metres"]})


def test_descriptions_of_nested_parameters_are_found() -> None:
    schema = {"description": "The place.", "properties": {"city": {"description": "Such as Paris, France."}}}
    assert descriptions_in(schema) == ["The place.", "Such as Paris, France."]


def test_the_sources_are_tried_in_order() -> None:
    city = {"type": "string", "description": "City and state, e.g. New York, NY."}
    assert value_source(QUERY, ["units", ""], {"type": "string"}, "") == "query"
    assert value_source(QUERY, [True], {"type": "boolean"}, "") == "boolean"
    assert value_source(QUERY, ["true"], {"type": "Boolean"}, "") == "boolean"
    assert value_source(QUERY, ["metric"], {"type": "string", "enum": ["metric", "imperial"]}, "") == "schema"
    assert value_source(QUERY, ["", "New York, NY"], city, "") == "left_out"
    assert value_source(QUERY, ["New York, NY"], city, "") == "description"
    assert value_source(QUERY, ["metric"], {"type": "string"}, "Returns the area in metric units.") == "description"
    assert value_source(QUERY, [1], {"type": "integer", "default": 1}, "") == "description"
    assert value_source(QUERY, [1], {"type": "integer", "default": True}, "") == "other"
    assert value_source(QUERY, ["New York, NY"], {"type": "string"}, "") == "other"
    assert value_source(QUERY, [], {"type": "array"}, "") == "other"


def single_turn(query: str, ground_truth: list[dict[str, dict[str, list[object]]]]) -> Example:
    properties = {"base": {"type": "integer"}, "city": {"type": "string"}, "exact": {"type": "boolean"}}
    function = {"name": "area", "description": "", "parameters": {"type": "dict", "properties": properties}}
    raw = {"id": "simple_python_0", "question": [[]], "function": [function], "ground_truth": ground_truth}
    option = Option(name="area", description="")
    return Example(id="bfcl/simple_python_0", query=query, options=[option], labels=["area"], raw=raw)


def test_an_example_is_selectable_when_no_value_has_to_be_rewritten() -> None:
    selectable = single_turn(QUERY, [{"area": {"base": [1000], "exact": [True]}}])
    rewritten = single_turn(QUERY, [{"area": {"base": [1000]}}, {"area": {"city": ["New York, NY"]}}])
    assert example_sources(selectable) == ["query", "boolean"]
    assert example_sources(rewritten) == ["query", "other"]
    dataset: dict[str, list[Example]] = {name: [] for name in BFCL_SINGLE_TURN_FILES}
    dataset["simple_python"] = [selectable, rewritten]
    stats = value_stats(dataset)
    assert stats["files"]["simple_python"] == {
        "examples": 2,
        "selectable": 1,
        "values": {"query": 2, "boolean": 1, "schema": 0, "left_out": 0, "description": 0, "other": 1},
    }
    assert "irrelevance" not in stats["files"] and "live_relevance" not in stats["files"]
