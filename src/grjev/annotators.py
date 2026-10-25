"""The probabilities of the models against the shares of the 100 annotators of each ChaosNLI example.

A label's share is the part of the annotators who chose it. The share measures how much the annotators disagree. It is
not the probability that the label is correct. The measures are those of Nie et al. (2020), the Jensen-Shannon distance
and the accuracy on the label with the most votes and on the label of the source dataset, with the entropy and the
highest probability of each distribution next to them.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from math import log, log2, sqrt
from pathlib import Path

from grjev.constants import (
    ANNOTATOR_BIN_EDGES,
    ANNOTATOR_RUNS,
    ANNOTATOR_SMALLEST_PROBABILITY,
    ANNOTATOR_TITLES,
    MODEL_TITLES,
    PROCESSED_DIRS,
    RESULTS_DIR,
    TEST_FILES,
)
from grjev.examples import read_dataset, read_jsonl
from grjev.runs import Row

type Shares = dict[str, float]

NLI_LABELS = {"e": "entailment", "n": "neutral", "c": "contradiction"}


@dataclass(frozen=True)
class Answer:
    """One answer of one model to one order of the labels of one example."""

    example: str
    shares: Shares
    probabilities: Shares
    original: str


@dataclass(frozen=True)
class Bin:
    """The answers of one bin. `mean` and `observed` are the two values averaged over the labels or examples in it."""

    low: float
    high: float
    count: int
    mean: float
    observed: float


@dataclass(frozen=True)
class Figures:
    """The figures of one model on one test file. Each answer to each order of the labels counts once.

    `jsd` is the mean Jensen-Shannon distance from the annotators' shares, and `uniform_jsd` that of a uniform
    distribution over the labels of the same answers. `majority` and `original` are the shares of
    answers whose highest probability is on the label with the most votes and on the label of the source dataset.
    `entropy` and `top` are the mean entropy in bits and the mean highest value, of the model and of the annotators.
    """

    examples: int
    answers: int
    jsd: float
    uniform_jsd: float
    majority: float
    original: float
    model_entropy: float
    annotator_entropy: float
    model_top: float
    annotator_top: float


def mean(values: Sequence[float]) -> float:
    """Return the mean, or NaN for no values."""
    return sum(values) / len(values) if values else float("nan")


def shares_of(raw: dict) -> Shares:
    """Return the annotators' share of each label of a raw ChaosNLI row, by the name sent to the model."""
    return dict(zip(label_names(raw), raw["label_dist"], strict=True))


def label_names(raw: dict) -> list[str]:
    """Return the labels of a raw ChaosNLI row in the order of its shares, by the name sent to the model."""
    if "premise" in raw["example"]:
        return list(NLI_LABELS.values())
    return [raw["example"]["hyp1"], raw["example"]["hyp2"]]


def original_label(raw: dict) -> str:
    """Return the label of the example in SNLI, MNLI or alphaNLI, by the name sent to the model."""
    old = raw["old_label"]
    return NLI_LABELS[old] if old in NLI_LABELS else label_names(raw)[int(old) - 1]


def entropy(values: Shares) -> float:
    """Return the entropy of a distribution in bits: 0 for one label at 1.00, 1 for two labels at 0.50."""
    return sum(-value * log2(value) for value in values.values() if value > 0)


def highest(values: Shares) -> str:
    """Return the label with the highest value, and the first of the labels in a tie."""
    return max(values, key=lambda name: values[name])


def kullback_leibler(first: Shares, second: Shares) -> float:
    """Return the Kullback-Leibler divergence of `first` from `second` in nats, over the labels of `first`."""
    return sum(
        value * log(value / max(second.get(name, 0.0), ANNOTATOR_SMALLEST_PROBABILITY))
        for name, value in first.items()
        if value > 0
    )


def jensen_shannon(first: Shares, second: Shares) -> float:
    """Return the Jensen-Shannon distance of Nie et al. (2020), the square root of the divergence in nats."""
    held = {name: second.get(name, 0.0) for name in first}
    middle = {name: (value + held[name]) / 2 for name, value in first.items()}
    return sqrt(max(0.0, (kullback_leibler(first, middle) + kullback_leibler(held, middle)) / 2))


def gap(shares: Shares, probabilities: Shares) -> float:
    """Return the value of the label with the most votes minus that of the label with the second most."""
    first, second = sorted(shares, key=lambda name: shares[name], reverse=True)[:2]
    return probabilities.get(first, 0.0) - probabilities.get(second, 0.0)


def uniform(shares: Shares) -> Shares:
    """Return the same probability for every label of `shares`."""
    return {name: 1 / len(shares) for name in shares}


def figures(answers: Sequence[Answer]) -> Figures:
    """Return the figures of the answers of one model to one test file."""
    return Figures(
        examples=len({answer.example for answer in answers}),
        answers=len(answers),
        jsd=mean([jensen_shannon(answer.shares, answer.probabilities) for answer in answers]),
        uniform_jsd=mean([jensen_shannon(answer.shares, uniform(answer.shares)) for answer in answers]),
        majority=mean([highest(answer.probabilities) == highest(answer.shares) for answer in answers]),
        original=mean([highest(answer.probabilities) == answer.original for answer in answers]),
        model_entropy=mean([entropy(answer.probabilities) for answer in answers]),
        annotator_entropy=mean([entropy(answer.shares) for answer in answers]),
        model_top=mean([max(answer.probabilities.values()) for answer in answers]),
        annotator_top=mean([max(answer.shares.values()) for answer in answers]),
    )


def binned(pairs: Sequence[tuple[float, float]]) -> list[Bin]:
    """Return one bin per step of ANNOTATOR_BIN_EDGES, holding the pairs whose first value falls in it. A pair is the
    value that places it in a bin and the value observed with it. Empty bins are left out."""
    edges = list(zip(ANNOTATOR_BIN_EDGES, ANNOTATOR_BIN_EDGES[1:], strict=False))
    held: list[list[tuple[float, float]]] = [[] for _ in edges]
    for placed, observed in pairs:
        held[min(int(placed * len(edges)), len(edges) - 1)].append((placed, observed))
    return [
        Bin(low, high, len(part), mean([p for p, _ in part]), mean([o for _, o in part]))
        for (low, high), part in zip(edges, held, strict=True)
        if part
    ]


def reliability_bins(answers: Sequence[Answer]) -> list[Bin]:
    """Return the bins of every label by the probability the model gives it, against the share of the annotators."""
    return binned(
        [(answer.probabilities.get(name, 0.0), share) for answer in answers for name, share in answer.shares.items()]
    )


def gap_bins(answers: Sequence[Answer]) -> list[Bin]:
    """Return the bins of every answer by the annotators' gap, against the model's gap on the same two labels."""
    return binned(
        [(gap(answer.shares, answer.shares), abs(gap(answer.shares, answer.probabilities))) for answer in answers]
    )


def annotator_ece(bins: Sequence[Bin]) -> float:
    """Return the distance between the mean probability and the mean share of the annotators in each bin, averaged
    over the bins with the number of labels as weight."""
    return sum(part.count * abs(part.observed - part.mean) for part in bins) / sum(part.count for part in bins)


def read_answers(dataset: str, folder: Path) -> dict[str, list[Answer]]:
    """Return the answers of one results folder by test file. Refused and rejected lists have no answer."""
    examples, _ = read_dataset(PROCESSED_DIRS[dataset], TEST_FILES[dataset])
    raw = {example.id: example.raw for file in examples.values() for example in file}
    out: dict[str, list[Answer]] = {}
    for row in read_jsonl(folder / "rows.jsonl", Row):
        shares, original = shares_of(raw[row.id]), original_label(raw[row.id])
        for answer in row.answers.values():
            out.setdefault(row.test_file, []).append(Answer(row.id, shares, answer.probabilities, original))
    return out


def all_answers() -> dict[str, dict[str, list[Answer]]]:
    """Return the answers of every run of ANNOTATOR_RUNS, by test file and then by model title."""
    out: dict[str, dict[str, list[Answer]]] = {}
    for dataset, runs in ANNOTATOR_RUNS.items():
        for model, run in runs.items():
            for test_file, answers in read_answers(dataset, RESULTS_DIR / run).items():
                out.setdefault(test_file, {})[MODEL_TITLES[model]] = answers
    return out


def all_figures() -> dict[str, dict[str, Figures]]:
    """Return the figures of every run of ANNOTATOR_RUNS, by test file and then by model title."""
    return {
        test_file: {model: figures(answers) for model, answers in by_model.items()}
        for test_file, by_model in all_answers().items()
    }


def paper_row(name: str, cells: Sequence[str]) -> str:
    """Return one row of the LaTeX table."""
    return f"{name} & " + " & ".join(cells) + r" \\"


def paper_table() -> str:
    """Return a LaTeX `tabular` with a block of rows for each test file, a uniform distribution first and the 100
    annotators last."""
    lines = [r"\begin{tabular}{lrrrrr}", r"\toprule"]
    lines.append(paper_row("Model", ["JSD", "Source label", "Most votes", "Entropy", "Highest"]))
    for test_file, by_model in all_figures().items():
        lines += [r"\midrule", rf"\multicolumn{{6}}{{l}}{{\emph{{{ANNOTATOR_TITLES[test_file]}}}}} \\"]
        uniform = next(iter(by_model.values())).uniform_jsd
        lines.append(paper_row("Uniform", [f"{uniform:.2f}", "--", "--", "--", "--"]))
        for model, found in by_model.items():
            cells = [f"{found.jsd:.2f}", f"{found.original:.0%}", f"{found.majority:.0%}"]
            lines.append(paper_row(model, [*cells, f"{found.model_entropy:.2f}", f"{found.model_top:.2f}"]))
        first = next(iter(by_model.values()))
        lines.append(
            paper_row(
                "100 annotators", ["--", "--", "--", f"{first.annotator_entropy:.2f}", f"{first.annotator_top:.2f}"]
            )
        )
    return "\n".join([*lines, r"\bottomrule", r"\end{tabular}", ""]).replace("%", r"\%")


def ece_paper_table() -> str:
    """Return a LaTeX `tabular` of the ECE in percentage points against the annotators' shares, one column per test
    file."""
    found = all_answers()
    models = list(next(iter(found.values())))
    lines = [r"\begin{tabular}{l" + "r" * len(found) + "}", r"\toprule"]
    lines += [paper_row("Model", [ANNOTATOR_TITLES[test_file] for test_file in found]), r"\midrule"]
    for model in models:
        cells = [f"{100 * annotator_ece(reliability_bins(by_model[model])):.0f}" for by_model in found.values()]
        lines.append(paper_row(model, cells))
    return "\n".join([*lines, r"\bottomrule", r"\end{tabular}", ""])
