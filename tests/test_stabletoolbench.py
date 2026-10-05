"""Tests for grjev.stabletoolbench. The last three convert the downloaded files and are skipped without them."""

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from grjev.constants import STABLETOOLBENCH_RAW_DIR, STABLETOOLBENCH_TEST_FILES
from grjev.examples import Example, Option, read_dataset
from grjev.stabletoolbench import examples_of, process_stabletoolbench


def api(category: str, tool: str, name: str, description: str = "") -> dict[str, Any]:
    return {"category_name": category, "tool_name": tool, "api_name": name, "api_description": description}


ROW = {
    "api_list": [api("Finance", "Converter", "Convert", "Convert currencies."), api("Finance", "Converter", "List")],
    "query": "Convert 5 euros to dollars.",
    "relevant APIs": [["Converter", "Convert"], ["Converter", "Convert"]],
    "query_id": 7,
}


def test_an_api_is_named_by_category_tool_and_api_and_keeps_the_order_of_the_list() -> None:
    [example] = examples_of("G1_tool", [ROW])
    assert example.id == "stabletoolbench/G1_tool/7"
    assert example.options == [
        Option(name="Finance / Converter / Convert", description="Convert currencies."),
        Option(name="Finance / Converter / List", description=""),
    ]
    assert (example.query, example.raw) == ("Convert 5 euros to dollars.", ROW)


def test_a_relevant_api_named_twice_is_one_label() -> None:
    assert examples_of("G1_tool", [ROW])[0].labels == ["Finance / Converter / Convert"]


def test_a_relevant_api_that_is_not_in_the_list_is_an_error() -> None:
    with pytest.raises(KeyError):
        examples_of("G1_tool", [ROW | {"relevant APIs": [["Converter", "Delete"]]}])


@pytest.fixture(scope="module")
def raw_rows() -> dict[str, list[dict[str, Any]]]:
    """The rows of each downloaded test file, by test file name."""
    if not (STABLETOOLBENCH_RAW_DIR / f"{STABLETOOLBENCH_TEST_FILES[0]}.json").exists():
        pytest.skip("StableToolBench is not downloaded")
    return {
        name: json.loads((STABLETOOLBENCH_RAW_DIR / f"{name}.json").read_text()) for name in STABLETOOLBENCH_TEST_FILES
    }


@pytest.fixture(scope="module")
def processed(
    raw_rows: dict[str, list[dict[str, Any]]], tmp_path_factory: pytest.TempPathFactory
) -> tuple[dict[str, list[Example]], list[Option]]:
    """The examples and the API list read back from disk after running the converter on the downloaded files."""
    processed_dir: Path = tmp_path_factory.mktemp("stabletoolbench")
    process_stabletoolbench(STABLETOOLBENCH_RAW_DIR, processed_dir)
    return read_dataset(processed_dir, STABLETOOLBENCH_TEST_FILES)


def test_every_raw_row_survives_unchanged_with_every_character(
    raw_rows: dict[str, list[dict[str, Any]]], processed: tuple[dict[str, list[Example]], list[Option]]
) -> None:
    for name, rows in raw_rows.items():
        kept = [example.raw for example in processed[0][name]]
        assert kept == rows
        assert Counter(json.dumps(kept, ensure_ascii=False, sort_keys=True)) == Counter(
            json.dumps(rows, ensure_ascii=False, sort_keys=True)
        )


def test_options_and_labels_match_the_raw_rows(processed: tuple[dict[str, list[Example]], list[Option]]) -> None:
    for examples in processed[0].values():
        for example in examples:
            apis = example.raw["api_list"]
            assert example.labels is not None
            names = [option.name for option in example.options]
            assert names == [" / ".join([api["category_name"], api["tool_name"], api["api_name"]]) for api in apis]
            assert [option.description for option in example.options] == [api["api_description"] for api in apis]
            assert len(set(names)) == len(names) and len(set(example.labels)) == len(example.labels)
            correct = {
                (api["tool_name"], api["api_name"])
                for api, name in zip(apis, names, strict=True)
                if name in example.labels
            }
            assert correct == {(tool, name) for tool, name in example.raw["relevant APIs"]}
            assert example.query == example.raw["query"]


def test_the_api_list_holds_every_api_once(processed: tuple[dict[str, list[Example]], list[Option]]) -> None:
    examples, apis = processed
    names = [api.name for api in apis]
    assert len(set(names)) == len(names)
    assert set(names) == {option.name for rows in examples.values() for example in rows for option in example.options}
