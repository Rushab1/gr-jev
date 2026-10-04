"""Tests for grjev.metatool. The last four run the converter on the downloaded files and are skipped without them."""

import ast
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from grjev.constants import METATOOL_RAW_DIR, METATOOL_TEST_FILES, METATOOL_TOOLS_FILE
from grjev.examples import Example, read_dataset
from grjev.metatool import labels_of, options_in_prompt, process_metatool

DESCRIPTIONS = {"maps": "Find places.", "mail": "Send email."}
PROMPT = """Choose a tool.
1. tool name: mail, tool description: ['Send email.']
2. tool name: maps, tool description: Find places.

[Examples Start]
query: "Where is Paris?" tool: maps
"""


def test_options_keep_the_order_of_the_prompt_and_take_descriptions_from_the_tool_file() -> None:
    options = options_in_prompt(PROMPT, DESCRIPTIONS)
    assert [(option.name, option.description) for option in options] == [
        ("mail", "Send email."),
        ("maps", "Find places."),
    ]


def test_a_tool_missing_from_the_tool_file_or_a_broken_numbering_is_an_error() -> None:
    with pytest.raises(KeyError):
        options_in_prompt(PROMPT, {"maps": "Find places."})
    with pytest.raises(ValueError, match="not numbered from 1"):
        options_in_prompt(PROMPT.replace("1. tool name", "3. tool name"), DESCRIPTIONS)


def test_labels_follow_the_rule_of_each_test_file() -> None:
    assert labels_of("similar_tools", {"tool": "maps"}) == ["maps"]
    assert labels_of("reliability", {"tool": "maps"}) == []
    assert labels_of("multi_tool", {"tool": ["maps", "mail"]}) == ["maps", "mail"]
    assert labels_of("tool_awareness", {"label": "negative"}) == ["no"]


@pytest.fixture(scope="module")
def raw_rows() -> dict[str, list[dict[str, Any]]]:
    """The rows of each downloaded MetaTool test file, by test file name."""
    if not (METATOOL_RAW_DIR / METATOOL_TOOLS_FILE).exists():
        pytest.skip("MetaTool is not downloaded")
    return {name: json.loads((METATOOL_RAW_DIR / path).read_text()) for name, path in METATOOL_TEST_FILES.items()}


@pytest.fixture(scope="module")
def processed(
    raw_rows: dict[str, list[dict[str, Any]]], tmp_path_factory: pytest.TempPathFactory
) -> dict[str, list[Example]]:
    """The examples read back from disk after running the converter on the downloaded files."""
    processed_dir: Path = tmp_path_factory.mktemp("metatool")
    process_metatool(METATOOL_RAW_DIR, processed_dir)
    return read_dataset(processed_dir, METATOOL_TEST_FILES)[0]


def characters(rows: list[dict[str, Any]]) -> Counter[str]:
    """Count every character of every key and value in the rows."""
    return Counter(json.dumps(rows, ensure_ascii=False, sort_keys=True))


def test_every_raw_row_survives_unchanged(
    raw_rows: dict[str, list[dict[str, Any]]], processed: dict[str, list[Example]]
) -> None:
    for name, rows in raw_rows.items():
        assert [example.raw for example in processed[name]] == rows


def test_character_counts_match_the_raw_files(
    raw_rows: dict[str, list[dict[str, Any]]], processed: dict[str, list[Example]]
) -> None:
    for name, rows in raw_rows.items():
        kept = characters([example.raw for example in processed[name]])
        assert kept == characters(rows)
        assert kept.total() == len(json.dumps(rows, ensure_ascii=False, sort_keys=True))


def test_options_are_the_tool_list_of_the_raw_prompt(processed: dict[str, list[Example]]) -> None:
    for examples in processed.values():
        for example in examples:
            prompt = example.raw.get("action_prompt", "")
            assert prompt.count(". tool name: ") == len(example.options)
            for position, option in enumerate(example.options, 1):
                line_start = f"\n{position}. tool name: {option.name}, tool description: "
                shown = prompt.split(line_start, 1)[1].split("\n", 1)[0]
                assert option.description == (ast.literal_eval(shown)[0] if shown.startswith("[") else shown)


def test_labels_match_the_raw_answers(processed: dict[str, list[Example]]) -> None:
    for name, examples in processed.items():
        for example in examples:
            names = [option.name for option in example.options]
            if name == "tool_awareness":
                assert example.labels == [{"positive": "yes", "negative": "no"}[example.raw["label"]]]
            elif name == "reliability":
                assert example.labels == [] and example.raw["tool"] not in names
            else:
                answers = example.raw["tool"] if name == "multi_tool" else [example.raw["tool"]]
                assert example.labels == answers and set(answers) <= set(names)
            assert example.query == example.raw["query"]
