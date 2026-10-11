"""Figures of the probability distribution of answers.

They are the accuracy and the calibration of the prediction, the differences between the probabilities of correct
options and of distractors, and the probabilities by position. An option is one entry of the list that is sent.
"""

import statistics
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from grjev.constants import (
    ECE_BINS,
    FULL_LIST,
    PROBABILITY_DECIMALS,
    RENORMALISED_REST,
    SECOND_TEAM_PROBABILITY,
    WITHOUT_LIST,
    YES_PROBABILITY,
)
from grjev.metrics import NONE_NAMES, entropy, top_gap
from grjev.runs import ListAnswer, Row, offered_labels


class Kind(StrEnum):
    """What the lists of some answers hold: one correct option each, several, only correct options, or none."""

    ONE = "one"
    SEVERAL = "several"
    ALL = "all"
    NONE = "none"


@dataclass(frozen=True)
class Parted:
    """One answer with the probabilities of its correct options and of its distractors, each from the highest down.

    `hit` says whether the prediction, the field `choice` of the answer, is a correct option.
    """

    answer: ListAnswer
    correct: tuple[float, ...]
    distractors: tuple[float, ...]
    hit: bool


@dataclass(frozen=True)
class Distribution:
    """The figures of some answers. Confidence is the highest probability of an answer.

    `accuracy` is the share of the answers whose prediction is a correct option, `overconfidence` the mean
    confidence minus it, and `ece` the expected calibration error. The three are None when every option is correct.
    `exact_match` is the share of the answers that the run scored as correct, for lists with several correct options.

    The figures below are means over `measured` answers: those with a correct option and a distractor, or every
    answer when there is none. `spread` is the highest probability of a correct option minus the lowest,
    `lowest_margin` the lowest of a correct option minus the highest of a distractor, and `highest_margin` the
    highest of a correct option minus the highest of a distractor. `ranked_correct` holds the mean probability of
    the correct options from the highest down, when every measured answer has the same number of them. A figure is
    None when the lists have no option that it needs. `every_correct_above` is the share of the measured answers
    whose correct options are all above SECOND_TEAM_PROBABILITY, for lists with several correct options.

    `by_position` is the mean probability at each position of the list and `predicted_at` the number of predictions
    there. They are None when the lists differ in length.
    """

    kind: Kind
    answers: int
    options: tuple[int, int]
    correct_options: tuple[int, int]
    accuracy: float | None
    exact_match: float | None
    confidence: float
    overconfidence: float | None
    ece: float | None
    entropy: float
    runner_up: float
    measured: int
    spread: float | None
    lowest_margin: float | None
    highest_margin: float | None
    ranked_correct: tuple[float, ...] | None
    highest_correct: float | None
    lowest_correct: float | None
    highest_distractor: float | None
    every_correct_above: float | None
    by_position: tuple[float, ...] | None
    predicted_at: tuple[int, ...] | None


@dataclass(frozen=True)
class YesFigures:
    """The yes/no answers of some examples: for the correct options and for the distractors, the number of answers,
    the mean probability of yes, and the number of answers at YES_PROBABILITY or more."""

    correct: int
    correct_mean: float | None
    correct_yes: int
    distractors: int
    distractor_mean: float | None
    distractor_yes: int


def rounded(row: Row) -> Row:
    """Return the row with every probability rounded to PROBABILITY_DECIMALS decimals."""
    answers = {
        name: answer.model_copy(
            update={"probabilities": {k: round(v, PROBABILITY_DECIMALS) for k, v in answer.probabilities.items()}}
        )
        for name, answer in row.answers.items()
    }
    return row.model_copy(update={"answers": answers})


def correct_names(row: Row, answer: ListAnswer) -> list[str]:
    """Return the correct options of a list: the labels that it holds, or its "None" candidate when it holds none."""
    held = offered_labels(row.labels, answer.probabilities)
    return held or [name for name in answer.candidates if name in NONE_NAMES]


def parted(row: Row, answer: ListAnswer) -> Parted:
    """Return the answer with its probabilities parted into those of correct options and those of distractors."""
    names = set(correct_names(row, answer))
    correct = sorted((answer.probabilities[name] for name in answer.candidates if name in names), reverse=True)
    others = sorted((answer.probabilities[name] for name in answer.candidates if name not in names), reverse=True)
    return Parted(answer, tuple(correct), tuple(others), answer.choice in names)


def kind_of(parts: Sequence[Parted]) -> Kind:
    """Return what the lists of the answers hold."""
    numbers = {len(part.correct) for part in parts}
    if numbers == {0}:
        return Kind.NONE
    if not any(part.distractors for part in parts):
        return Kind.ALL
    return Kind.ONE if numbers == {1} else Kind.SEVERAL


def ece(pairs: Sequence[tuple[float, bool]], bins: int = ECE_BINS) -> float:
    """Return the expected calibration error of pairs of a confidence and whether the prediction is correct.

    The pairs are put in bins of equal width by confidence. A bin holds the confidences above its lower edge up to
    its upper edge, and the first bin also holds 0. The error is the distance between the mean confidence of a bin
    and its accuracy, averaged over the bins with the number of pairs as weight.
    """
    total = 0.0
    for index in range(bins):
        low, high = index / bins, (index + 1) / bins
        held = [(value, hit) for value, hit in pairs if low < value <= high or (index == 0 and value == 0)]
        if held:
            accuracy = statistics.fmean(hit for _, hit in held)
            total += len(held) / len(pairs) * abs(accuracy - statistics.fmean(value for value, _ in held))
    return total


def positions(answers: Sequence[ListAnswer]) -> tuple[tuple[float, ...], tuple[int, ...]] | None:
    """Return the mean probability at each position and the number of predictions there, from the first position.

    Return None when the lists of the answers differ in length.
    """
    if len({len(answer.candidates) for answer in answers}) > 1:
        return None
    predicted = Counter(answer.candidates.index(answer.choice) for answer in answers)
    by_place = zip(*([answer.probabilities[name] for name in answer.candidates] for answer in answers), strict=True)
    means = tuple(statistics.fmean(values) for values in by_place)
    return means, tuple(predicted[place] for place in range(len(means)))


def span(values: Sequence[int]) -> tuple[int, int]:
    """Return the lowest and the highest of the values."""
    return min(values), max(values)


def distribution(answers: Sequence[tuple[Row, ListAnswer]]) -> Distribution:
    """Return the figures of the answers, each given with the example that it answers."""
    parts = [parted(row, answer) for row, answer in answers]
    kind = kind_of(parts)
    confidence = statistics.fmean(max(part.answer.probabilities.values()) for part in parts)
    accuracy = None if kind is Kind.ALL else statistics.fmean(part.hit for part in parts)
    pairs = [(max(part.answer.probabilities.values()), part.hit) for part in parts]
    measured = [part for part in parts if part.correct and part.distractors] or parts
    held, margins = kind is not Kind.NONE, kind in (Kind.ONE, Kind.SEVERAL)
    same_number = len({len(part.correct) for part in measured}) == 1
    placed = positions([part.answer for part in parts])
    mean = statistics.fmean
    return Distribution(
        kind=kind,
        answers=len(parts),
        options=span([len(part.answer.candidates) for part in parts]),
        correct_options=span([len(part.correct) for part in parts]),
        accuracy=accuracy,
        exact_match=mean(part.answer.correct for part in parts) if kind is Kind.SEVERAL else None,
        confidence=confidence,
        overconfidence=None if accuracy is None else confidence - accuracy,
        ece=None if accuracy is None else ece(pairs),
        entropy=mean(entropy(part.answer) for part in parts),
        runner_up=mean(top_gap(part.answer) for part in parts),
        measured=len(measured),
        spread=mean(part.correct[0] - part.correct[-1] for part in measured) if held else None,
        lowest_margin=mean(part.correct[-1] - part.distractors[0] for part in measured) if margins else None,
        highest_margin=mean(part.correct[0] - part.distractors[0] for part in measured) if margins else None,
        ranked_correct=(
            tuple(mean(values) for values in zip(*(part.correct for part in measured), strict=True))
            if held and same_number
            else None
        ),
        highest_correct=mean(part.correct[0] for part in measured) if held else None,
        lowest_correct=mean(part.correct[-1] for part in measured) if held else None,
        highest_distractor=mean(part.distractors[0] for part in measured) if kind is not Kind.ALL else None,
        every_correct_above=(
            mean(part.correct[-1] > SECOND_TEAM_PROBABILITY for part in measured) if kind is Kind.SEVERAL else None
        ),
        by_position=placed[0] if placed else None,
        predicted_at=placed[1] if placed else None,
    )


@dataclass(frozen=True)
class Removal:
    """The second correct option of the examples of a run, before and after the top correct option is removed.

    `before` and `after` are its mean probabilities in the full list and in the list without the top correct
    option, over `examples` examples. `renormalised` is the mean of its probability in the full list divided by the
    probability that the full list gives to the options other than the top correct one. It is the value that the
    full list gives when the probability of the removed option is shared out in proportion. It is computed over the
    `kept` examples in which those options hold RENORMALISED_REST or more, and `after_kept` is the mean after the
    removal over the same examples. Both are None when there is no such example.
    """

    before: float
    after: float
    examples: int
    renormalised: float | None
    after_kept: float | None
    kept: int


def second_after_removal(rows: Sequence[Row], full: str = FULL_LIST) -> Removal | None:
    """Return the figures of the second correct option before and after the top one is removed.

    The second correct option of an example is the correct option with the second-highest probability in the list
    named `full`. The list without the correct option that has the highest probability there gives the value after.
    The examples are those with several correct options and an answer to both lists. Return None when there is none.
    """
    before, after, shares, after_kept = [], [], [], []
    for row in rows:
        answer = row.answers.get(full)
        if answer is None or len(row.labels) < 2:
            continue
        ranked = sorted(row.labels, key=lambda label: answer.probabilities[label], reverse=True)
        removed = row.answers.get(f"{WITHOUT_LIST}_{row.labels.index(ranked[0]) + 1}")
        if removed is None:
            continue
        top, second = answer.probabilities[ranked[0]], answer.probabilities[ranked[1]]
        before.append(second)
        after.append(removed.probabilities[ranked[1]])
        if 1 - top >= RENORMALISED_REST:
            shares.append(second / (1 - top))
            after_kept.append(after[-1])
    if not before:
        return None
    renormalised = statistics.fmean(shares) if shares else None
    kept = statistics.fmean(after_kept) if after_kept else None
    return Removal(statistics.fmean(before), statistics.fmean(after), len(before), renormalised, kept, len(shares))


def yes_figures(rows: Sequence[Row]) -> YesFigures:
    """Return the figures of the yes/no answers of the examples, for the correct options and for the distractors."""
    correct = [value for row in rows for name, value in row.yes.items() if name in row.labels]
    others = [value for row in rows for name, value in row.yes.items() if name not in row.labels]
    return YesFigures(
        correct=len(correct),
        correct_mean=statistics.fmean(correct) if correct else None,
        correct_yes=sum(value >= YES_PROBABILITY for value in correct),
        distractors=len(others),
        distractor_mean=statistics.fmean(others) if others else None,
        distractor_yes=sum(value >= YES_PROBABILITY for value in others),
    )
