"""Figures of a run, computed from its rows: CSR with a bootstrap interval over the examples, and counts of answers."""

import random
import statistics
from collections import Counter
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from itertools import pairwise
from math import log2

from grjev.constants import (
    BOOTSTRAP_RESAMPLES,
    COUNTED_WORDINGS,
    INTERVAL_TAIL,
    NONE_NAME,
    PLACEMENTS,
    RELEASED_ORDER,
    SEPARATED_PLACEMENTS,
    UNCOUNTED_WORDINGS,
)
from grjev.runs import ListAnswer, Row, top_tools

# The name of a group of tool lists -> the names of the lists whose answers it pools.
type Groups = dict[str, list[str]]


@dataclass(frozen=True)
class Figures:
    """The figures of the answers to some tool lists. `csr`, `low`, `high` and `zero_probabilities` are percentages.

    `entropy` is the mean entropy of an answer's probabilities in bits, and `gap` the mean of its highest probability
    minus its second-highest. `second_wrong`, `second_tied` and `top_wrong` count the answers that miss the correct
    tools of a query with several correct tools, each answer once. `highest_correct`, `lowest_correct` and
    `correct_together` are means over the answers to queries with several correct tools: the probability of the
    correct tool with the highest probability, of the one with the lowest, and of all the correct tools summed. They
    are None when no query has several correct tools.
    """

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
    entropy: float
    gap: float
    highest_correct: float | None
    lowest_correct: float | None
    correct_together: float | None
    one_choice: int
    all_correct: int
    none_correct: int
    second_wrong: int
    second_tied: int
    top_wrong: int


def interval(values: Sequence[float], seed: int) -> tuple[float, float]:
    """Return the 95% bootstrap interval of the mean of the values, which hold one value per example."""
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(values, k=len(values))) for _ in range(BOOTSTRAP_RESAMPLES))
    tail = round(BOOTSTRAP_RESAMPLES * INTERVAL_TAIL)
    return means[tail], means[-tail]


def entropy(answer: ListAnswer) -> float:
    """Return the entropy of the probabilities of an answer in bits: 0 for one tool at 1.00, 1 for two tools at 0.50."""
    return sum(-value * log2(value) for value in answer.probabilities.values() if value > 0)


def top_gap(answer: ListAnswer) -> float:
    """Return the highest probability of an answer minus its second-highest."""
    first, second = sorted(answer.probabilities.values(), reverse=True)[:2]
    return first - second


def having(rows: Sequence[Row], lists: Collection[str]) -> list[Row]:
    """Return the examples that have an answer for every named tool list."""
    return [row for row in rows if all(name in row.answers for name in lists)]


def correct_shares(rows: Sequence[Row], lists: Collection[str]) -> list[float]:
    """Return, for each example, the share of the named tool lists that Jev answered correctly."""
    return [statistics.fmean(row.answers[name].correct for name in lists) for row in rows]


def miss_of(row: Row, answer: ListAnswer) -> str | None:
    """Return how an answer misses the correct tools of a query with several correct tools, or None when it does not.

    `top_wrong`: no tool with the highest probability is correct. `second_tied`: the top tool is correct, and a tie
    leaves the next place open. `second_wrong`: the top tool is correct, and a wrong tool takes the next place.
    """
    if len(row.labels) < 2 or answer.correct:
        return None
    highest = max(answer.probabilities.values())
    if not any(answer.probabilities[name] == highest for name in row.labels):
        return "top_wrong"
    return "second_tied" if top_tools(answer.probabilities, len(row.labels)) is None else "second_wrong"


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
    misses = Counter(miss_of(row, answer) for row, answer in answers)
    spreads = [
        sorted(answer.probabilities[tool] for tool in row.labels) for row, answer in answers if len(row.labels) > 1
    ]
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
        entropy=statistics.fmean(entropy(answer) for _, answer in answers),
        gap=statistics.fmean(top_gap(answer) for _, answer in answers),
        highest_correct=statistics.fmean(spread[-1] for spread in spreads) if spreads else None,
        lowest_correct=statistics.fmean(spread[0] for spread in spreads) if spreads else None,
        correct_together=statistics.fmean(map(sum, spreads)) if spreads else None,
        one_choice=sum(len({row.answers[name].choice for name in lists}) == 1 for row in rows),
        all_correct=sum(share == 1 for share in shares),
        none_correct=sum(share == 0 for share in shares),
        second_wrong=misses["second_wrong"],
        second_tied=misses["second_tied"],
        top_wrong=misses["top_wrong"],
    )


def ranked_means(rows: Sequence[Row], lists: Sequence[str]) -> tuple[float, ...]:
    """Return the mean probability of the highest tool of each answer to the named lists, then of the second-highest.

    The means go on down to the lowest tool of the shortest list.
    """
    ranked = [sorted(row.answers[name].probabilities.values(), reverse=True) for row in rows for name in lists]
    return tuple(statistics.fmean(values) for values in zip(*ranked, strict=False))


def placed(rows: Sequence[Row], lists: Sequence[str], base: str | None = None) -> tuple[list[float], list[int]]:
    """Return the mean probability at each place of the named lists, and the number of answers that select each place.

    The place of a tool is its place in the list that is answered. With `base` it is its place in the example's list
    of that name, which follows one tool through several orders of a list.
    """
    values: dict[int, list[float]] = {}
    selected: Counter[int] = Counter()
    for row in rows:
        for name in lists:
            order = row.answers[base or name].candidates
            for tool, value in row.answers[name].probabilities.items():
                values.setdefault(order.index(tool), []).append(value)
            selected[order.index(row.answers[name].choice)] += 1
    return [statistics.fmean(values[place]) for place in sorted(values)], [selected[place] for place in sorted(values)]


def most_selected(rows: Sequence[Row], lists: Sequence[str]) -> dict[int, int]:
    """Return the number of examples by the number of the named lists that select the example's most selected tool."""
    counts = Counter(Counter(row.answers[name].choice for name in lists).most_common(1)[0][1] for row in rows)
    return dict(sorted(counts.items()))


@dataclass(frozen=True)
class Repeated:
    """Two answers to one tool list compared over the examples, such as the answers of two runs.

    `same_choice` counts the examples with the same selected tool in both answers, and `identical` those with the same
    probability for every tool. `largest_change` is the largest change of one tool's probability. `overtaken` is, over
    the examples whose selected tool differs, the largest lead that the first answer gives its selected tool over the
    tool that the second answer selects. It is 0 when no selected tool differs.
    """

    answers: int
    same_choice: int
    identical: int
    largest_change: float
    overtaken: float


def repeated(first: Sequence[Row], second: Sequence[Row], name: str, other: str) -> Repeated:
    """Compare each example's answer to the list `name` in the first rows with its answer to `other` in the second."""
    later = {row.id: row.answers[other] for row in second if other in row.answers}
    pairs = [(row.answers[name], later[row.id]) for row in first if name in row.answers]
    leads = [
        one.probabilities[one.choice] - one.probabilities[two.choice] for one, two in pairs if one.choice != two.choice
    ]
    changes = [abs(value - two.probabilities[tool]) for one, two in pairs for tool, value in one.probabilities.items()]
    return Repeated(
        answers=len(pairs),
        same_choice=len(pairs) - len(leads),
        identical=sum(one.probabilities == two.probabilities for one, two in pairs),
        largest_change=max(changes),
        overtaken=max(leads, default=0.0),
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
    length run pools the placements of each list length, and the list lengths of each placement. Lists that are
    named by the wording of their instruction are not pooled.
    """
    placements = list(PLACEMENTS)
    pooled = {
        f"{len(placements)} placements": placements,
        "adjacent": [f"adjacent_{name}" for name in placements],
        "separated": [f"separated_{early}_{late}" for early, late in SEPARATED_PLACEMENTS],
    }
    pooled |= {f"{length} tools": [f"{length}_{name}" for name in placements] for length in lengths}
    pooled |= {f"{name}, every length": [f"{length}_{name}" for length in lengths] for name in placements}
    present = {group: lists for group, lists in pooled.items() if lists and set(lists) <= set(names)}
    wordings = {*COUNTED_WORDINGS, *UNCOUNTED_WORDINGS}
    worded = any(name.rpartition("_")[2] in wordings for name in names)
    every = {"every list": list(names)} if len(names) > 1 and not worded else {}
    return {name: [name] for name in names} | present | every


def compared_groups(groups: Groups, lengths: Sequence[int]) -> dict[str, tuple[str, str]]:
    """Return the pairs of groups whose CSR is compared, by name of the comparison: the first group minus the second.

    A wording run compares each wording with the one before it. A growth run compares, for each wording, the list
    before it is grown with the longest list.
    """
    placed = f"{len(PLACEMENTS)} placements"
    pairs = {
        "first minus last": ("first", "last"),
        f"{RELEASED_ORDER} minus {placed}": (RELEASED_ORDER, placed),
        "adjacent minus separated": ("adjacent", "separated"),
        "first minus last, every length": ("first, every length", "last, every length"),
    }
    if lengths:
        shortest, longest = f"{lengths[0]} tools", f"{lengths[-1]} tools"
        pairs[f"{shortest} minus {longest}"] = (shortest, longest)
    wordings = [*COUNTED_WORDINGS, *UNCOUNTED_WORDINGS]
    pairs |= {f"{later} minus {earlier}": (later, earlier) for earlier, later in pairwise(wordings)}
    by_wording: dict[str, list[str]] = {}
    for name in groups:
        size, _, wording = name.rpartition("_")
        if size and wording in wordings:
            by_wording.setdefault(wording, []).append(name)
    pairs |= {f"{own[0]} minus {own[-1]}": (own[0], own[-1]) for own in by_wording.values() if len(own) > 1}
    return {name: pair for name, pair in pairs.items() if set(pair) <= set(groups)}


def row_groups(rows: Sequence[Row]) -> dict[str, list[Row]]:
    """Return the examples that have figures together, by name: those of each test file.

    When every test file has the same tool lists, as in a length run or a wording run, all the examples come first
    as one more group. When the number of correct tools differs within a test file, the examples with each number
    of correct tools are groups too.
    """
    by_file: dict[str, list[Row]] = {}
    by_number: dict[int, list[Row]] = {}
    for row in rows:
        by_file.setdefault(row.test_file, []).append(row)
        by_number.setdefault(len(row.labels), []).append(row)
    same_lists = all(set(list_names(own)) == set(list_names(rows)) for own in by_file.values())
    mixed = any(len({len(row.labels) for row in own}) > 1 for own in by_file.values())
    every = {"every test file": list(rows)} if same_lists and len(by_file) > 1 else {}
    numbers = {f"{number} correct tool{'' if number == 1 else 's'}": by_number[number] for number in sorted(by_number)}
    return every | by_file | (numbers if mixed else {})
