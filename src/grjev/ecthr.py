"""Convert the test cases of ECtHR Task A of LexGLUE into the common format."""

from pathlib import Path
from typing import Any

# pyarrow ships no type information.
import pyarrow.parquet  # type: ignore[import-untyped]

from grjev.constants import ECTHR_ARTICLES, ECTHR_RAW_FILE, ECTHR_TEST_FILE, TOOLS_FILE_NAME
from grjev.examples import Example, Option, write_jsonl

ARTICLES = [Option(name=name, description=title) for name, title in ECTHR_ARTICLES]


def examples_of(rows: list[dict[str, Any]]) -> list[Example]:
    """Convert the raw rows. The facts of a case are the query, and the 10 articles are the options of every case.

    The paragraphs of the facts are joined with a line feed. The labels are the articles that the Court found
    violated, and they are empty when it found no violation of the 10 articles.
    """
    return [
        Example(
            id=f"ecthr/{ECTHR_TEST_FILE}/{number}",
            query="\n".join(row["text"]),
            options=ARTICLES,
            labels=[ARTICLES[label].name for label in sorted(row["labels"])],
            raw=row,
        )
        for number, row in enumerate(rows)
    ]


def process_ecthr(raw_dir: Path, processed_dir: Path) -> dict[str, int]:
    """Write the test cases and the 10 articles. Return the number of rows written."""
    examples = examples_of(pyarrow.parquet.read_table(raw_dir / ECTHR_RAW_FILE).to_pylist())
    write_jsonl(processed_dir / f"{ECTHR_TEST_FILE}.jsonl", examples)
    write_jsonl(processed_dir / TOOLS_FILE_NAME, ARTICLES)
    return {f"{ECTHR_TEST_FILE}.jsonl": len(examples), TOOLS_FILE_NAME: len(ARTICLES)}
