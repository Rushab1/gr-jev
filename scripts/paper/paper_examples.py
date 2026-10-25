"""Write the table of one example from each dataset and test file as a LaTeX file.

The examples are EXAMPLE_TABLE_ROWS in constants.py, and the code is in src/grjev/example_tables.py.
"""

import argparse
from pathlib import Path

from grjev.constants import EXAMPLES_PAPER_TABLE, PAPER_TABLES_DIR
from grjev.example_tables import paper_table


def parse_args() -> argparse.Namespace:
    """Read the folder to write."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=PAPER_TABLES_DIR, help="the folder of the LaTeX file")
    return parser.parse_args()


def main() -> None:
    """Build the table from the results folders and write it."""
    path = parse_args().out / f"{EXAMPLES_PAPER_TABLE}.tex"
    path.write_text(paper_table(), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
