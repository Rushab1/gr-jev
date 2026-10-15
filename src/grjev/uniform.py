"""Correct options whose probability is below 1/n, for a list of n options.

1/n is the probability of each option when the model spreads its probability evenly over the list. It is not the
probability that an option is correct.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from grjev.constants import MODEL_TITLES, PROBABILITY_DECIMALS, REPO_ROOT, TABLES_DIR, UNIFORM_DEFINITION
from grjev.examples import read_jsonl
from grjev.runs import ListAnswer, Row
from grjev.tables import keeps, model_folder, read_spec

COUNT_HEADERS = [
    "Answered lists",
    "Refused lists",
    "Lists with a correct option below 1/n",
    "Lists with every correct option above every distractor",
    "Of those, lists with a correct option below 1/n",
    "Correct options",
    "Correct options below 1/n",
]


@dataclass(frozen=True)
class BelowUniform:
    """Counts over the lists of some examples with two or more labels.

    `lists` counts the answered lists, `refused` the lists the model refused, `correct` the correct options of the
    answered lists, `below` those with a probability below 1/n, and `lists_below` the lists with at least one of them.
    `ranked` counts the answered lists whose correct options are all above every distractor, and `ranked_below`
    those of them with a correct option below 1/n.
    """

    lists: int
    refused: int
    correct: int
    below: int
    lists_below: int
    ranked: int
    ranked_below: int


def correct_below(labels: Sequence[str], answer: ListAnswer) -> list[str]:
    """Return the labels whose probability is below 1/n, for the n options of the list that was sent.

    The list must hold every label and have a probability for each option. A probability is rounded to
    PROBABILITY_DECIMALS first, so that 0.09999999999999999 counts as 0.1.
    """
    if set(answer.probabilities) != set(answer.candidates):
        raise ValueError(f"the probabilities name {sorted(answer.probabilities)}, the list {answer.candidates}")
    missing = [label for label in labels if label not in answer.candidates]
    if missing:
        raise ValueError(f"the list does not hold the labels {missing}")
    uniform = round(1 / len(answer.candidates), PROBABILITY_DECIMALS)
    return [label for label in labels if round(answer.probabilities[label], PROBABILITY_DECIMALS) < uniform]


def ranked_correctly(labels: Sequence[str], answer: ListAnswer) -> bool:
    """Return whether every label has a higher probability than every distractor, after rounding to
    PROBABILITY_DECIMALS. A tie between a label and a distractor is not a correct ranking."""
    probabilities = {name: round(value, PROBABILITY_DECIMALS) for name, value in answer.probabilities.items()}
    distractors = [value for name, value in probabilities.items() if name not in labels]
    return min(probabilities[label] for label in labels) > max(distractors)


def counted(rows: Sequence[Row], name: str) -> BelowUniform:
    """Return the counts of the list of that name over the examples with two or more labels.

    An answered list counts when it holds a distractor. A refused list counts on its labels alone, because a row does
    not save the options of a list that the model refused. A list that is neither answered nor refused raises.
    """
    several = [row for row in rows if len(row.labels) > 1]
    lost = [row.id for row in several if name not in row.answers and name not in row.refused]
    if lost:
        raise ValueError(f"{len(lost)} examples have no answer and no refusal for {name}, such as {lost[0]}")
    answered = [
        (row.labels, row.answers[name])
        for row in several
        if name in row.answers and len(row.answers[name].candidates) > len(row.labels)
    ]
    below = [correct_below(labels, answer) for labels, answer in answered]
    ranked = [ranked_correctly(labels, answer) for labels, answer in answered]
    return BelowUniform(
        lists=len(answered),
        refused=sum(name in row.refused for row in several),
        correct=sum(len(labels) for labels, _ in answered),
        below=sum(len(found) for found in below),
        lists_below=sum(bool(found) for found in below),
        ranked=sum(ranked),
        ranked_below=sum(good and bool(found) for good, found in zip(ranked, below, strict=True)),
    )


def by_labels(rows: Sequence[Row]) -> dict[int, list[Row]]:
    """Return the rows by the number of labels of their example, from the lowest number."""
    groups: dict[int, list[Row]] = {}
    for row in sorted(rows, key=lambda row: len(row.labels)):
        groups.setdefault(len(row.labels), []).append(row)
    return groups


def share(count: int, total: int) -> str:
    """Return a count with its percentage of the total."""
    return f"{count:,} ({100 * count / total:.1f}%)" if total else f"{count:,}"


def cells(found: BelowUniform) -> list[str]:
    """Return the cells of the counts of one model."""
    return [
        f"{found.lists:,}",
        f"{found.refused:,}",
        share(found.lists_below, found.lists),
        share(found.ranked, found.lists),
        share(found.ranked_below, found.ranked),
        f"{found.correct:,}",
        share(found.below, found.correct),
    ]


def table(first: list[str], body: list[list[str]]) -> list[str]:
    """Return the lines of a Markdown table: the first columns name the lists and the model, the others are counts."""
    header = [*first, *COUNT_HEADERS]
    align = ["---"] * len(first) + ["---:"] * len(COUNT_HEADERS)
    return [f"| {' | '.join(line)} |" for line in (header, align, *body)]


def document(runs: dict[str, tuple[str, str]], by_label: Sequence[str], root: Path = REPO_ROOT) -> str:
    """Return the counts of each run and model as a Markdown document, with the results folders that it reads.

    `runs` maps a dataset to the label of its row in the definition UNIFORM_DEFINITION and the list that it uses. A
    dataset in `by_label` gets a second table by the number of labels of the example.
    """
    spec = read_spec(TABLES_DIR / f"{UNIFORM_DEFINITION}.json")
    rows = {row.label: row for row in spec.rows}
    totals, folders = [], []
    groups: dict[str, list[list[str]]] = {dataset: [] for dataset in by_label}
    for dataset, (label, name) in runs.items():
        for model in spec.models:
            folder = model_folder(rows[label].folder, model, root)
            found = [row for row in read_jsonl(root / folder / "rows.jsonl", Row) if keeps(rows[label], row)]
            folders.append(f"- {dataset}, {MODEL_TITLES[model]}: `{folder}`, list `{name}`")
            totals.append([dataset, MODEL_TITLES[model], *cells(counted(found, name))])
            for number, own in by_labels(found).items() if dataset in by_label else ():
                groups[dataset].append([str(number), MODEL_TITLES[model], *cells(counted(own, name))])
    lines = ["# Correct options below 1/n", "", *table(["Dataset", "Model"], totals)]
    for dataset, body in groups.items():
        lines += ["", f"## {dataset} by the number of correct options", ""]
        lines += table(["Correct options in the list", "Model"], sorted(body, key=lambda cells: int(cells[0])))
    return "\n".join([*lines, "", "## Results folders", "", *folders]) + "\n"
