"""Convert the raw MetaTool files into the common format."""

import json
import re
from pathlib import Path
from typing import Any

from grjev.constants import METATOOL_TEST_FILES, METATOOL_TOOL_LINE, METATOOL_TOOLS_FILE, TOOLS_FILE_NAME
from grjev.examples import Example, Option, write_jsonl

TOOL_LINE = re.compile(METATOOL_TOOL_LINE, re.MULTILINE)


def options_in_prompt(prompt: str, descriptions: dict[str, str]) -> list[Option]:
    """Return the tools listed in a MetaTool prompt, in their listed order, with descriptions from the tool file."""
    listed = TOOL_LINE.findall(prompt)
    if [int(number) for number, _ in listed] != list(range(1, len(listed) + 1)):
        raise ValueError(f"The tool list in this prompt is not numbered from 1: {prompt[:200]!r}")
    return [Option(name=name, description=descriptions[name]) for _, name in listed]


def labels_of(test_file: str, row: dict[str, Any]) -> list[str]:
    """Return the correct answers of one raw row, which are stored differently in each test file."""
    if test_file == "tool_awareness":
        return [{"positive": "yes", "negative": "no"}[row["label"]]]
    if test_file == "reliability":
        return []
    if test_file == "multi_tool":
        return list(row["tool"])
    return [row["tool"]]


def examples_of(test_file: str, rows: list[dict[str, Any]], descriptions: dict[str, str]) -> list[Example]:
    """Convert the rows of one raw test file."""
    return [
        Example(
            id=f"metatool/{test_file}/{index}",
            query=row["query"],
            options=options_in_prompt(row.get("action_prompt", ""), descriptions),
            labels=labels_of(test_file, row),
            raw=row,
        )
        for index, row in enumerate(rows)
    ]


def process_metatool(raw_dir: Path, processed_dir: Path) -> dict[str, int]:
    """Write every MetaTool test file and the tool list in the common format. Return the number of rows written."""
    descriptions = json.loads((raw_dir / METATOOL_TOOLS_FILE).read_text())
    write_jsonl(processed_dir / TOOLS_FILE_NAME, [Option(name=n, description=d) for n, d in descriptions.items()])
    written = {TOOLS_FILE_NAME: len(descriptions)}
    for test_file, raw_path in METATOOL_TEST_FILES.items():
        examples = examples_of(test_file, json.loads((raw_dir / raw_path).read_text()), descriptions)
        write_jsonl(processed_dir / f"{test_file}.jsonl", examples)
        written[f"{test_file}.jsonl"] = len(examples)
    return written
