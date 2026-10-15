"""Chart the choices that a probability threshold selects, list against yes/no, on examples with several correct
choices.

The runs are UNIFORM_RUNS and THRESHOLD_YES_NO_RUNS in constants.py, and the probabilities are those saved in
rows.jsonl. The script writes the chart as a PNG file and a Markdown file with the table of the measures. With
`--paper` it also writes the figures of THRESHOLD_PAPER_FIGURES to the folder of the paper.
"""

import argparse
from pathlib import Path

from grjev.constants import PAPER_FIGURES_DIR, THRESHOLD_PAPER_FIGURES, THRESHOLD_YES_NO_RUNS, UNIFORM_RUNS
from grjev.thresholds import chart, read_pairs, table


def parse_args() -> argparse.Namespace:
    """Read the files to write."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chart", type=Path, required=True, help="the PNG file of the chart")
    parser.add_argument("--table", type=Path, required=True, help="the Markdown file of the table")
    parser.add_argument("--paper", action="store_true", help="also write the figures of the paper")
    return parser.parse_args()


def main() -> None:
    """Read the runs, and write the chart and the table."""
    args = parse_args()
    found = read_pairs(UNIFORM_RUNS, THRESHOLD_YES_NO_RUNS)
    chart(found, args.chart)
    title = "# Choices selected by a probability threshold\n\n"
    args.table.write_text(title + f"![The measures against the threshold]({args.chart.name})\n\n" + table(found))
    print(args.chart, args.table)
    for name, measures in THRESHOLD_PAPER_FIGURES.items() if args.paper else ():
        chart(found, PAPER_FIGURES_DIR / f"{name}.pdf", measures, paper=True)
        print(PAPER_FIGURES_DIR / f"{name}.pdf")


if __name__ == "__main__":
    main()
