"""Convert the HotpotQA validation questions of the distractor setting into the common format."""

from pathlib import Path
from typing import Any

# pyarrow ships no type information.
import pyarrow.parquet  # type: ignore[import-untyped]

from grjev.constants import (
    HOTPOTQA_PASSAGES,
    HOTPOTQA_RAW_FILE,
    HOTPOTQA_TEN_FILE,
    HOTPOTQA_TEST_FILE,
    TOOLS_FILE_NAME,
)
from grjev.examples import Example, Option, distinct_options, write_jsonl


def examples_of(rows: list[dict[str, Any]]) -> list[Example]:
    """Convert the raw rows. A question is the query, its passages are the options, and a label is a passage title.

    A passage is named by its title, and its description is its sentences joined. The labels are the titles of the
    passages that hold a supporting fact, in the order of the passages.
    """
    examples = []
    for row in rows:
        context, supporting = row["context"], set(row["supporting_facts"]["title"])
        passages = zip(context["title"], context["sentences"], strict=True)
        examples.append(
            Example(
                id=f"hotpotqa/{HOTPOTQA_TEST_FILE}/{row['id']}",
                query=row["question"],
                options=[Option(name=title, description="".join(sentences).strip()) for title, sentences in passages],
                labels=[title for title in context["title"] if title in supporting],
                raw=row,
            )
        )
    return examples


def process_hotpotqa(raw_dir: Path, processed_dir: Path) -> dict[str, int]:
    """Write every question, the questions with 10 passages and their distinct passages. Return the rows written."""
    examples = examples_of(pyarrow.parquet.read_table(raw_dir / HOTPOTQA_RAW_FILE).to_pylist())
    ten = [example for example in examples if len(example.options) == HOTPOTQA_PASSAGES]
    passages = distinct_options(ten)
    write_jsonl(processed_dir / f"{HOTPOTQA_TEST_FILE}.jsonl", examples)
    write_jsonl(processed_dir / f"{HOTPOTQA_TEN_FILE}.jsonl", ten)
    write_jsonl(processed_dir / TOOLS_FILE_NAME, passages)
    return {
        f"{HOTPOTQA_TEST_FILE}.jsonl": len(examples),
        f"{HOTPOTQA_TEN_FILE}.jsonl": len(ten),
        TOOLS_FILE_NAME: len(passages),
    }
