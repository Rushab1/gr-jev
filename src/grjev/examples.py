"""The common format of a processed dataset: one example per row, with the same fields for every dataset."""

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from grjev.constants import TOOLS_FILE_NAME


class Option(BaseModel):
    """One tool or function that a model can select."""

    name: str
    description: str


class Example(BaseModel):
    """One query with its options in the order of the raw file.

    `labels` holds the names of the correct options. It is empty when no option is correct, and holds "yes" or "no"
    for an example that has no options. `raw` is the row of the raw file, unchanged, so no raw data is lost.
    """

    id: str
    query: str
    options: list[Option]
    labels: list[str]
    raw: dict[str, Any]


def write_jsonl(path: Path, rows: Iterable[BaseModel]) -> None:
    """Write one JSON object per line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(row.model_dump_json() + "\n" for row in rows))


def read_jsonl[T: BaseModel](path: Path, model: type[T]) -> list[T]:
    """Read a file written by write_jsonl."""
    return [model.model_validate_json(line) for line in path.read_text().splitlines()]


def read_dataset(processed_dir: Path, test_files: Iterable[str]) -> tuple[dict[str, list[Example]], list[Option]]:
    """Return the examples of each named test file of a processed dataset, and its tool list."""
    examples = {name: read_jsonl(processed_dir / f"{name}.jsonl", Example) for name in test_files}
    return examples, read_jsonl(processed_dir / TOOLS_FILE_NAME, Option)
