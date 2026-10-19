"""The choices that a probability threshold selects, on examples with two or more correct choices.

A threshold t selects the choices whose probability is at or above t. The list form takes the probabilities of one
list of choices, which sum to 1. The yes/no form takes the probability of yes of a separate question per choice.
Both forms are read on the same examples.
"""

from collections.abc import Callable, Sequence
from pathlib import Path

import matplotlib
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import StrMethodFormatter

from grjev.constants import (
    MODEL_COLORS,
    MODEL_TITLES,
    PROBABILITY_DECIMALS,
    REPO_ROOT,
    TABLES_DIR,
    THRESHOLD_MAJOR_TICKS,
    THRESHOLD_MINOR_TICKS,
    THRESHOLD_PAGE_SIZE,
    THRESHOLD_PAPER_SIZE,
    THRESHOLD_STEPS,
    THRESHOLDS_TABLED,
    UNIFORM_DEFINITION,
)
from grjev.runs import Row
from grjev.tables import read_spec, selected

# The probability and whether the choice is correct, for each choice of one example.
Choices = list[tuple[float, bool]]
FORMS = (("list", "-"), ("yes/no", "--"))
# The measures whose best value over the thresholds the table gives. Precision and recall reach 1 at an end.
BEST_SHOWN = ("Exact set accuracy", "F1")
# The measures whose charts mark the best value of each curve.
BEST_MARKED = ("Exact set accuracy",)


def choices(probabilities: dict[str, float], labels: Sequence[str]) -> Choices:
    """Return the rounded probability of each choice and whether it is a label."""
    return [(round(value, PROBABILITY_DECIMALS), name in labels) for name, value in probabilities.items()]


def paired(lists: Sequence[Row], name: str, asked: Sequence[Row]) -> tuple[list[Choices], list[Choices]]:
    """Return the choices of the list of that name and of the yes/no questions, for the same examples.

    An example counts when it has two or more labels, its list was answered and holds a distractor, and every one
    of its yes/no questions was answered. The yes/no questions must be about the options of the list.
    """
    yes = {row.id: row for row in asked if len(row.labels) > 1 and not row.refused}
    kept = [
        row
        for row in lists
        if len(row.labels) > 1
        and name in row.answers
        and len(row.answers[name].candidates) > len(row.labels)
        and row.id in yes
    ]
    for row in kept:
        if set(yes[row.id].yes) != set(row.answers[name].candidates):
            raise ValueError(f"the yes/no questions of {row.id} are not about the options of its list")
    listed = [choices(row.answers[name].probabilities, row.labels) for row in kept]
    return listed, [choices(yes[row.id].yes, row.labels) for row in kept]


def exact(found: Sequence[Choices], t: float) -> float:
    """Return the share of examples with every correct choice at or above t and every distractor below it."""
    return sum(all((value >= t) == hit for value, hit in example) for example in found) / len(found)


def counts(found: Sequence[Choices], t: float) -> tuple[int, int, int]:
    """Return the choices at or above t, the correct ones among them, and all correct choices."""
    pooled = [pair for example in found for pair in example]
    chosen = [hit for value, hit in pooled if value >= t]
    return len(chosen), sum(chosen), sum(hit for _, hit in pooled)


def precision(found: Sequence[Choices], t: float) -> float:
    """Return the share of the choices at or above t that are correct, over all examples, or nan without one."""
    chosen, right, _ = counts(found, t)
    return right / chosen if chosen else float("nan")


def recall(found: Sequence[Choices], t: float) -> float:
    """Return the share of all correct choices that are at or above t."""
    _, right, correct = counts(found, t)
    return right / correct


def other_recall(found: Sequence[Choices], t: float) -> float:
    """Return the share of the correct choices other than the highest one of each example that are at or above t.

    With one correct choice selected per example, recall over all correct choices is the number of examples over
    the number of correct choices, 0.50 when each example has two. This measure leaves that choice out.
    """
    rest = [sorted((value for value, hit in example if hit), reverse=True)[1:] for example in found]
    return sum(value >= t for values in rest for value in values) / sum(len(values) for values in rest)


def f1(found: Sequence[Choices], t: float) -> float:
    """Return the F1 of the precision and recall at t, and 0 when no correct choice is at or above t."""
    chosen, right, correct = counts(found, t)
    return 2 * right / (chosen + correct) if right else 0.0


# Name in the table -> the label of the vertical axis and the measure.
MEASURES: dict[str, tuple[str, Callable[[Sequence[Choices], float], float]]] = {
    "Exact set accuracy": ("Exact set accuracy", exact),
    "Precision": ("Precision: choices at or above t\nthat are correct", precision),
    "Recall": ("Recall: correct choices\nat or above t", recall),
    "Recall of the other correct choices": (
        "Recall of the correct choices\nother than the highest one",
        other_recall,
    ),
    "F1": ("F1 of that precision\nand recall", f1),
}


def thresholds() -> list[float]:
    """Return the thresholds of the charts."""
    return [step / THRESHOLD_STEPS for step in range(THRESHOLD_STEPS + 1)]


def read_pairs(
    runs: dict[str, tuple[str, str]], yes_runs: dict[str, str], root: Path = REPO_ROOT
) -> dict[tuple[str, str], tuple[list[Choices], list[Choices]]]:
    """Return the choices of the list and of the yes/no questions for each dataset and model.

    `runs` maps a dataset to the label of its list run in the definition UNIFORM_DEFINITION and the name of the list,
    and `yes_runs` to the label of its yes/no run.
    """
    spec = read_spec(TABLES_DIR / f"{UNIFORM_DEFINITION}.json")
    rows = {row.label: row for row in spec.rows}
    found = {}
    for dataset, (label, name) in runs.items():
        for model in spec.models:
            lists = selected(rows[label], model, root).rows
            found[(dataset, model)] = paired(lists, name, selected(rows[yes_runs[dataset]], model, root).rows)
    return found


def chart(
    found: dict[tuple[str, str], tuple[list[Choices], list[Choices]]],
    path: Path,
    names: Sequence[str] = tuple(MEASURES),
    paper: bool = False,
) -> None:
    """Draw the named measures against the threshold, one row per measure and one column per dataset.

    A chart for `docs/` has a title and its legend in the first panel. A chart for the paper has the width of the
    two columns of the paper, its legend under the panels and no title, since its caption says what it shows. The
    format follows the suffix of the path, with the fonts embedded as TrueType in a PDF.
    """
    datasets = list(dict.fromkeys(dataset for dataset, _ in found))
    steps = thresholds()
    width, height = THRESHOLD_PAPER_SIZE if paper else THRESHOLD_PAGE_SIZE
    with matplotlib.rc_context({"font.size": 7 if paper else 10, "pdf.fonttype": 42}):
        figure = Figure(figsize=(width, height * len(names) + (0.5 if paper else 0)))
        axes = figure.subplots(len(names), len(datasets), sharex=True, sharey=True, squeeze=False)
        for (dataset, model), pairs in found.items():
            for (form, style), forms in zip(FORMS, pairs, strict=True):
                line = {"color": MODEL_COLORS[model], "linestyle": style, "linewidth": 1.2 if paper else 1.6}
                for row, name in enumerate(names):
                    axis = axes[row][datasets.index(dataset)]
                    values = [MEASURES[name][1](forms, t) for t in steps]
                    # The measure is read at the thresholds only, so each value holds until the next threshold.
                    axis.plot(steps, values, label=f"{MODEL_TITLES[model]}, {form}", drawstyle="steps-post", **line)
                    if name in BEST_MARKED:
                        mark_best(axis, forms, MEASURES[name][1], MODEL_COLORS[model], filled=form == FORMS[0][0])
        for column, dataset in enumerate(datasets):
            sizes = [len(pairs[0]) for (own, _), pairs in found.items() if own == dataset]
            span = f"{min(sizes):,}" if min(sizes) == max(sizes) else f"{min(sizes):,} to {max(sizes):,}"
            axes[0][column].set_title(f"{dataset} ({span} examples)")
        for row, name in enumerate(names):
            axes[row][0].set_ylabel(MEASURES[name][0])
        for axis in axes.flat:
            set_ticks(axis)
            axis.grid(alpha=0.3)
            axis.set_ylim(0, 1.02)
        for axis in axes[-1]:
            axis.set_xlabel("Probability threshold t")
        if paper:
            figure.legend(*axes[0][0].get_legend_handles_labels(), loc="lower center", ncol=3, frameon=False)
            figure.tight_layout(rect=(0, 0.16 / len(names), 1, 1))
        else:
            axes[0][-1].legend(fontsize=8, loc="upper right")
            figure.suptitle(
                "Choices selected by a probability threshold t, on examples with 2 or more correct choices:\n"
                "one list (solid) against a yes/no question per choice (dashed)"
            )
            figure.tight_layout()
        figure.savefig(path, dpi=130)


def set_ticks(axis: Axes) -> None:
    """Put the ticks of THRESHOLD_MAJOR_TICKS, labelled with one decimal, and of THRESHOLD_MINOR_TICKS on both axes."""
    for ticked in (axis.xaxis, axis.yaxis):
        ticked.set_ticks(THRESHOLD_MAJOR_TICKS)
        ticked.set_ticks(THRESHOLD_MINOR_TICKS, minor=True)
        ticked.set_major_formatter(StrMethodFormatter("{x:.1f}"))


def mark_best(
    axis: Axes, found: Sequence[Choices], measure: Callable[[Sequence[Choices], float], float], color: str, filled: bool
) -> None:
    """Mark the highest value of a measure at the lowest threshold that reaches it, filled or hollow."""
    t, value = top(found, measure)
    face = color if filled else "white"
    axis.plot(t, value, marker="o", markersize=4, color=color, markerfacecolor=face, linestyle="none", zorder=3)


def top(found: Sequence[Choices], measure: Callable[[Sequence[Choices], float], float]) -> tuple[float, float]:
    """Return the lowest threshold that reaches the highest value of a measure over the thresholds, and that value."""
    values = {t: measure(found, t) for t in thresholds()}
    highest = max(values.values())
    return next((t, value) for t, value in values.items() if value == highest)


def best(found: Sequence[Choices], measure: Callable[[Sequence[Choices], float], float]) -> str:
    """Return the highest value of a measure over the thresholds, with the lowest threshold that reaches it."""
    t, value = top(found, measure)
    return f"{value:.2f} ({t:.2f})"


def paper_table(found: dict[tuple[str, str], tuple[list[Choices], list[Choices]]]) -> str:
    """Return a LaTeX `tabular` of the best exact set accuracy over the thresholds, with the models as rows and a list
    and a yes/no column for each dataset."""
    datasets = list(dict.fromkeys(dataset for dataset, _ in found))
    models = list(dict.fromkeys(model for _, model in found))
    names = " & ".join(rf"\multicolumn{{2}}{{c}}{{{dataset}}}" for dataset in datasets)
    rules = " ".join(rf"\cmidrule(lr){{{2 * place + 2}-{2 * place + 3}}}" for place in range(len(datasets)))
    lines = [rf"\begin{{tabular}}{{l{'rr' * len(datasets)}}}", r"\toprule", f" & {names} \\\\", rules]
    lines += ["Model" + " & List & Yes/no" * len(datasets) + r" \\", r"\midrule"]
    for model in models:
        values = [
            max(exact(forms, t) for t in thresholds()) for dataset in datasets for forms in found[(dataset, model)]
        ]
        lines.append(MODEL_TITLES[model] + "".join(f" & {value:.2f}" for value in values) + r" \\")
    return "\n".join([*lines, r"\bottomrule", r"\end{tabular}"]) + "\n"


def table(found: dict[tuple[str, str], tuple[list[Choices], list[Choices]]]) -> str:
    """Return a Markdown table of each measure at the thresholds of THRESHOLDS_TABLED, and the best value of the
    measures of BEST_SHOWN."""
    header = ["Dataset", "Model", "Form", "Examples", "Measure"]
    header += [f"t = {t:g}" for t in THRESHOLDS_TABLED] + ["Best value (t)"]
    lines = [f"| {' | '.join(header)} |", "|" + "---|" * 5 + "---:|" * (len(THRESHOLDS_TABLED) + 1)]
    for (dataset, model), pairs in found.items():
        for (form, _), forms in zip(FORMS, pairs, strict=True):
            for name, (_, measure) in MEASURES.items():
                cells = [f"{measure(forms, t):.2f}" for t in THRESHOLDS_TABLED]
                cells.append(best(forms, measure) if name in BEST_SHOWN else "")
                lines.append(
                    f"| {dataset} | {MODEL_TITLES[model]} | {form} | {len(forms):,} | {name} | {' | '.join(cells)} |"
                )
    return "\n".join(lines) + "\n"
