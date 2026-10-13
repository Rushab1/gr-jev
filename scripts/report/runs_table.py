"""Write the table of runs of a definition in src/grjev/definitions/, such as docs/all_runs.md from all_runs.json.

Without `--out` the document is printed.
"""

import argparse
from pathlib import Path

from grjev.constants import TABLES_DIR
from grjev.tables import markdown, read_spec


def parse_args() -> argparse.Namespace:
    """Read the name of the definition and the file to write."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("definition", choices=sorted(path.stem for path in TABLES_DIR.glob("*.json")))
    parser.add_argument("--out", type=Path, help="the Markdown file to write")
    return parser.parse_args()


def main() -> None:
    """Build the document of the named definition from the results folders, and write or print it."""
    args = parse_args()
    document = markdown(read_spec(TABLES_DIR / f"{args.definition}.json"))
    if args.out is None:
        print(document, end="")
    else:
        args.out.write_text(document, encoding="utf-8")
        print(args.out)


if __name__ == "__main__":
    main()
