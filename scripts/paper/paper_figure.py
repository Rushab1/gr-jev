"""Write the figure of a definition in src/grjev/definitions/ as a LaTeX file for the paper.

The file holds a TikZ picture: the correct options of the lists with several correct options on the scale of the
probability, with the threshold of TypeSafe's example code.
"""

import argparse
from pathlib import Path

from grjev.constants import PAPER_FIGURES_DIR, TABLES_DIR
from grjev.figure import figure
from grjev.tables import read_spec, selected


def parse_args() -> argparse.Namespace:
    """Read the name of the definition and the folder to write."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("definition", choices=sorted(path.stem for path in TABLES_DIR.glob("*.json")))
    parser.add_argument("--out", type=Path, default=PAPER_FIGURES_DIR, help="the folder of the LaTeX file")
    return parser.parse_args()


def main() -> None:
    """Build the figure from the results folders and write it."""
    args = parse_args()
    spec = read_spec(TABLES_DIR / f"{args.definition}.json")
    if spec.figure is None:
        raise SystemExit(f"{args.definition} defines no figure")
    rows = {row.label: row for row in spec.rows}
    labels = {label for row in spec.figure.rows for label in (row.run, row.removal)}
    runs = {label: {model: selected(rows[label], model) for model in spec.models} for label in labels}
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / f"{spec.figure.file}.tex"
    path.write_text(figure(spec.figure, runs), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
