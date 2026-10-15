"""Tests for grjev.hotpotqa. The last one converts the downloaded file and is skipped without it."""

from pathlib import Path
from typing import Any

import pyarrow.parquet  # type: ignore[import-untyped]
import pytest

from grjev.constants import HOTPOTQA_RAW_DIR, HOTPOTQA_RAW_FILE, HOTPOTQA_TEN_FILE, HOTPOTQA_TEST_FILE
from grjev.examples import Option, read_dataset
from grjev.hotpotqa import examples_of, process_hotpotqa

ROW: dict[str, Any] = {
    "id": "abc",
    "question": "Which film stars the actress?",
    "answer": "The Film",
    "type": "bridge",
    "level": "hard",
    "supporting_facts": {"title": ["The Film", "The Actress", "The Film"], "sent_id": [0, 1, 2]},
    "context": {
        "title": ["Other", "The Actress", "The Film"],
        "sentences": [["Unrelated."], ["She was born.", " She acts."], ["It is a film.", " She stars in it."]],
    },
}


def test_a_question_is_the_query_and_its_passages_are_options_named_by_their_title() -> None:
    [example] = examples_of([ROW])
    assert (example.id, example.query, example.raw) == ("hotpotqa/validation/abc", "Which film stars the actress?", ROW)
    assert example.options[1] == Option(name="The Actress", description="She was born. She acts.")
    assert [option.name for option in example.options] == ["Other", "The Actress", "The Film"]


def test_the_labels_are_the_titles_with_a_supporting_fact_once_each_in_the_order_of_the_passages() -> None:
    assert examples_of([ROW])[0].labels == ["The Actress", "The Film"]


def test_every_downloaded_question_keeps_its_passages_and_its_two_supporting_titles(tmp_path: Path) -> None:
    if not (HOTPOTQA_RAW_DIR / HOTPOTQA_RAW_FILE).exists():
        pytest.skip("HotpotQA is not downloaded")
    rows: list[dict[str, Any]] = pyarrow.parquet.read_table(HOTPOTQA_RAW_DIR / HOTPOTQA_RAW_FILE).to_pylist()
    written = process_hotpotqa(HOTPOTQA_RAW_DIR, tmp_path)
    examples, passages = read_dataset(tmp_path, (HOTPOTQA_TEST_FILE, HOTPOTQA_TEN_FILE))
    assert [example.raw for example in examples[HOTPOTQA_TEST_FILE]] == rows
    assert written[f"{HOTPOTQA_TEST_FILE}.jsonl"] == len(rows) == 7405
    assert all(len(example.labels or []) == 2 for example in examples[HOTPOTQA_TEST_FILE])
    assert all(len(example.options) == 10 for example in examples[HOTPOTQA_TEN_FILE])
    assert len(examples[HOTPOTQA_TEN_FILE]) == 7345
    for example, row in zip(examples[HOTPOTQA_TEST_FILE], rows, strict=True):
        texts = ["".join(sentences).strip() for sentences in row["context"]["sentences"]]
        assert [option.description for option in example.options] == texts
    assert {option.name for example in examples[HOTPOTQA_TEN_FILE] for option in example.options} == {
        passage.name for passage in passages
    }
