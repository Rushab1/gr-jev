"""Print the probabilities of the models against the shares of the ChaosNLI annotators, one table per test file.

The runs are ANNOTATOR_RUNS in constants.py, and the code is in src/grjev/annotators.py.
"""

from grjev.annotators import SplitFigures, all_figures

ROWS: list[tuple[str, str]] = [
    ("Examples", "examples"),
    ("Answers, one per order of the labels", "answers"),
    ("Labels below 0.1 or above 0.9, annotators", "annotator_ends"),
    ("Labels below 0.1, model", "model_below"),
    ("Labels above 0.9, model", "model_above"),
    ("Labels that 30% to 70% of annotators chose, once per order", "middle_labels"),
    ("Of those, below 0.1 or above 0.9, model", "middle_ends"),
    ("Split examples, two labels with at least 30% each", "split"),
    ("Split examples, annotators' gap between the two labels", "annotator_gap"),
    ("Split examples, model's gap between the two labels", "model_gap"),
    ("Split examples, answers that favour the label fewer annotators chose", "minority"),
    ("Split examples, distance of the model from the annotators", "split_distance"),
    ("Split examples, distance of 1/n on each label", "uniform_distance"),
    ("Split examples, distance of all on the majority label", "majority_distance"),
    ("Clear examples, distance of the model", "clear_distance"),
    ("Clear examples, distance of all on the majority label", "clear_majority_distance"),
    ("Mean change of a label's probability over the orders", "order_change"),
]
SHARES = {"annotator_ends", "model_below", "model_above", "middle_ends", "minority"}


def cell(name: str, value: float) -> str:
    """Return a count with a thousands separator, a share as a percentage, or a probability with 2 decimals."""
    if isinstance(value, int):
        return f"{value:,}"
    return f"{100 * value:.0f}%" if name in SHARES else f"{value:.2f}"


def table(by_model: dict[str, SplitFigures]) -> str:
    """Return a Markdown table with the measures as rows and the models as columns."""
    models = list(by_model)
    lines = ["| Measure | " + " | ".join(models) + " |", "|---|" + "---:|" * len(models)]
    for title, name in ROWS:
        lines.append(f"| {title} | " + " | ".join(cell(name, getattr(by_model[m], name)) for m in models) + " |")
    return "\n".join(lines)


def main() -> None:
    """Print one table per test file."""
    for test_file, by_model in all_figures().items():
        print(f"### {test_file}\n\n{table(by_model)}\n")


if __name__ == "__main__":
    main()
