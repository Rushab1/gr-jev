"""Tests for grjev.ecthr. The last one converts the downloaded file and is skipped without it."""

from pathlib import Path
from typing import Any

import pyarrow.parquet  # type: ignore[import-untyped]
import pytest

from grjev.constants import ECTHR_ARTICLES, ECTHR_RAW_DIR, ECTHR_RAW_FILE, ECTHR_TEST_FILE, ECTHR_VIOLATED_FILE
from grjev.ecthr import examples_of, process_ecthr
from grjev.examples import read_dataset

ROW: dict[str, Any] = {"text": ["5. The applicant was born in 1955.", "6. He submitted his claim."], "labels": [9, 3]}


def test_the_facts_are_the_query_and_the_10_articles_are_the_options_of_every_case() -> None:
    [example] = examples_of([ROW])
    assert (example.id, example.raw) == ("ecthr/test/0", ROW)
    assert example.query == "5. The applicant was born in 1955.\n6. He submitted his claim."
    assert [(option.name, option.description) for option in example.options] == list(ECTHR_ARTICLES)


def test_the_labels_are_the_violated_articles_and_are_empty_when_none_is_violated() -> None:
    violated, none = examples_of([ROW, ROW | {"labels": []}])
    assert violated.labels == ["Article 6", "Article 1 of Protocol 1"]
    assert none.labels == [] and none.id == "ecthr/test/1"


def test_every_downloaded_case_keeps_its_paragraphs_and_its_labels(tmp_path: Path) -> None:
    if not (ECTHR_RAW_DIR / ECTHR_RAW_FILE).exists():
        pytest.skip("ECtHR is not downloaded")
    rows: list[dict[str, Any]] = pyarrow.parquet.read_table(ECTHR_RAW_DIR / ECTHR_RAW_FILE).to_pylist()
    written = process_ecthr(ECTHR_RAW_DIR, tmp_path)
    examples, articles = read_dataset(tmp_path, (ECTHR_TEST_FILE, ECTHR_VIOLATED_FILE))
    cases = examples[ECTHR_TEST_FILE]
    assert [case.raw for case in cases] == rows and written[f"{ECTHR_TEST_FILE}.jsonl"] == 1000
    # 1,580 paragraphs hold a line feed themselves, so the query is compared whole and not split.
    assert [case.query for case in cases] == ["\n".join(row["text"]) for row in rows]
    assert [len(case.labels or []) for case in cases] == [len(row["labels"]) for row in rows]
    assert sum(not case.labels for case in cases) == 153 and len(articles) == 10
    assert (
        examples[ECTHR_VIOLATED_FILE] == [case for case in cases if case.labels]
        and written[f"{ECTHR_VIOLATED_FILE}.jsonl"] == 847
    )
