"""Write the 95% bootstrap intervals of the main figures of the paper as a LaTeX table.

The runs are UNIFORM_RUNS, COPIES_RUNS and THRESHOLD_YES_NO_RUNS in constants.py. The table is INTERVALS_PAPER_TABLE
in the folder of the paper.
"""

import argparse
from pathlib import Path

from grjev.constants import INTERVALS_PAPER_TABLE, PAPER_TABLES_DIR
from grjev.intervals import paper_table


def parse_args() -> argparse.Namespace:
    """Read the folder to write."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=PAPER_TABLES_DIR, help="the folder of the LaTeX file")
    return parser.parse_args()


def main() -> None:
    """Build the table from the results folders and write it."""
    args = parse_args()
    path = args.out / f"{INTERVALS_PAPER_TABLE}.tex"
    path.write_text(paper_table(), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
