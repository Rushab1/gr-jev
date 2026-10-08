"""Tests for grjev.mmlu. The last two convert the downloaded file and are skipped without it."""

from pathlib import Path
from typing import Any

import pyarrow.parquet  # type: ignore[import-untyped]
import pytest

from grjev.constants import MMLU_RAW_DIR, MMLU_RAW_FILE, MMLU_STANDALONE_FILE, MMLU_TEST_FILE, MMLU_TEST_FILES
from grjev.examples import Example, Option, read_dataset, read_jsonl, write_jsonl
from grjev.mmlu import examples_of, process_mmlu, standalone

ROW = {"question": "What is 2 + 2?", "subject": "elementary_mathematics", "choices": ["3", "4", "5", "6"], "answer": 1}


def test_a_question_is_the_query_and_its_choices_are_options_without_a_description() -> None:
    [example] = examples_of([ROW])
    assert (example.id, example.query, example.raw) == ("mmlu/test/0", "What is 2 + 2?", ROW)
    assert example.options == [Option(name=choice, description="") for choice in ("3", "4", "5", "6")]
    assert example.labels == ["4"]
    assert [item.id for item in examples_of([ROW, ROW])] == ["mmlu/test/0", "mmlu/test/1"]


@pytest.mark.parametrize(
    "choices",
    [
        ["3", "4", "4", "6"],
        ["3", "4", "5", "None of the above"],
        ["3", "4", "all of the above.", "6"],
        ["3", "4", "Both A and B", "6"],
        ["I only", "II only", "5", "6"],
        ["3", "4", "5", "Neither of these"],
    ],
)
def test_a_question_is_not_standalone_when_a_choice_repeats_or_refers_to_another(choices: list[str]) -> None:
    assert standalone(examples_of([ROW])[0])
    assert not standalone(examples_of([ROW | {"choices": choices}])[0])


def test_a_question_with_a_line_separator_in_its_text_is_read_back_as_one_row(tmp_path: Path) -> None:
    separators = "first\u2028second\u0085third\x0cfourth\rfifth\nsixth"
    examples = examples_of([ROW | {"question": separators}, ROW])
    write_jsonl(tmp_path / "test.jsonl", examples)
    assert read_jsonl(tmp_path / "test.jsonl", Example) == examples


@pytest.fixture(scope="module")
def raw_rows() -> list[dict[str, Any]]:
    """The rows of the downloaded test file."""
    if not (MMLU_RAW_DIR / MMLU_RAW_FILE).exists():
        pytest.skip("MMLU is not downloaded")
    rows: list[dict[str, Any]] = pyarrow.parquet.read_table(MMLU_RAW_DIR / MMLU_RAW_FILE).to_pylist()
    return rows


@pytest.fixture(scope="module")
def processed(
    raw_rows: list[dict[str, Any]], tmp_path_factory: pytest.TempPathFactory
) -> tuple[dict[str, list[Example]], list[Option]]:
    """The examples and the list of choices read back from disk after running the converter on the downloaded file."""
    processed_dir: Path = tmp_path_factory.mktemp("mmlu")
    process_mmlu(MMLU_RAW_DIR, processed_dir)
    return read_dataset(processed_dir, MMLU_TEST_FILES)


def test_every_raw_row_survives_unchanged_with_every_character(
    raw_rows: list[dict[str, Any]], processed: tuple[dict[str, list[Example]], list[Option]]
) -> None:
    examples = processed[0][MMLU_TEST_FILE]
    assert [example.raw for example in examples] == raw_rows and len(raw_rows) == 14_042
    assert len({row["subject"] for row in raw_rows}) == 57
    for example, row in zip(examples, raw_rows, strict=True):
        assert example.query == row["question"] and [option.name for option in example.options] == row["choices"]
        assert example.labels == [row["choices"][row["answer"]]]


def test_the_standalone_file_holds_the_13096_questions_whose_choices_can_be_moved(
    processed: tuple[dict[str, list[Example]], list[Option]],
) -> None:
    every, kept = processed[0][MMLU_TEST_FILE], processed[0][MMLU_STANDALONE_FILE]
    assert len(kept) == 13_096 and kept == [example for example in every if standalone(example)]
    assert all(len({option.name for option in example.options}) == 4 for example in kept)
    choices = {option.name for example in kept for option in example.options}
    assert {option.name for option in processed[1]} == choices and len(processed[1]) == len(choices)
