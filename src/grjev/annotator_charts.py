"""The two ChaosNLI charts, one column per test file.

The reliability chart puts the probability a model gives a label against the share of the 100 annotators who chose it,
with a second row for the difference from the diagonal. The gap chart puts the annotator gap between the two labels
with the most votes against the model gap on the same two labels, in one row. Both read the bins of grjev.annotators.
"""

from collections.abc import Callable, Sequence
from pathlib import Path

import matplotlib
from matplotlib.figure import Figure
from matplotlib.patches import Patch
from matplotlib.ticker import PercentFormatter

from grjev.annotators import Answer, Bin, gap_bins, reliability_bins
from grjev.bin_charts import bin_ticks, draw_shares, share_axis
from grjev.constants import (
    ANNOTATOR_BIN_EDGES,
    ANNOTATOR_GAP_PAGE_SIZE,
    ANNOTATOR_GAP_PAPER_SIZE,
    ANNOTATOR_PAGE_SIZE,
    ANNOTATOR_PAPER_SIZE,
    ANNOTATOR_TITLES,
    FIGURE_DPI,
    MODEL_COLORS,
    MODEL_TITLES,
)

RELIABILITY_LABELS = (
    "Probability the model gives a label",
    "Share of the 100 annotators\nwho chose the label",
    "Annotators' share minus the\nprobability (points)",
)
COLORS = {title: MODEL_COLORS[model] for model, title in MODEL_TITLES.items()}


def chart(
    found: dict[str, dict[str, list[Bin]]], labels: tuple[str, str, str], path: Path, paper: bool = False
) -> None:
    """Draw one column per test file with the bins above and their distance from the diagonal below."""
    files = list(found)
    width, heights = ANNOTATOR_PAPER_SIZE if paper else ANNOTATOR_PAGE_SIZE
    with matplotlib.rc_context({"font.size": 7 if paper else 10, "pdf.fonttype": 42}):
        figure = Figure(figsize=(width, sum(heights) + (0.7 if paper else 1.2)))
        axes = figure.subplots(
            2, len(files), sharex=True, sharey="row", squeeze=False, gridspec_kw={"height_ratios": heights}
        )
        behind = {
            axis: share_axis(axis, ANNOTATOR_BIN_EDGES, axis in axes[:, -1], axis is axes[0][-1]) for axis in axes.flat
        }
        models = list(next(iter(found.values())))
        for column, test_file in enumerate(files):
            top, bottom = axes[0][column], axes[1][column]
            for model, bins in found[test_file].items():
                style = {"color": COLORS[model], "linewidth": 1.2 if paper else 1.6, "markersize": 3 if paper else 4}
                top.plot([part.mean for part in bins], [part.observed for part in bins], "o-", label=model, **style)
                bottom.plot(
                    [part.mean for part in bins],
                    [100 * (part.observed - part.mean) for part in bins],
                    "o-",
                    **style,
                )
                spans = [(part.low, part.high) for part in bins]
                counts = [part.count for part in bins]
                for axis in (top, bottom):
                    draw_shares(behind[axis], spans, counts, COLORS[model], (models.index(model), len(models)))
            top.plot((0, 1), (0, 1), color="grey", linestyle=":", linewidth=1)
            top.set_title(ANNOTATOR_TITLES[test_file])
            top.set_ylim(0, 1.02)
            top.yaxis.set_major_formatter(PercentFormatter(1.0))
            bottom.axhline(0, color="grey", linestyle=":", linewidth=1)
            for axis in (top, bottom):
                axis.set_xlabel(labels[0])
                axis.tick_params(labelbottom=True, labelleft=True)
                axis.grid(alpha=0.3, axis="y")
                axis.set_xlim(0, 1)
                bin_ticks(axis, ANNOTATOR_BIN_EDGES)
        axes[0][0].set_ylabel(labels[1])
        axes[1][0].set_ylabel(labels[2])
        if paper:
            figure.legend(*axes[0][0].get_legend_handles_labels(), loc="lower center", ncol=3, frameon=False)
            figure.tight_layout(rect=(0, 0.08, 1, 1))
        else:
            axes[0][0].legend(fontsize=8, loc="upper left")
            figure.tight_layout()
        figure.savefig(path, dpi=FIGURE_DPI)


def bins_of(
    answers: dict[str, dict[str, list[Answer]]], read: Callable[[Sequence[Answer]], list[Bin]]
) -> dict[str, dict[str, list[Bin]]]:
    """Return the bins that `read` gives for every test file and model."""
    return {
        test_file: {model: read(held) for model, held in by_model.items()} for test_file, by_model in answers.items()
    }


def reliability_chart(answers: dict[str, dict[str, list[Answer]]], path: Path, paper: bool = False) -> None:
    """Draw the reliability chart of the probabilities against the shares of the annotators."""
    chart(bins_of(answers, reliability_bins), RELIABILITY_LABELS, path, paper)


def gap_chart(answers: dict[str, dict[str, list[Answer]]], path: Path, paper: bool = False) -> None:
    """Draw one panel per test file with the model gap against the annotator gap, over the share of the examples in
    each bin. Every answer to an example falls in the bin of its annotator gap, so one bar per bin serves the models."""
    found = bins_of(answers, gap_bins)
    width, height = ANNOTATOR_GAP_PAPER_SIZE if paper else ANNOTATOR_GAP_PAGE_SIZE
    style = {"linewidth": 1.2 if paper else 1.6, "markersize": 3 if paper else 4}
    with matplotlib.rc_context({"font.size": 7 if paper else 10, "pdf.fonttype": 42}):
        figure = Figure(figsize=(width, height + (0.4 if paper else 0.6)))
        axes = figure.subplots(1, len(found), sharex=True, sharey=True, squeeze=False)[0]
        for column, (axis, (test_file, by_model)) in enumerate(zip(axes, found.items(), strict=True)):
            if len({tuple(part.count for part in bins) for bins in by_model.values()}) > 1:
                raise ValueError(f"the models answered different lists of {test_file}")
            last = column == len(axes) - 1
            behind = share_axis(axis, ANNOTATOR_BIN_EDGES, last, False)
            bins = next(iter(by_model.values()))
            draw_shares(behind, [(part.low, part.high) for part in bins], [part.count for part in bins], "grey", (0, 1))
            for model, held in by_model.items():
                axis.plot(
                    [part.mean for part in held],
                    [part.observed for part in held],
                    "o-",
                    label=model,
                    color=COLORS[model],
                    **style,
                )
            axis.plot((0, 1), (0, 1), color="grey", linestyle=":", linewidth=1)
            examples = len({answer.example for answer in next(iter(answers[test_file].values()))})
            axis.set_title(f"{ANNOTATOR_TITLES[test_file]} ({examples:,} examples)")
            axis.set_xlabel("Annotator gap")
            axis.set_xlim(0, 1)
            axis.set_ylim(0, 1.02)
            axis.tick_params(labelleft=True)
            axis.grid(alpha=0.3, axis="y")
            bin_ticks(axis, ANNOTATOR_BIN_EDGES)
            if last:
                behind.set_ylabel("Proportion of examples (log scale)", color="grey")
        axes[0].set_ylabel("Model gap")
        handles, labels = axes[0].get_legend_handles_labels()
        figure.legend(
            [*handles, Patch(facecolor="grey", alpha=0.25, linewidth=0)],
            [*labels, "Proportion of examples"],
            loc="lower center",
            ncol=len(labels) + 1,
            frameon=False,
        )
        figure.tight_layout(rect=(0, 0.1, 1, 1))
        figure.savefig(path, dpi=FIGURE_DPI)
