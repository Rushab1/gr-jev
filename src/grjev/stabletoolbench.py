"""Convert the StableToolBench test files into the common format."""

import json
from pathlib import Path
from typing import Any

from grjev.constants import STABLETOOLBENCH_TEST_FILES, TOOLS_FILE_NAME
from grjev.examples import Example, Option, distinct_options, write_jsonl


def option_of(api: dict[str, Any]) -> Option:
    """Return one API of a raw list. Its name joins the category, tool and API names, which identify it in all files."""
    name = f"{api['category_name']} / {api['tool_name']} / {api['api_name']}"
    return Option(name=name, description=api["api_description"])


def labels_of(row: dict[str, Any]) -> list[str]:
    """Return the names of the row's relevant APIs, each once. The raw row gives each as a tool name and an API name."""
    names = {(api["tool_name"], api["api_name"]): option_of(api).name for api in row["api_list"]}
    return list(dict.fromkeys(names[tool, api] for tool, api in row["relevant APIs"]))


def examples_of(test_file: str, rows: list[dict[str, Any]]) -> list[Example]:
    """Convert the rows of one raw test file."""
    return [
        Example(
            id=f"stabletoolbench/{test_file}/{row['query_id']}",
            query=row["query"],
            options=[option_of(api) for api in row["api_list"]],
            labels=labels_of(row),
            raw=row,
        )
        for row in rows
    ]


def process_stabletoolbench(raw_dir: Path, processed_dir: Path) -> dict[str, int]:
    """Write every test file and the list of all APIs in the common format. Return the number of rows written."""
    by_file = {
        test_file: examples_of(test_file, json.loads((raw_dir / f"{test_file}.json").read_text()))
        for test_file in STABLETOOLBENCH_TEST_FILES
    }
    for test_file, examples in by_file.items():
        write_jsonl(processed_dir / f"{test_file}.jsonl", examples)
    apis = distinct_options(example for examples in by_file.values() for example in examples)
    write_jsonl(processed_dir / TOOLS_FILE_NAME, apis)
    return {f"{test_file}.jsonl": len(examples) for test_file, examples in by_file.items()} | {
        TOOLS_FILE_NAME: len(apis)
    }
