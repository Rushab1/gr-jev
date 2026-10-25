"""Convert ChaosNLI into the common format: SNLI and MNLI with three labels, and αNLI with two hypotheses."""

import json
from pathlib import Path
from typing import Any

from grjev.constants import (
    CHAOSNLI_ALPHA_FILE,
    CHAOSNLI_ALPHA_RAW_FILE,
    CHAOSNLI_LABELS,
    CHAOSNLI_NLI_FILES,
    TOOLS_FILE_NAME,
)
from grjev.examples import Example, Option, distinct_options, write_jsonl

LABELS = [Option(name=name, description=description) for _, name, description in CHAOSNLI_LABELS]
LABEL_NAMES = {code: name for code, name, _ in CHAOSNLI_LABELS}


def read_rows(path: Path) -> list[dict[str, Any]]:
    """Return the rows of a ChaosNLI file, one JSON object per line."""
    return [json.loads(line) for line in path.read_text().split("\n") if line]


def nli_examples(rows: list[dict[str, Any]], test_file: str) -> list[Example]:
    """Convert the rows of SNLI or MNLI. The premise and the hypothesis are the query, and the 3 labels the options.

    The label is the one that most of the 100 annotators of ChaosNLI chose.
    """
    return [
        Example(
            id=f"chaosnli/{test_file}/{row['uid']}",
            query=f"Premise: {row['example']['premise']}\nHypothesis: {row['example']['hypothesis']}",
            options=LABELS,
            labels=[LABEL_NAMES[row["majority_label"]]],
            raw=row,
        )
        for row in rows
    ]


def alpha_examples(rows: list[dict[str, Any]]) -> list[Example]:
    """Convert the rows of αNLI. The two observations are the query, and the two hypotheses the options.

    A hypothesis is named by its text and has no description. The label is the hypothesis that most of the 100
    annotators of ChaosNLI chose.
    """
    examples = []
    for row in rows:
        hypotheses = [row["example"]["hyp1"], row["example"]["hyp2"]]
        examples.append(
            Example(
                id=f"chaosnli_alpha/{CHAOSNLI_ALPHA_FILE}/{row['uid']}",
                query=f"Observation 1: {row['example']['obs1']}\nObservation 2: {row['example']['obs2']}",
                options=[Option(name=hypothesis, description="") for hypothesis in hypotheses],
                labels=[hypotheses[row["majority_label"] - 1]],
                raw=row,
            )
        )
    return examples


def process_chaosnli(raw_dir: Path, processed_dir: Path) -> dict[str, int]:
    """Write the SNLI and the MNLI examples and the 3 labels. Return the rows written."""
    written = {}
    for test_file, raw_file in CHAOSNLI_NLI_FILES.items():
        examples = nli_examples(read_rows(raw_dir / raw_file), test_file)
        write_jsonl(processed_dir / f"{test_file}.jsonl", examples)
        written[f"{test_file}.jsonl"] = len(examples)
    write_jsonl(processed_dir / TOOLS_FILE_NAME, LABELS)
    return written | {TOOLS_FILE_NAME: len(LABELS)}


def process_chaosnli_alpha(raw_dir: Path, processed_dir: Path) -> dict[str, int]:
    """Write the αNLI examples and their distinct hypotheses. Return the rows written."""
    examples = alpha_examples(read_rows(raw_dir / CHAOSNLI_ALPHA_RAW_FILE))
    hypotheses = distinct_options(examples)
    write_jsonl(processed_dir / f"{CHAOSNLI_ALPHA_FILE}.jsonl", examples)
    write_jsonl(processed_dir / TOOLS_FILE_NAME, hypotheses)
    return {f"{CHAOSNLI_ALPHA_FILE}.jsonl": len(examples), TOOLS_FILE_NAME: len(hypotheses)}
