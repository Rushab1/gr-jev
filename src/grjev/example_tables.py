"""One example from each dataset and test file, with the probabilities of the three models.

Each row of EXAMPLE_TABLE_ROWS names a dataset, a test file, the results folder of Jev and the list in it. The example
is the first by id that the run holds for that test file. The choices are given in the order they were sent. A query or
a choice longer than its limit is cut at a space and followed by an ellipsis.
"""

from dataclasses import dataclass
from pathlib import Path

from grjev.annotators import shares_of
from grjev.constants import (
    EXAMPLE_CHOICE_CHARACTERS,
    EXAMPLE_MODEL_HEADERS,
    EXAMPLE_QUERY_CHARACTERS,
    EXAMPLE_TABLE_MODELS,
    EXAMPLE_TABLE_ROWS,
    EXAMPLE_TITLES,
    PROCESSED_DIRS,
    RESULTS_DIR,
    RESULTS_MODEL_NAMES,
)
from grjev.examples import Example, read_dataset, read_jsonl
from grjev.runs import Row

ESCAPED = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_\allowbreak ",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde ",
}


@dataclass(frozen=True)
class Shown:
    """One example to print, with the probability each model gives each choice in the order sent."""

    title: str
    query: str
    choices: list[str]
    labels: list[str]
    shares: dict[str, float]
    probabilities: dict[str, dict[str, float]]


def escaped(text: str) -> str:
    """Return the text with the characters that LaTeX reads as commands written out."""
    return "".join(ESCAPED.get(letter, letter) for letter in " ".join(text.split()))


def shortened(text: str, limit: int) -> str:
    """Return the text cut at the last space before `limit` and followed by an ellipsis."""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "\\ldots"


def folder_of(run: str, model: str) -> Path:
    """Return the results folder of a model, from the folder of Jev."""
    name, date = run.split("/")
    suffix = RESULTS_MODEL_NAMES.get(model)
    return RESULTS_DIR / (f"{name}_{suffix}" if suffix else name) / date


def first_row(folder: Path, test_file: str) -> Row:
    """Return the first row of the run by id, among the rows of one test file."""
    rows = [row for row in read_jsonl(folder / "rows.jsonl", Row) if row.test_file == test_file]
    return min(rows, key=lambda row: row.id)


def example_of(dataset: str, test_file: str, example_id: str) -> Example:
    """Return the example of a test file by its id."""
    examples, _ = read_dataset(PROCESSED_DIRS[dataset], (test_file,))
    return next(example for example in examples[test_file] if example.id == example_id)


def shown(dataset: str, test_file: str, run: str, listed: str) -> Shown:
    """Return the first example of one run, with the answer of each model to one of its lists."""
    row = first_row(folder_of(run, EXAMPLE_TABLE_MODELS[0]), test_file)
    example = example_of(dataset, test_file, row.id)
    probabilities = {}
    for model in EXAMPLE_TABLE_MODELS:
        answer = first_row(folder_of(run, model), test_file).answers[listed]
        probabilities[model] = answer.probabilities
    shares = shares_of(example.raw) if dataset.startswith("chaosnli") else {}
    choices = row.answers[listed].candidates
    return Shown(EXAMPLE_TITLES[test_file], example.query, choices, row.labels, shares, probabilities)


def choice_row(shown_example: Shown, choice: str) -> str:
    """Return the row of one choice, marked when it is correct, with the share and the probabilities."""
    name = escaped(shortened(choice, EXAMPLE_CHOICE_CHARACTERS))
    marked = rf"{name}$^\star$" if choice in shown_example.labels else name
    share = f"{shown_example.shares[choice]:.2f}" if choice in shown_example.shares else "--"
    cells = [f"{shown_example.probabilities[model].get(choice, 0.0):.2f}" for model in EXAMPLE_TABLE_MODELS]
    return f"{marked} & {share} & " + " & ".join(cells) + r" \\"


def full_width(text: str) -> str:
    """Return a row that spans the five columns of the table."""
    return rf"\multicolumn{{5}}{{@{{}}p{{\linewidth}}@{{}}}}{{{text}}} \\"


def header() -> str:
    """Return the row of column names."""
    return (
        "Choice & Annotators & " + " & ".join(EXAMPLE_MODEL_HEADERS[model] for model in EXAMPLE_TABLE_MODELS) + r" \\"
    )


def block(shown_example: Shown) -> list[str]:
    """Return the tabular of one example: its name in bold, its query, the column names and one row per choice."""
    query = escaped(shortened(shown_example.query, EXAMPLE_QUERY_CHARACTERS))
    # The choice column and the four number columns add up to the width of the rows that span them.
    return [
        r"\noindent\begin{tabular}{@{}>{\raggedright\arraybackslash}p{\dimexpr0.54\linewidth-24pt}"
        r">{\raggedleft\arraybackslash}p{0.19\linewidth}*{3}{>{\raggedleft\arraybackslash}p{0.09\linewidth}}@{}}",
        full_width(rf"\textbf{{{shown_example.title}}}"),
        full_width(query),
        r"\addlinespace[2pt]",
        r"\toprule",
        header(),
        r"\midrule",
        *[choice_row(shown_example, choice) for choice in shown_example.choices],
        r"\bottomrule",
        r"\end{tabular}",
        r"\par\bigskip",
    ]


def paper_table() -> str:
    """Return one LaTeX tabular per row of EXAMPLE_TABLE_ROWS. Columns and pages break only between examples."""
    lines = [r"\setlength{\tabcolsep}{3pt}", r"\par\medskip"]
    for dataset, test_file, run, listed in EXAMPLE_TABLE_ROWS:
        lines += block(shown(dataset, test_file, run, listed))
    return "\n".join([*lines, ""])
