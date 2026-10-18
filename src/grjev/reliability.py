"""The reliability diagram of the yes/no answers to examples with two or more correct choices.

Each bin of YES_BIN_EDGES gives a point: the mean probability of yes of its answers against the share of them that are
about a correct choice. A calibrated model puts every point on the diagonal. A second row gives the share minus the
mean probability, which is 0 for a calibrated model.
"""

from pathlib import Path

import matplotlib
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter

from grjev.constants import (
    MODEL_COLORS,
    MODEL_TITLES,
    RELIABILITY_PAGE_SIZE,
    RELIABILITY_PAPER_SIZE,
    TABLES_DIR,
    UNIFORM_DEFINITION,
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


def chart(found: dict[tuple[str, str], list[YesBin | None]], path: Path, paper: bool = False) -> None:
    """Draw one column per dataset: the reliability diagram above and its distance from the diagonal below it."""
    datasets = list(dict.fromkeys(dataset for dataset, _ in found))
    width, heights = RELIABILITY_PAPER_SIZE if paper else RELIABILITY_PAGE_SIZE
    with matplotlib.rc_context({"font.size": 7 if paper else 10, "pdf.fonttype": 42}):
        figure = Figure(figsize=(width, sum(heights) + (0.4 if paper else 0.6)))
        axes = figure.subplots(
            2, len(datasets), sharex=True, sharey="row", squeeze=False, gridspec_kw={"height_ratios": heights}
        )
        for (dataset, model), bins in found.items():
            top, bottom = axes[0][datasets.index(dataset)], axes[1][datasets.index(dataset)]
            held = [part for part in bins if part]
            style = {"color": MODEL_COLORS[model], "linewidth": 1.2 if paper else 1.6, "markersize": 3 if paper else 4}
            top.plot([p.mean for p in held], [p.correct for p in held], "o-", label=MODEL_TITLES[model], **style)
            bottom.plot([p.mean for p in held], [100 * (p.correct - p.mean) for p in held], "o-", **style)
        for column, dataset in enumerate(datasets):
            axes[0][column].plot((0, 1), (0, 1), color="grey", linestyle=":", linewidth=1)
            axes[0][column].set_title(dataset)
            axes[0][column].set_ylim(0, 1.02)
            axes[0][column].yaxis.set_major_formatter(PercentFormatter(1.0))
            axes[0][column].tick_params(labelbottom=True, labelleft=True)
            axes[1][column].tick_params(labelleft=True)
            axes[0][column].set_xlabel("Probability of yes")
            axes[1][column].axhline(0, color="grey", linestyle=":", linewidth=1)
            axes[1][column].set_xlabel("Probability of yes")
        axes[0][0].set_ylabel("Percentage of answers\nthat are correct")
        axes[1][0].set_ylabel("Percentage correct minus\nprobability of yes (points)")
        for axis in axes.flat:
            axis.grid(alpha=0.3)
            axis.set_xlim(0, 1)
        if paper:
            figure.legend(*axes[0][0].get_legend_handles_labels(), loc="lower center", ncol=3, frameon=False)
            figure.tight_layout(rect=(0, 0.08, 1, 1))
        else:
            axes[0][0].legend(fontsize=8, loc="upper left")
            figure.suptitle("Yes/no answers on examples with 2 or more correct choices, in bins of width 0.1")
            figure.tight_layout()
        figure.savefig(path, dpi=130)
