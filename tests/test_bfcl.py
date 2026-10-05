"""Tests for grjev.bfcl. The last six convert the downloaded files and are skipped without them."""

import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

import pytest

from grjev.bfcl import (
    agentic_examples,
    called_functions,
    examples_of,
    process_bfcl,
    read_rows,
    single_turn_example,
    turn_examples,
)
from grjev.constants import (
    BFCL_ANSWER_DIR,
    BFCL_ANY_CALL_FILES,
    BFCL_CLASS_DOCS,
    BFCL_FILE_PREFIX,
    BFCL_MEMORY_DOCS,
    BFCL_MEMORY_FILE,
    BFCL_MULTI_TURN_FILES,
    BFCL_NO_CALL_FILES,
    BFCL_RAW_DIR,
    BFCL_SINGLE_TURN_FILES,
    BFCL_TEST_FILES,
    BFCL_WEB_SEARCH_FILE,
)
from grjev.examples import Example, Option, read_dataset

type Rows = list[dict[str, Any]]
type Processed = tuple[dict[str, list[Example]], list[Option]]


def function(name: str, description: str = "") -> dict[str, Any]:
    return {"name": name, "description": description, "parameters": {"type": "dict", "properties": {}}}


def user(content: str) -> dict[str, str]:
    return {"role": "user", "content": content}


ROW = {
    "id": "multiple_0",
    "question": [[{"role": "system", "content": "Be brief."}, user("Weather in Paris?")]],
    "function": [function("get_weather", "Get the weather."), function("send_email", "Send an email.")],
}
ANSWER = {
    "id": "multiple_0",
    "ground_truth": [{"get_weather": {"city": ["Paris"]}}, {"get_weather": {"city": ["Lyon"]}}],
}
TURNS = {
    "id": "multi_turn_miss_func_0",
    "question": [[user("Add 1 and 2.")], [], [user("Tell Ana.")]],
    "involved_classes": ["MathAPI", "MessageAPI"],
    "excluded_function": ["subtract"],
    "missed_function": {"1": ["add"]},
}
TURNS_ANSWER = {
    "id": "multi_turn_miss_func_0",
    "ground_truth": [[], ["add(a=1,b=2)", "add(a=3,b=4)"], ["send(to='Ana')"]],
}
DOCS = {
    BFCL_CLASS_DOCS["MathAPI"]: [function("add"), function("subtract"), function("logarithm")],
    BFCL_CLASS_DOCS["MessageAPI"]: [function("send")],
    BFCL_CLASS_DOCS["WebSearchAPI"]: [function("search")],
    **{file: [function(f"{backend}_read")] for backend, file in BFCL_MEMORY_DOCS.items()},
}


def write_rows(path: Path, rows: Rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def names(example: Example) -> list[str]:
    return [option.name for option in example.options]


def test_the_query_is_the_last_message_and_raw_holds_the_row_with_its_ground_truth() -> None:
    example = single_turn_example("multiple", ROW, ANSWER)
    assert (example.id, example.query) == ("bfcl/multiple_0", "Weather in Paris?")
    assert example.options == [
        Option(name="get_weather", description="Get the weather."),
        Option(name="send_email", description="Send an email."),
    ]
    assert example.raw == ROW | {"ground_truth": ANSWER["ground_truth"]}


def test_labels_are_the_called_functions_or_empty_without_a_call_or_none_when_any_call_counts() -> None:
    assert single_turn_example("multiple", ROW, ANSWER).labels == ["get_weather"]
    assert called_functions([{"b": {}}, {"a": {}}, {"b": {}}]) == ["b", "a"]
    assert single_turn_example(BFCL_NO_CALL_FILES[0], ROW, {}).labels == []
    assert single_turn_example(BFCL_ANY_CALL_FILES[0], ROW, {}).labels is None


def test_a_ground_truth_file_in_another_order_is_an_error(tmp_path: Path) -> None:
    second = ROW | {"id": "multiple_1"}
    write_rows(tmp_path / f"{BFCL_FILE_PREFIX}multiple.json", [ROW, second])
    write_rows(tmp_path / BFCL_ANSWER_DIR / f"{BFCL_FILE_PREFIX}multiple.json", [ANSWER | {"id": "multiple_1"}, ANSWER])
    with pytest.raises(ValueError, match="same order"):
        examples_of("multiple", tmp_path)


def test_a_multi_turn_row_gives_one_example_per_turn_with_the_functions_available_at_that_turn() -> None:
    examples = turn_examples(TURNS, TURNS_ANSWER, DOCS)
    assert [example.id for example in examples] == [f"bfcl/multi_turn_miss_func_0/turn_{turn}" for turn in range(3)]
    assert [example.query for example in examples] == ["Add 1 and 2.", "", "Tell Ana."]
    assert [names(example) for example in examples] == [["logarithm", "send"], *[["add", "logarithm", "send"]] * 2]
    assert [example.labels for example in examples] == [[], ["add"], ["send"]]
    assert all(example.raw == TURNS | TURNS_ANSWER for example in examples)


def test_a_memory_row_gives_one_example_per_backend_and_no_function_is_a_label() -> None:
    row = {"id": "memory_0", "question": [[user("What is my name?")]], "involved_classes": ["MemoryAPI"]}
    answer = {"id": "memory_0", "ground_truth": ["Ana"], "source": "My name is Ana."}
    examples = agentic_examples(BFCL_MEMORY_FILE, row, answer, DOCS)
    assert [example.id for example in examples] == [f"bfcl/memory_0/{backend}" for backend in BFCL_MEMORY_DOCS]
    assert [names(example) for example in examples] == [[f"{backend}_read"] for backend in BFCL_MEMORY_DOCS]
    assert all(example.labels is None and example.raw == row | answer for example in examples)
    [search] = agentic_examples(BFCL_WEB_SEARCH_FILE, row | {"involved_classes": ["WebSearchAPI"]}, answer, DOCS)
    assert (search.id, names(search), search.labels) == ("bfcl/memory_0", ["search"], None)


@pytest.fixture(scope="module")
def raw_rows() -> dict[str, tuple[Rows, Rows]]:
    """The rows of each downloaded test file and of its ground-truth file. Without such a file the rows are empty."""
    if not (BFCL_RAW_DIR / f"{BFCL_FILE_PREFIX}{BFCL_TEST_FILES[0]}.json").exists():
        pytest.skip("BFCL is not downloaded")
    found = {}
    for name in BFCL_TEST_FILES:
        rows = read_rows(BFCL_RAW_DIR / f"{BFCL_FILE_PREFIX}{name}.json")
        answer_path = BFCL_RAW_DIR / BFCL_ANSWER_DIR / f"{BFCL_FILE_PREFIX}{name}.json"
        found[name] = (rows, read_rows(answer_path) if answer_path.exists() else [{} for _ in rows])
    return found


@pytest.fixture(scope="module")
def processed(raw_rows: dict[str, tuple[Rows, Rows]], tmp_path_factory: pytest.TempPathFactory) -> Processed:
    """The examples and the function list read back from disk after running the converter on the downloaded files."""
    processed_dir: Path = tmp_path_factory.mktemp("bfcl")
    process_bfcl(BFCL_RAW_DIR, processed_dir)
    return read_dataset(processed_dir, BFCL_TEST_FILES)


def split_raw(examples: list[Example], rows: Rows, answers: Rows) -> tuple[Rows, Rows]:
    """Take the merged raw rows apart again, into the rows of the test file and the rows of its ground-truth file.

    A multi-turn or memory row is held by several examples and is taken once.
    """
    kept = list({example.raw["id"]: example.raw for example in examples}.values())
    assert all(set(raw) == set(row) | set(answer) for raw, row, answer in zip(kept, rows, answers, strict=True))
    kept_rows = [{key: raw[key] for key in row} for raw, row in zip(kept, rows, strict=True)]
    kept_answers = [{key: raw[key] for key in answer} for raw, answer in zip(kept, answers, strict=True)]
    return kept_rows, kept_answers


def characters(rows: Rows) -> Counter[str]:
    """Count every character of every key and value in the rows."""
    return Counter(json.dumps(rows, ensure_ascii=False, sort_keys=True))


def test_every_row_of_a_test_file_and_of_its_ground_truth_survives_unchanged(
    raw_rows: dict[str, tuple[Rows, Rows]], processed: Processed
) -> None:
    for name, (rows, answers) in raw_rows.items():
        assert split_raw(processed[0][name], rows, answers) == (rows, answers)


def test_character_counts_match_the_raw_files(raw_rows: dict[str, tuple[Rows, Rows]], processed: Processed) -> None:
    for name, (rows, answers) in raw_rows.items():
        kept_rows, kept_answers = split_raw(processed[0][name], rows, answers)
        assert (characters(kept_rows), characters(kept_answers)) == (characters(rows), characters(answers))


def test_single_turn_options_and_labels_match_the_raw_rows(
    raw_rows: dict[str, tuple[Rows, Rows]], processed: Processed
) -> None:
    for name in BFCL_SINGLE_TURN_FILES:
        rows, answers = raw_rows[name]
        for example, row, answer in zip(processed[0][name], rows, answers, strict=True):
            listed = [(function["name"], function["description"]) for function in row["function"]]
            assert [(option.name, option.description) for option in example.options] == listed
            assert len(row["question"]) == 1 and row["question"][0][-1] == user(example.query)
            if name in BFCL_ANY_CALL_FILES:
                assert example.labels is None
                continue
            assert example.labels is not None and len(set(example.labels)) == len(example.labels)
            called = {function for call in answer.get("ground_truth", []) for function in call}
            assert set(example.labels) == called and called <= {function for function, _ in listed}
            assert bool(example.labels) == (name not in BFCL_NO_CALL_FILES)


# Functions available at a turn in each multi-turn file: median, minimum and maximum, as shown on the dashboard.
FUNCTIONS_PER_TURN = {
    "multi_turn_base": (28, 17, 39),
    "multi_turn_miss_func": (28, 15, 39),
    "multi_turn_miss_param": (28, 17, 39),
    "multi_turn_long_context": (28, 17, 39),
}


def test_multi_turn_examples_match_the_turns_of_the_raw_rows(
    raw_rows: dict[str, tuple[Rows, Rows]], processed: Processed
) -> None:
    unavailable = []
    for name in BFCL_MULTI_TURN_FILES:
        rows, answers = raw_rows[name]
        examples = iter(processed[0][name])
        for row, answer in zip(rows, answers, strict=True):
            for turn, (messages, calls) in enumerate(zip(row["question"], answer["ground_truth"], strict=True)):
                example = next(examples)
                assert example.id == f"bfcl/{row['id']}/turn_{turn}" and example.labels is not None
                assert messages == ([user(example.query)] if messages else []) and (messages or example.query == "")
                assert len(set(names(example))) == len(example.options)
                assert not set(names(example)) & set(row.get("excluded_function", []))
                assert set(example.labels) == {call.split("(")[0] for call in calls}
                unavailable += [(row["id"], turn, label) for label in example.labels if label not in names(example)]
        assert next(examples, None) is None
        sizes = [len(example.options) for example in processed[0][name]]
        assert (median(sizes), min(sizes), max(sizes)) == FUNCTIONS_PER_TURN[name]
    # An inconsistency in BFCL: this ground truth calls a function that its row withholds until turn 3.
    assert unavailable == [("multi_turn_miss_func_49", 1, "tail")]


def test_agentic_examples_have_the_functions_of_their_class_or_backend_and_no_label(
    raw_rows: dict[str, tuple[Rows, Rows]], processed: Processed
) -> None:
    web, memory = processed[0][BFCL_WEB_SEARCH_FILE], processed[0][BFCL_MEMORY_FILE]
    web_rows, memory_rows = raw_rows[BFCL_WEB_SEARCH_FILE][0], raw_rows[BFCL_MEMORY_FILE][0]
    assert [example.raw["id"] for example in web] == [row["id"] for row in web_rows]
    assert [example.raw["id"] for example in memory] == [row["id"] for row in memory_rows for _ in BFCL_MEMORY_DOCS]
    assert Counter(len(example.options) for example in web) == {2: len(web_rows)}
    assert Counter(len(example.options) for example in memory) == dict.fromkeys((15, 12, 5), len(memory_rows))
    for example in web + memory:
        assert example.labels is None and example.raw["question"] == [[user(example.query)]]


def test_the_function_list_holds_every_name_and_description_once(processed: Processed) -> None:
    examples, functions = processed
    pairs = [(function.name, function.description) for function in functions]
    assert len(set(pairs)) == len(pairs)
    assert set(pairs) == {(o.name, o.description) for rows in examples.values() for e in rows for o in e.options}
