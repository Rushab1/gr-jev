"""Count the correct options whose probability is below 1/n, on the lists with several correct options.

The runs and the lists are UNIFORM_RUNS in constants.py, and the probabilities are those saved in rows.jsonl. Without
`--out` the document is printed.
"""

import argparse
from pathlib import Path

from grjev.constants import UNIFORM_BY_LABELS, UNIFORM_RUNS
from grjev.uniform import document


def parse_args() -> argparse.Namespace:
    """Read the file to write."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="the Markdown file to write")
    return parser.parse_args()


def main() -> None:
    """Build the document from the results folders, and write or print it."""
    args = parse_args()
    text = document(UNIFORM_RUNS, UNIFORM_BY_LABELS)
    if args.out is None:
        print(text, end="")
    else:
        args.out.write_text(text, encoding="utf-8")
        print(args.out)


if __name__ == "__main__":
    main()
