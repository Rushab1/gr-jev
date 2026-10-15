"""The common format of a processed dataset: one example per row, with the same fields for every dataset."""

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, TypeAdapter

from grjev.constants import TOOLS_FILE_NAME


class Option(BaseModel):
    """One tool or function that a model can select."""

    name: str
    description: str


class Example(BaseModel):
    """One query with its options in the order of the raw file.

    `labels` holds the names of the correct options. It is empty when no option is correct, and holds "yes" or "no"
    for an example that has no options. It is None when the answer is not a choice among the options.

    `raw` is the row of the raw file, unchanged, so no raw data is lost. When the raw data keeps an example's answer
    in a second file, `raw` holds both rows merged. When one raw row gives several examples, each holds the whole row.
    """

    id: str
    query: str
    options: list[Option]
    labels: list[str] | None
    raw: dict[str, Any]


def write_jsonl(path: Path, rows: Iterable[BaseModel]) -> None:
    """Write one JSON object per line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(row.model_dump_json() + "\n" for row in rows))


def distinct_options(examples: Iterable[Example]) -> list[Option]:
    """Return every different option of the examples, in the order of first appearance."""
    seen = {(option.name, option.description): option for example in examples for option in example.options}
    return list(seen.values())


def read_jsonl[T: BaseModel](path: Path, model: type[T]) -> list[T]:
    """Read a file written by write_jsonl."""
    # A row ends at a line feed only. str.splitlines would also cut a row at a line separator inside its text.
    return [model.model_validate_json(line) for line in path.read_text().split("\n") if line]


def read_dataset(processed_dir: Path, test_files: Iterable[str]) -> tuple[dict[str, list[Example]], list[Option]]:
    """Return the examples of each named test file of a processed dataset, and its tool list."""
    examples = {name: read_jsonl(processed_dir / f"{name}.jsonl", Example) for name in test_files}
    return examples, read_jsonl(processed_dir / TOOLS_FILE_NAME, Option)


def read_rewordings(path: Path) -> dict[str, list[Option]]:
    """Return the rewordings of each tool in a rewordings file, by the name of the tool."""
    return TypeAdapter(dict[str, list[Option]]).validate_json(path.read_bytes())
