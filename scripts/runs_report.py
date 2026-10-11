"""Write the report of runs of a definition in src/grjev/definitions/ as a web page.

The page has one table per run, with the models as rows and the figures as columns. A browser prints it to a PDF.
"""

import argparse
from pathlib import Path

from grjev.constants import TABLES_DIR
from grjev.report import page
from grjev.tables import read_spec


def parse_args() -> argparse.Namespace:
    """Read the name of the definition and the file to write."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("definition", choices=sorted(path.stem for path in TABLES_DIR.glob("*.json")))
    parser.add_argument("--out", type=Path, required=True, help="the HTML file to write")
    return parser.parse_args()


def main() -> None:
    """Build the page of the named definition from the results folders and write it."""
    args = parse_args()
    args.out.write_text(page(read_spec(TABLES_DIR / f"{args.definition}.json")), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
