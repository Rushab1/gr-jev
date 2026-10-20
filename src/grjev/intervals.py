"""95% bootstrap intervals of the main figures of the paper, over the examples.

Each figure is a sum over the examples divided by another sum over them, such as the gaps of the answers over the
number of answers. A resample draws the examples with replacement and keeps every answer of an example together.
"""

import random
from collections.abc import Sequence
from pathlib import Path

from grjev.constants import (
    BOOTSTRAP_RESAMPLES,
    BOOTSTRAP_SEED,
    COPIES_RUNS,
    INTERVAL_TAIL,
    MODEL_TITLES,
    REPO_ROOT,
    TABLES_DIR,
    THRESHOLD_YES_NO_RUNS,
    UNIFORM_DEFINITION,
    UNIFORM_RUNS,
)
from grjev.distribution import parted
from grjev.runs import ListAnswer, Row
from grjev.tables import RowSpec, answers_of, read_spec, selected
from grjev.thresholds import Choices, exact, read_pairs, top
from grjev.uniform import correct_below, ranked_correctly

# What one example adds to the sum above the line of a figure and to the sum below it.
Pair = tuple[float, float]
# The rows of the table for each dataset: the figure, its scale and its number of decimals.
FIGURES = (
    ("Gap", 100, 0),
    ("Ranked", 100, 0),
    (r"Below $1/n$", 100, 0),
    ("Gap of the copies", 100, 0),
    ("Exact set, list", 1, 2),
    ("Exact set, yes/no", 1, 2),
)


def ratio(pairs: Sequence[Pair]) -> float:
    """Return the sum of the first values of the pairs over the sum of the second values."""
    return sum(above for above, _ in pairs) / sum(below for _, below in pairs)


def ratio_interval(pairs: Sequence[Pair], seed: int = BOOTSTRAP_SEED) -> tuple[float, float]:
    """Return the 95% bootstrap interval of the ratio of the pairs, which hold one pair per example."""
    rng = random.Random(seed)
    ratios = sorted(ratio(rng.choices(pairs, k=len(pairs))) for _ in range(BOOTSTRAP_RESAMPLES))
    tail = round(BOOTSTRAP_RESAMPLES * INTERVAL_TAIL)
    return ratios[tail], ratios[-tail]


def gap_pairs(answers: Sequence[tuple[Row, ListAnswer]]) -> list[Pair]:
    """Return, for each example, the sum over its answers of the highest minus the lowest probability of a correct
    choice, and the number of those answers. As in `distribution`, an answer counts when its list holds a correct
    choice and a distractor, and every answer counts when no list holds both."""
    parts = [(row.id, parted(row, answer)) for row, answer in answers]
    measured = [(key, part) for key, part in parts if part.correct and part.distractors] or parts
    sums: dict[str, Pair] = {}
    for key, part in measured:
        above, below = sums.get(key, (0.0, 0.0))
        sums[key] = (above + part.correct[0] - part.correct[-1], below + 1)
    return list(sums.values())


def ranked_pairs(rows: Sequence[Row], name: str) -> tuple[list[Pair], list[Pair]]:
    """Return two pairs for each example that `uniform.counted` counts: whether its list of that name ranks every
    label above every distractor, over 1, and whether that list also has a label below 1/n, over whether it ranks."""
    answered = [
        (row.labels, row.answers[name])
        for row in rows
        if len(row.labels) > 1 and name in row.answers and len(row.answers[name].candidates) > len(row.labels)
    ]
    good = [ranked_correctly(labels, answer) for labels, answer in answered]
    low = [bool(correct_below(labels, answer)) for labels, answer in answered]
    return [(float(g), 1.0) for g in good], [(float(g and b), float(g)) for g, b in zip(good, low, strict=True)]


def exact_pairs(found: Sequence[Choices]) -> list[Pair]:
    """Return, for each example, whether its set is exact at the threshold with the highest exact set accuracy over
    all the examples. The threshold stays fixed, so the interval leaves out the choice of the threshold."""
    t, _ = top(found, exact)
    return [(exact([example], t), 1.0) for example in found]


def cell(pairs: Sequence[Pair], scale: int, decimals: int) -> str:
    """Return a figure and its interval, multiplied by the scale and with that number of decimals."""
    low, high = ratio_interval(pairs)
    value, low, high = (scale * number for number in (ratio(pairs), low, high))
    return f"{value:.{decimals}f} [{low:.{decimals}f}, {high:.{decimals}f}]"


def figure_cells(
    dataset: str,
    model: str,
    rows: dict[str, RowSpec],
    found: dict[tuple[str, str], tuple[list[Choices], list[Choices]]],
) -> list[str]:
    """Return the cells of FIGURES for one dataset and model."""
    label, name = UNIFORM_RUNS[dataset]
    lists = selected(rows[label], model)
    good, low = ranked_pairs(lists.rows, name)
    copies = list(answers_of(selected(rows[COPIES_RUNS[dataset]], model)).values())
    listed, asked = found[(dataset, model)]
    pairs = [gap_pairs(list(answers_of(lists).values())), good, low, gap_pairs(copies)]
    pairs += [exact_pairs(listed), exact_pairs(asked)]
    return [cell(own, scale, decimals) for own, (_, scale, decimals) in zip(pairs, FIGURES, strict=True)]


def paper_table(root: Path = REPO_ROOT) -> str:
    """Return a LaTeX `tabular` of FIGURES with their intervals, with a block of rows for each dataset of
    UNIFORM_RUNS and a column for each model."""
    spec = read_spec(TABLES_DIR / f"{UNIFORM_DEFINITION}.json")
    rows = {row.label: row for row in spec.rows}
    found = read_pairs(UNIFORM_RUNS, THRESHOLD_YES_NO_RUNS, root)
    width = len(spec.models) + 1
    header = "Figure & " + " & ".join(MODEL_TITLES[model] for model in spec.models) + r" \\"
    lines = [rf"\begin{{tabular}}{{l{'r' * len(spec.models)}}}", r"\toprule", header]
    for dataset in UNIFORM_RUNS:
        cells = {model: figure_cells(dataset, model, rows, found) for model in spec.models}
        lines += [r"\midrule", rf"\multicolumn{{{width}}}{{l}}{{\emph{{{dataset}}}}} \\"]
        for index, (figure, _, _) in enumerate(FIGURES):
            lines.append(figure + "".join(f" & {cells[model][index]}" for model in spec.models) + r" \\")
    return "\n".join([*lines, r"\bottomrule", r"\end{tabular}"]) + "\n"
