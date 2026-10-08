"""Convert the MMLU test questions into the common format."""

import re
from pathlib import Path
from typing import Any

# pyarrow ships no type information.
import pyarrow.parquet  # type: ignore[import-untyped]

from grjev.constants import (
    MMLU_RAW_FILE,
    MMLU_REFERRING_CHOICE,
    MMLU_STANDALONE_FILE,
    MMLU_TEST_FILE,
    TOOLS_FILE_NAME,
)
from grjev.examples import Example, Option, distinct_options, write_jsonl


def examples_of(rows: list[dict[str, Any]]) -> list[Example]:
    """Convert the raw rows. A question is the query, its choices are the options, and the id holds the row number."""
    return [
        Example(
            id=f"mmlu/{MMLU_TEST_FILE}/{number}",
            query=row["question"],
            options=[Option(name=choice, description="") for choice in row["choices"]],
            labels=[row["choices"][row["answer"]]],
            raw=row,
        )
        for number, row in enumerate(rows)
    ]


def standalone(example: Example) -> bool:
    """Say whether the choices of a question all differ and none refers to another choice."""
    choices = [option.name for option in example.options]
    refers = any(re.search(MMLU_REFERRING_CHOICE, choice, re.IGNORECASE) for choice in choices)
    return len(set(choices)) == len(choices) and not refers


def process_mmlu(raw_dir: Path, processed_dir: Path) -> dict[str, int]:
    """Write every question, the standalone questions and their distinct choices. Return the number of rows written."""
    examples = examples_of(pyarrow.parquet.read_table(raw_dir / MMLU_RAW_FILE).to_pylist())
    kept = [example for example in examples if standalone(example)]
    choices = distinct_options(kept)
    write_jsonl(processed_dir / f"{MMLU_TEST_FILE}.jsonl", examples)
    write_jsonl(processed_dir / f"{MMLU_STANDALONE_FILE}.jsonl", kept)
    write_jsonl(processed_dir / TOOLS_FILE_NAME, choices)
    return {
        f"{MMLU_TEST_FILE}.jsonl": len(examples),
        f"{MMLU_STANDALONE_FILE}.jsonl": len(kept),
        TOOLS_FILE_NAME: len(choices),
    }
