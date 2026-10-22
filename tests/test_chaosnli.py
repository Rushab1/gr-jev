"""Tests for grjev.chaosnli. The last one converts the downloaded files and is skipped without them."""

from pathlib import Path
from typing import Any

import pytest

from grjev.chaosnli import alpha_examples, nli_examples, process_chaosnli, process_chaosnli_alpha, read_rows
from grjev.constants import (
    CHAOSNLI_ALPHA_FILE,
    CHAOSNLI_ALPHA_RAW_FILE,
    CHAOSNLI_LABELS,
    CHAOSNLI_NLI_FILES,
    CHAOSNLI_RAW_DIR,
)
from grjev.examples import read_dataset

NLI_ROW: dict[str, Any] = {
    "uid": "46359n",
    "label_counter": {"e": 76, "n": 20, "c": 4},
    "majority_label": "e",
    "label_dist": [0.76, 0.2, 0.04],
    "example": {"uid": "46359n", "premise": "A man walks.", "hypothesis": "A person moves.", "source": "mnli_agree_3"},
}
ALPHA_ROW: dict[str, Any] = {
    "uid": "a05ed03f-1",
    "label_counter": {"2": 91, "1": 9},
    "majority_label": 2,
    "label_dist": [0.09, 0.91],
    "example": {
        "uid": "a05ed03f-1",
        "obs1": "Jo went out.",
        "obs2": "Jo got wet.",
        "hyp1": "It rained.",
        "hyp2": "Jo swam.",
    },
}


def test_an_nli_example_is_the_premise_and_the_hypothesis_with_the_3_labels() -> None:
    [example] = nli_examples([NLI_ROW], "mnli_m")
    assert (example.id, example.raw) == ("chaosnli/mnli_m/46359n", NLI_ROW)
    assert example.query == "Premise: A man walks.\nHypothesis: A person moves."
    assert [(option.name, option.description) for option in example.options] == [
        (name, description) for _, name, description in CHAOSNLI_LABELS
    ]
    assert example.labels == ["entailment"]


def test_an_alpha_example_is_the_two_observations_with_the_two_hypotheses_and_the_majority_hypothesis() -> None:
    [example] = alpha_examples([ALPHA_ROW])
    assert (example.id, example.raw) == ("chaosnli_alpha/alphanli/a05ed03f-1", ALPHA_ROW)
    assert example.query == "Observation 1: Jo went out.\nObservation 2: Jo got wet."
    assert [option.name for option in example.options] == ["It rained.", "Jo swam."]
    assert example.labels == ["Jo swam."]


def test_every_downloaded_row_keeps_its_text_and_its_majority_label(tmp_path: Path) -> None:
    if not (CHAOSNLI_RAW_DIR / CHAOSNLI_ALPHA_RAW_FILE).exists():
        pytest.skip("ChaosNLI is not downloaded")
    written = process_chaosnli(CHAOSNLI_RAW_DIR, tmp_path / "nli") | process_chaosnli_alpha(
        CHAOSNLI_RAW_DIR, tmp_path / "alpha"
    )
    assert written == {"snli.jsonl": 1514, "mnli_m.jsonl": 1599, "alphanli.jsonl": 1532, "tools.jsonl": 3064}
    nli, labels = read_dataset(tmp_path / "nli", tuple(CHAOSNLI_NLI_FILES))
    assert [label.name for label in labels] == ["entailment", "neutral", "contradiction"]
    for test_file, raw_file in CHAOSNLI_NLI_FILES.items():
        rows = read_rows(CHAOSNLI_RAW_DIR / raw_file)
        assert [example.raw for example in nli[test_file]] == rows
        assert all(
            row["example"]["hypothesis"] in example.query for row, example in zip(rows, nli[test_file], strict=True)
        )
    alpha, _ = read_dataset(tmp_path / "alpha", (CHAOSNLI_ALPHA_FILE,))
    rows = read_rows(CHAOSNLI_RAW_DIR / CHAOSNLI_ALPHA_RAW_FILE)
    assert [example.raw for example in alpha[CHAOSNLI_ALPHA_FILE]] == rows
    assert all(len({option.name for option in example.options}) == 2 for example in alpha[CHAOSNLI_ALPHA_FILE])
