"""Write the ChaosNLI tables and figure of the paper.

The runs are ANNOTATOR_RUNS in constants.py. The table is ANNOTATORS_PAPER_TABLE in the folder of the tables of the
paper, with ANNOTATORS_ECE_PAPER_TABLE beside it, and the figure is ANNOTATORS_PAPER_FIGURE in the folder of its
figures.
"""

import argparse
from pathlib import Path

from grjev.annotator_charts import gap_chart
from grjev.annotators import all_answers, ece_paper_table, paper_table
from grjev.constants import (
    ANNOTATORS_ECE_PAPER_TABLE,
    ANNOTATORS_PAPER_FIGURE,
    ANNOTATORS_PAPER_TABLE,
    PAPER_FIGURES_DIR,
    PAPER_TABLES_DIR,
)


def parse_args() -> argparse.Namespace:
    """Read the folders to write."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables", type=Path, default=PAPER_TABLES_DIR, help="the folder of the LaTeX file")
    parser.add_argument("--figures", type=Path, default=PAPER_FIGURES_DIR, help="the folder of the PDF file")
    return parser.parse_args()


def main() -> None:
    """Build the tables and the figure from the results folders and write them."""
    args = parse_args()
    table = args.tables / f"{ANNOTATORS_PAPER_TABLE}.tex"
    table.write_text(paper_table(), encoding="utf-8")
    calibration = args.tables / f"{ANNOTATORS_ECE_PAPER_TABLE}.tex"
    calibration.write_text(ece_paper_table(), encoding="utf-8")
    figure = args.figures / f"{ANNOTATORS_PAPER_FIGURE}.pdf"
    gap_chart(all_answers(), figure, paper=True)
    print(table)
    print(calibration)
    print(figure)


if __name__ == "__main__":
    main()
