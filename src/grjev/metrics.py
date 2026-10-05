"""Figures of a run, computed from its rows: CSR with a bootstrap interval over the examples, and counts of answers."""

import random
import statistics
from collections.abc import Collection, Sequence
from dataclasses import dataclass

from grjev.constants import (
    BOOTSTRAP_RESAMPLES,
    INTERVAL_TAIL,
    NONE_NAME,
    PLACEMENTS,
    RELEASED_ORDER,
    SEPARATED_PLACEMENTS,
)
from grjev.runs import Row, top_tools

# The name of a group of tool lists -> the names of the lists whose answers it pools.
type Groups = dict[str, list[str]]


@dataclass(frozen=True)
class Figures:
    """The figures of the answers to some tool lists. `csr`, `low`, `high` and `zero_probabilities` are percentages."""

    examples: int
    answers: int
    correct: int
    csr: float
    low: float
    high: float
    none: int
    confident: int
    confident_wrong: int
    zero_probabilities: float
    one_choice: int
    all_correct: int
    none_correct: int
    tied: int
    choice_correct: int


def interval(values: Sequence[float], seed: int) -> tuple[float, float]:
    """Return the 95% bootstrap interval of the mean of the values, which hold one value per example."""
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(values, k=len(values))) for _ in range(BOOTSTRAP_RESAMPLES))
    tail = round(BOOTSTRAP_RESAMPLES * INTERVAL_TAIL)
    return means[tail], means[-tail]


def having(rows: Sequence[Row], lists: Collection[str]) -> list[Row]:
    """Return the examples that have an answer for every named tool list."""
    return [row for row in rows if all(name in row.answers for name in lists)]


def correct_shares(rows: Sequence[Row], lists: Collection[str]) -> list[float]:
    """Return, for each example, the share of the named tool lists that Jev answered correctly."""
    return [statistics.fmean(row.answers[name].correct for name in lists) for row in rows]


def figures(rows: Sequence[Row], lists: Sequence[str], seed: int, confident_from: float) -> Figures:
    """Return the figures of the named tool lists, over the examples that have all of them.

    An answer is confident when its highest probability is at least `confident_from`. The interval resamples the
    examples, each with its share of correct lists.
    """
    rows = having(rows, lists)
    shares = correct_shares(rows, lists)
    low, high = interval(shares, seed)
    answers = [(row, row.answers[name]) for row in rows for name in lists]
    confident = [answer for _, answer in answers if max(answer.probabilities.values()) >= confident_from]
    probabilities = [value for _, answer in answers for value in answer.probabilities.values()]
    return Figures(
        examples=len(rows),
        answers=len(answers),
        correct=sum(answer.correct for _, answer in answers),
        csr=100 * statistics.fmean(shares),
        low=100 * low,
        high=100 * high,
        none=sum(answer.choice == NONE_NAME for _, answer in answers),
        confident=len(confident),
        confident_wrong=sum(not answer.correct for answer in confident),
        zero_probabilities=100 * statistics.fmean(value == 0 for value in probabilities),
        one_choice=sum(len({row.answers[name].choice for name in lists}) == 1 for row in rows),
        all_correct=sum(share == 1 for share in shares),
        none_correct=sum(share == 0 for share in shares),
        tied=sum(
            len(row.labels) > 1 and top_tools(answer.probabilities, len(row.labels)) is None for row, answer in answers
        ),
        choice_correct=sum(answer.choice in row.labels for row, answer in answers),
    )


def difference(
    rows: Sequence[Row], first: Sequence[str], second: Sequence[str], seed: int
) -> tuple[float, float, float]:
    """Return CSR on the first tool lists minus CSR on the second, in points, and its 95% bootstrap interval.

    The difference is taken within each example, and the interval resamples the examples.
    """
    rows = having(rows, [*first, *second])
    gaps = [one - other for one, other in zip(correct_shares(rows, first), correct_shares(rows, second), strict=True)]
    low, high = interval(gaps, seed)
    return 100 * statistics.fmean(gaps), 100 * low, 100 * high


def list_names(rows: Sequence[Row]) -> list[str]:
    """Return the names of the tool lists of the examples, each once, in the order of first appearance."""
    return list(dict.fromkeys(name for row in rows for name in row.answers))


def list_groups(names: Sequence[str], lengths: Sequence[int]) -> Groups:
    """Return the groups of tool lists that have figures: each list, then the groups that pool lists, then every list.

    A position run pools the placements of one correct tool, and the adjacent and the separated orders of two. A
    length run pools the placements of each list length, and the list lengths of each placement.
    """
    placements = list(PLACEMENTS)
    pooled = {
        f"{len(placements)} placements": placements,
        "adjacent": [f"adjacent_{name}" for name in placements],
        "separated": [f"separated_{early}_{late}" for early, late in SEPARATED_PLACEMENTS],
    }
    pooled |= {f"{length} tools": [f"{length}_{name}" for name in placements] for length in lengths}
    pooled |= {f"{name}, every length": [f"{length}_{name}" for length in lengths] for name in placements}
    present = {group: lists for group, lists in pooled.items() if set(lists) <= set(names)}
    every = {"every list": list(names)} if len(names) > 1 else {}
    return {name: [name] for name in names} | present | every


def compared_groups(groups: Groups, lengths: Sequence[int]) -> dict[str, tuple[str, str]]:
    """Return the pairs of groups whose CSR is compared, by name of the comparison: the first group minus the second."""
    placed = f"{len(PLACEMENTS)} placements"
    shortest, longest = f"{lengths[0]} tools", f"{lengths[-1]} tools"
    pairs = {
        "first minus last": ("first", "last"),
        f"{RELEASED_ORDER} minus {placed}": (RELEASED_ORDER, placed),
        "adjacent minus separated": ("adjacent", "separated"),
        f"{shortest} minus {longest}": (shortest, longest),
        "first minus last, every length": ("first, every length", "last, every length"),
    }
    return {name: pair for name, pair in pairs.items() if set(pair) <= set(groups)}


def row_groups(rows: Sequence[Row]) -> dict[str, list[Row]]:
    """Return the examples that have figures together, by name: those of each test file.

    When every example has the same tool lists, as in a length run, all the examples come first as one more group.
    """
    by_file: dict[str, list[Row]] = {}
    for row in rows:
        by_file.setdefault(row.test_file, []).append(row)
    same_lists = len({tuple(row.answers) for row in rows}) == 1
    return ({"every test file": list(rows)} if same_lists and len(by_file) > 1 else {}) | by_file
