"""Print the figures of the models against the shares of the ChaosNLI annotators, one table per test file.

The runs are ANNOTATOR_RUNS in constants.py, and the code is in src/grjev/annotators.py. The rows of Nie et al. (2020)
are ANNOTATOR_BASELINES.
"""

import argparse
from pathlib import Path

from grjev.annotators import Figures, all_figures
from grjev.constants import ANNOTATOR_BASELINES

COLUMNS: list[tuple[str, str]] = [
    ("Examples", "examples"),
    ("Answers, one per order of the labels", "answers"),
    ("Jensen-Shannon distance from the annotators", "jsd"),
    ("Answers on the label with the most votes", "majority"),
    ("Answers on the label of the source dataset", "original"),
    ("Entropy of the probabilities (bits)", "model_entropy"),
    ("Entropy of the shares (bits)", "annotator_entropy"),
    ("Highest probability", "model_top"),
    ("Highest share", "annotator_top"),
]


def cell(value: float | int) -> str:
    """Return a count with a thousands separator, or a figure with two decimals."""
    return f"{value:,}" if isinstance(value, int) else f"{value:.2f}"


def table(test_file: str, by_model: dict[str, Figures]) -> str:
    """Return a Markdown table with the models and the rows of Nie et al. (2020) as rows."""
    lines = ["| Model | " + " | ".join(name for name, _ in COLUMNS) + " |", "|---|" + "---:|" * len(COLUMNS)]
    for name, (jsd, original, majority) in ANNOTATOR_BASELINES[test_file].items():
        published = [cell(jsd), cell(majority), cell(original)]
        lines.append(f"| {name} (Nie et al., 2020) | -- | -- | " + " | ".join(published) + " | -- | -- | -- | -- |")
    for model, figures in by_model.items():
        lines.append(f"| {model} | " + " | ".join(cell(getattr(figures, field)) for _, field in COLUMNS) + " |")
    return "\n".join(lines)


def main() -> None:
    """Print one table per test file, or write them to the file given by --out."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write the tables to this file instead of printing them")
    arguments = parser.parse_args()
    text = "\n\n".join(
        f"### {test_file}\n\n{table(test_file, by_model)}" for test_file, by_model in all_figures().items()
    )
    if arguments.out:
        arguments.out.write_text(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
