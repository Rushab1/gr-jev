"""The reliability diagram of the yes/no answers to examples with two or more correct choices.

Each bin of YES_BIN_EDGES gives a point: the mean probability of yes of its answers against the share of them that are
about a correct choice. A calibrated model puts every point on the diagonal. A second row gives the share minus the
mean probability, which is 0 for a calibrated model. Bars behind both rows give the share of the answers in each bin.
The expected calibration error is given over every bin and without the first YES_ECE_SKIPPED_BINS bins.
"""

from collections.abc import Sequence
from pathlib import Path

import matplotlib
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter

from grjev.bin_charts import bin_ticks, draw_shares, share_axis
from grjev.constants import (
    FIGURE_DPI,
    MODEL_COLORS,
    MODEL_TITLES,
    RELIABILITY_PAGE_SIZE,
    RELIABILITY_PAPER_SIZE,
    TABLES_DIR,
    UNIFORM_DEFINITION,
    YES_BIN_EDGES,
    YES_ECE_SKIPPED_BINS,
)
from grjev.distribution import YesBin, yes_bins
from grjev.tables import read_spec, selected


def read_bins(yes_runs: dict[str, str]) -> dict[tuple[str, str], list[YesBin | None]]:
    """Return the bins of the yes/no answers for each dataset and model, from the run of each dataset in `yes_runs`."""
    spec = read_spec(TABLES_DIR / f"{UNIFORM_DEFINITION}.json")
    rows = {row.label: row for row in spec.rows}
    return {
        (dataset, model): yes_bins(selected(rows[label], model).rows)
        for dataset, label in yes_runs.items()
        for model in spec.models
    }


def yes_ece(bins: Sequence[YesBin | None], skipped: int = 0) -> float:
    """Return the expected calibration error of the bins after the first `skipped`, weighted by their answers."""
    held = [part for part in bins[skipped:] if part]
    total = sum(part.answers for part in held)
    return sum(part.answers / total * abs(part.correct - part.mean) for part in held)


def ece_table(found: dict[tuple[str, str], list[YesBin | None]]) -> str:
    """Return a Markdown table of the expected calibration error over every bin and without the first bins."""
    lines = [
        "| Dataset | Model | Answers | ECE over every bin | Answers in the bins left out | ECE without those bins |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for (dataset, model), bins in found.items():
        answers = sum(part.answers for part in bins if part)
        left_out = sum(part.answers for part in bins[:YES_ECE_SKIPPED_BINS] if part)
        every, rest = yes_ece(bins), yes_ece(bins, YES_ECE_SKIPPED_BINS)
        lines.append(
            f"| {dataset} | {MODEL_TITLES[model]} | {answers:,} | {every:.3f} "
            f"| {left_out:,} ({left_out / answers:.0%}) | {rest:.3f} |"
        )
    return "\n".join(lines)


def chart(found: dict[tuple[str, str], list[YesBin | None]], path: Path, paper: bool = False) -> None:
    """Draw one column per dataset: the reliability diagram above and its distance from the diagonal below it, each
    over the share of the answers in each bin."""
    datasets = list(dict.fromkeys(dataset for dataset, _ in found))
    models = list(dict.fromkeys(model for _, model in found))
    width, heights = RELIABILITY_PAPER_SIZE if paper else RELIABILITY_PAGE_SIZE
    with matplotlib.rc_context({"font.size": 7 if paper else 10, "pdf.fonttype": 42}):
        figure = Figure(figsize=(width, sum(heights) + (0.4 if paper else 0.6)))
        axes = figure.subplots(
            2, len(datasets), sharex=True, sharey="row", squeeze=False, gridspec_kw={"height_ratios": heights}
        )
        behind = {axis: share_axis(axis, YES_BIN_EDGES, axis in axes[:, -1], axis is axes[0][-1]) for axis in axes.flat}
        for (dataset, model), bins in found.items():
            top, bottom = axes[0][datasets.index(dataset)], axes[1][datasets.index(dataset)]
            held = [part for part in bins if part]
            style = {"color": MODEL_COLORS[model], "linewidth": 1.2 if paper else 1.6, "markersize": 3 if paper else 4}
            top.plot([p.mean for p in held], [p.correct for p in held], "o-", label=MODEL_TITLES[model], **style)
            bottom.plot([p.mean for p in held], [100 * (p.correct - p.mean) for p in held], "o-", **style)
            for axis in (top, bottom):
                spans = [(part.low, part.high) for part in held]
                counts = [part.answers for part in held]
                draw_shares(behind[axis], spans, counts, MODEL_COLORS[model], (models.index(model), len(models)))
        for column, dataset in enumerate(datasets):
            axes[0][column].plot((0, 1), (0, 1), color="grey", linestyle=":", linewidth=1)
            axes[0][column].set_title(dataset)
            axes[0][column].set_ylim(0, 1.02)
            axes[0][column].yaxis.set_major_formatter(PercentFormatter(1.0))
            axes[0][column].tick_params(labelbottom=True, labelleft=True)
            axes[1][column].tick_params(labelleft=True)
            axes[0][column].set_xlabel("Mean predicted probability of yes")
            axes[1][column].axhline(0, color="grey", linestyle=":", linewidth=1)
            axes[1][column].set_xlabel("Mean predicted probability of yes")
        axes[0][0].set_ylabel("Observed frequency")
        axes[1][0].set_ylabel("Observed frequency minus mean\npredicted probability (points)")
        for axis in axes.flat:
            axis.grid(alpha=0.3, axis="y")
            axis.set_xlim(0, 1)
            bin_ticks(axis, YES_BIN_EDGES)
        if paper:
            figure.legend(*axes[0][0].get_legend_handles_labels(), loc="lower center", ncol=3, frameon=False)
            figure.tight_layout(rect=(0, 0.08, 1, 1))
        else:
            axes[0][0].legend(fontsize=8, loc="upper left")
            figure.tight_layout()
        figure.savefig(path, dpi=FIGURE_DPI)
