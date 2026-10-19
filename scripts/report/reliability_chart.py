"""Draw the reliability diagram of the yes/no answers to the examples with several correct choices.

The runs are THRESHOLD_YES_NO_RUNS in constants.py and the bins YES_BIN_EDGES. With `--paper` the script also writes
the diagram to the folder of the paper as reliability.pdf. It prints the expected calibration error of the yes/no
answers over every bin and without the first YES_ECE_SKIPPED_BINS bins.
"""

import argparse
from pathlib import Path

from grjev.constants import PAPER_FIGURES_DIR, THRESHOLD_YES_NO_RUNS
from grjev.reliability import chart, ece_table, read_bins


def parse_args() -> argparse.Namespace:
    """Read the file to write."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chart", type=Path, required=True, help="the PNG file of the diagram")
    parser.add_argument("--paper", action="store_true", help="also write the figure of the paper")
    return parser.parse_args()


def main() -> None:
    """Read the runs and draw the diagram."""
    args = parse_args()
    found = read_bins(THRESHOLD_YES_NO_RUNS)
    chart(found, args.chart)
    print(args.chart)
    print(ece_table(found))
    if args.paper:
        chart(found, PAPER_FIGURES_DIR / "reliability.pdf", paper=True)
        print(PAPER_FIGURES_DIR / "reliability.pdf")


if __name__ == "__main__":
    main()
