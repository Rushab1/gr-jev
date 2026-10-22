"""The probabilities of the models against the shares of the 100 annotators of each ChaosNLI example.

A label's share is the part of the annotators who chose it. An example is split when two labels each have at least
ANNOTATOR_SPLIT_SHARE of the annotators, and clear otherwise. The share is a measure of how much people disagree,
not the probability that the label is correct.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from grjev.constants import (
    ANNOTATOR_EDGES,
    ANNOTATOR_MIDDLE,
    ANNOTATOR_RUNS,
    ANNOTATOR_SPLIT_SHARE,
    MODEL_TITLES,
    PROCESSED_DIRS,
    RESULTS_DIR,
    TEST_FILES,
)
from grjev.examples import read_dataset, read_jsonl
from grjev.runs import Row

type Shares = dict[str, float]


@dataclass(frozen=True)
class SplitFigures:
    """Figures of one model on one test file. Shares are fractions, and each answer to one order counts once.

    `ends` is the share of labels below the low edge or above the high edge, for the annotators and for the model.
    `middle_ends` is that share of the model, on the labels that ANNOTATOR_MIDDLE of the annotators chose. The gap of an
    example is the share or probability of the label most annotators chose minus that of the second label. A distance
    is the total variation distance from the annotators' shares.
    """

    examples: int
    answers: int
    annotator_ends: float
    model_below: float
    model_above: float
    middle_labels: int
    middle_ends: float
    split: int
    annotator_gap: float
    model_gap: float
    minority: float
    split_distance: float
    uniform_distance: float
    majority_distance: float
    clear_distance: float
    clear_majority_distance: float
    order_change: float


def mean(values: Sequence[float]) -> float:
    """Return the mean, or NaN for no values."""
    return sum(values) / len(values) if values else float("nan")


def shares_of(raw: dict) -> Shares:
    """Return the annotators' share of each label of a raw ChaosNLI row, by the name sent to the model."""
    names = (
        ["entailment", "neutral", "contradiction"]
        if "premise" in raw["example"]
        else [raw["example"]["hyp1"], raw["example"]["hyp2"]]
    )
    return dict(zip(names, raw["label_dist"], strict=True))


def distance(first: Shares, second: Shares) -> float:
    """Return the total variation distance: half the sum of the absolute differences over the labels."""
    return sum(abs(first.get(name, 0.0) - second.get(name, 0.0)) for name in first.keys() | second.keys()) / 2


def gap(shares: Shares, probabilities: Shares) -> float:
    """Return the probability of the label most annotators chose minus that of the second label."""
    first, second = sorted(shares, key=shares.__getitem__, reverse=True)[:2]
    return probabilities.get(first, 0.0) - probabilities.get(second, 0.0)


def is_split(shares: Shares) -> bool:
    """Say whether two labels each have at least ANNOTATOR_SPLIT_SHARE of the annotators."""
    return sorted(shares.values())[-2] >= ANNOTATOR_SPLIT_SHARE


def at_ends(value: float) -> bool:
    """Say whether a share or a probability is below the low edge or above the high edge."""
    return value < ANNOTATOR_EDGES[0] or value > ANNOTATOR_EDGES[1]


def figures(items: Sequence[tuple[Shares, list[Shares]]]) -> SplitFigures:
    """Return the figures of a list of examples, each with its shares and the model's answer to each order."""
    labels = [
        (shares[name], answer.get(name, 0.0)) for shares, answers in items for answer in answers for name in shares
    ]
    low, high = ANNOTATOR_MIDDLE
    middle = [probability for share, probability in labels if low <= share <= high]
    split = [(shares, answers) for shares, answers in items if is_split(shares)]
    clear = [(shares, answers) for shares, answers in items if not is_split(shares)]
    split_answers = [(shares, answer) for shares, answers in split for answer in answers]
    return SplitFigures(
        examples=len(items),
        answers=sum(len(answers) for _, answers in items),
        annotator_ends=mean([at_ends(share) for share, _ in labels]),
        model_below=mean([probability < ANNOTATOR_EDGES[0] for _, probability in labels]),
        model_above=mean([probability > ANNOTATOR_EDGES[1] for _, probability in labels]),
        middle_labels=len(middle),
        middle_ends=mean([at_ends(probability) for probability in middle]),
        split=len(split),
        annotator_gap=mean([gap(shares, shares) for shares, _ in split]),
        model_gap=mean([abs(gap(shares, answer)) for shares, answer in split_answers]),
        minority=mean([gap(shares, answer) < 0 for shares, answer in split_answers]),
        split_distance=mean([distance(shares, answer) for shares, answer in split_answers]),
        uniform_distance=mean([distance(shares, dict.fromkeys(shares, 1 / len(shares))) for shares, _ in split]),
        majority_distance=mean([distance(shares, {max(shares, key=shares.__getitem__): 1.0}) for shares, _ in split]),
        clear_distance=mean([distance(shares, answer) for shares, answers in clear for answer in answers]),
        clear_majority_distance=mean(
            [distance(shares, {max(shares, key=shares.__getitem__): 1.0}) for shares, _ in clear]
        ),
        order_change=mean(
            [
                max(a.get(n, 0.0) for a in answers) - min(a.get(n, 0.0) for a in answers)
                for s, answers in items
                for n in s
            ]
        ),
    )


def run_figures(dataset: str, folder: Path) -> dict[str, SplitFigures]:
    """Return the figures of one results folder by test file. Refused and rejected lists have no answer."""
    examples, _ = read_dataset(PROCESSED_DIRS[dataset], TEST_FILES[dataset])
    shares = {example.id: shares_of(example.raw) for file in examples.values() for example in file}
    by_file: dict[str, list[tuple[Shares, list[Shares]]]] = {}
    for row in read_jsonl(folder / "rows.jsonl", Row):
        answers = [answer.probabilities for answer in row.answers.values()]
        by_file.setdefault(row.test_file, []).append((shares[row.id], answers))
    return {test_file: figures(items) for test_file, items in by_file.items()}


def all_figures() -> dict[str, dict[str, SplitFigures]]:
    """Return the figures of every run of ANNOTATOR_RUNS, by test file and then by model title."""
    out: dict[str, dict[str, SplitFigures]] = {}
    for dataset, runs in ANNOTATOR_RUNS.items():
        for model, folder in runs.items():
            for test_file, values in run_figures(dataset, RESULTS_DIR / folder).items():
                out.setdefault(test_file, {})[MODEL_TITLES[model]] = values
    return out
