"""Convert the BFCL test files into the common format."""

import json
from pathlib import Path
from typing import Any

from grjev.constants import (
    BFCL_ANSWER_DIR,
    BFCL_ANY_CALL_FILES,
    BFCL_CLASS_DOCS,
    BFCL_FILE_PREFIX,
    BFCL_FUNC_DOC_DIR,
    BFCL_MEMORY_DOCS,
    BFCL_MEMORY_FILE,
    BFCL_MULTI_TURN_FILES,
    BFCL_NO_CALL_FILES,
    BFCL_SINGLE_TURN_FILES,
    BFCL_TEST_FILES,
    TOOLS_FILE_NAME,
)
from grjev.examples import Example, Option, distinct_options, write_jsonl

type Row = dict[str, Any]


def read_rows(path: Path) -> list[Row]:
    """Read a BFCL file, which has one JSON object per line."""
    return [json.loads(line) for line in path.read_text().split("\n") if line]


def read_answers(test_file: str, raw_dir: Path, rows: list[Row]) -> list[Row]:
    """Return the ground-truth row of each test row. A file without a ground-truth file gives empty rows."""
    if test_file in BFCL_NO_CALL_FILES + BFCL_ANY_CALL_FILES:
        return [{} for _ in rows]
    answers = read_rows(raw_dir / BFCL_ANSWER_DIR / f"{BFCL_FILE_PREFIX}{test_file}.json")
    if [answer["id"] for answer in answers] != [row["id"] for row in rows]:
        raise ValueError(f"The ground truth of {test_file} does not have the ids of the test file in the same order")
    return answers


def read_function_docs(raw_dir: Path) -> dict[str, list[Row]]:
    """Return the function definitions of every file that an API class or a memory backend points to."""
    files = {*BFCL_CLASS_DOCS.values(), *BFCL_MEMORY_DOCS.values()}
    return {name: read_rows(raw_dir / BFCL_FUNC_DOC_DIR / name) for name in files}


def options_of(functions: list[Row]) -> list[Option]:
    """Return the name and description of each function definition."""
    return [Option(name=function["name"], description=function["description"]) for function in functions]


def query_of(messages: list[Row]) -> str:
    """Return the last message of a turn, which is the user's query. A turn that only adds functions has no message."""
    return messages[-1]["content"] if messages else ""


def called_functions(ground_truth: list[Row]) -> list[str]:
    """Return the names of the functions a single-turn ground truth calls, each once, in the order of first call."""
    return list(dict.fromkeys(name for call in ground_truth for name in call))


def single_turn_example(test_file: str, row: Row, answer: Row) -> Example:
    """Convert a single-turn row and its ground-truth row. Messages before the query stay in `raw`.

    The labels are the called functions. A file whose correct output has no call has none, and a file that accepts
    any call has no stored label.
    """
    labels = None if test_file in BFCL_ANY_CALL_FILES else called_functions(answer.get("ground_truth", []))
    return Example(
        id=f"bfcl/{row['id']}",
        query=query_of(row["question"][0]),
        options=options_of(row["function"]),
        labels=labels,
        raw=row | answer,
    )


def turn_examples(row: Row, answer: Row, docs: dict[str, list[Row]]) -> list[Example]:
    """Convert a multi-turn row into one example per turn.

    The options are the functions of the row's API classes without its excluded functions. A function listed in
    `missed_function` is withheld until the turn it is listed under. The labels are the functions that the ground
    truth of the turn calls.
    """
    excluded = row.get("excluded_function", [])
    defined = [function for name in row["involved_classes"] for function in docs[BFCL_CLASS_DOCS[name]]]
    functions = [function for function in defined if function["name"] not in excluded]
    added = row.get("missed_function", {})
    examples = []
    for turn, (messages, calls) in enumerate(zip(row["question"], answer["ground_truth"], strict=True)):
        withheld = {name for added_at, names in added.items() if int(added_at) > turn for name in names}
        examples.append(
            Example(
                id=f"bfcl/{row['id']}/turn_{turn}",
                query=query_of(messages),
                options=options_of([function for function in functions if function["name"] not in withheld]),
                labels=list(dict.fromkeys(call.split("(", 1)[0] for call in calls)),
                raw=row | answer,
            )
        )
    return examples


def agentic_examples(test_file: str, row: Row, answer: Row, docs: dict[str, list[Row]]) -> list[Example]:
    """Convert a web search or memory row. Its answer is text, so no function is a label.

    A web search row has the functions of its API class. A memory row gives one example per memory backend, with the
    functions of that backend.
    """
    if test_file == BFCL_MEMORY_FILE:
        lists = {f"/{backend}": docs[file] for backend, file in BFCL_MEMORY_DOCS.items()}
    else:
        lists = {"": [function for name in row["involved_classes"] for function in docs[BFCL_CLASS_DOCS[name]]]}
    return [
        Example(
            id=f"bfcl/{row['id']}{suffix}",
            query=query_of(row["question"][0]),
            options=options_of(functions),
            labels=None,
            raw=row | answer,
        )
        for suffix, functions in lists.items()
    ]


def examples_of(test_file: str, raw_dir: Path) -> list[Example]:
    """Convert one test file with its ground truth."""
    rows = read_rows(raw_dir / f"{BFCL_FILE_PREFIX}{test_file}.json")
    pairs = list(zip(rows, read_answers(test_file, raw_dir, rows), strict=True))
    if test_file in BFCL_SINGLE_TURN_FILES:
        return [single_turn_example(test_file, row, answer) for row, answer in pairs]
    docs = read_function_docs(raw_dir)
    if test_file in BFCL_MULTI_TURN_FILES:
        return [example for row, answer in pairs for example in turn_examples(row, answer, docs)]
    return [example for row, answer in pairs for example in agentic_examples(test_file, row, answer, docs)]


def process_bfcl(raw_dir: Path, processed_dir: Path) -> dict[str, int]:
    """Write every test file and the list of all functions in the common format. Return the number of rows written."""
    by_file = {test_file: examples_of(test_file, raw_dir) for test_file in BFCL_TEST_FILES}
    for test_file, examples in by_file.items():
        write_jsonl(processed_dir / f"{test_file}.jsonl", examples)
    functions = distinct_options(example for examples in by_file.values() for example in examples)
    write_jsonl(processed_dir / TOOLS_FILE_NAME, functions)
    written = {f"{test_file}.jsonl": len(examples) for test_file, examples in by_file.items()}
    return written | {TOOLS_FILE_NAME: len(functions)}
