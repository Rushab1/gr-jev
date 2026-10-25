"""The parts shared by the matplotlib charts that put a measure against the bins of a probability.

Each chart draws one line per model over the bins, with a bar per bin behind it for the share of the answers in it.
"""

from collections.abc import Sequence

from matplotlib.axes import Axes
from matplotlib.ticker import NullLocator


def share_axis(axis: Axes, edges: Sequence[float], ticked: bool, labelled: bool) -> Axes:
    """Return an axis behind `axis` for the share of the answers in each bin, on a log scale from 0.1% to 100%."""
    behind = axis.twinx()
    behind.set_yscale("log")
    behind.set_ylim(0.001, 1)
    behind.set_yticks([0.001, 0.01, 0.1, 1], ["0.1%", "1%", "10%", "100%"])
    behind.yaxis.set_minor_locator(NullLocator())
    behind.tick_params(labelright=ticked, colors="grey")
    if labelled:
        behind.set_ylabel("Percentage of answers in the bin\n(log scale)", color="grey")
    for edge in edges[1:-1]:
        behind.axvline(edge, color="black", linestyle=":", linewidth=0.6, zorder=3)
    axis.set_zorder(behind.get_zorder() + 1)
    axis.patch.set_visible(False)
    return behind


def draw_shares(
    axis: Axes, spans: Sequence[tuple[float, float]], counts: Sequence[int], colour: str, place: tuple[int, int]
) -> None:
    """Draw a bar per bin with the share of a model's answers in it, the `place[0]`th of `place[1]` bars in a bin."""
    total = sum(counts)
    width = (spans[0][1] - spans[0][0]) / place[1]
    lefts = [low + place[0] * width for low, _ in spans]
    axis.bar(lefts, [count / total for count in counts], width, align="edge", color=colour, alpha=0.25, linewidth=0)


def bin_ticks(axis: Axes, edges: Sequence[float]) -> None:
    """Put a tick on every bin edge and a label on every second one."""
    axis.set_xticks(list(edges), [f"{edge:.1f}" if step % 2 == 0 else "" for step, edge in enumerate(edges)])
