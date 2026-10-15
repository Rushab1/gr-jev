"""Write the tables of the findings of a definition in scripts/definitions/ as LaTeX files for the paper.

Each finding whose table names a file gets `<file>.tex` in the output folder: a `tabular` with the models as rows.
"""

import argparse
from pathlib import Path

from grjev.constants import PAPER_TABLES_DIR, TABLES_DIR
from grjev.report import paper_latex
from grjev.tables import read_spec, selected


def parse_args() -> argparse.Namespace:
    """Read the name of the definition and the folder to write."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("definition", choices=sorted(path.stem for path in TABLES_DIR.glob("*.json")))
    parser.add_argument("--out", type=Path, default=PAPER_TABLES_DIR, help="the folder of the LaTeX files")
    return parser.parse_args()


def main() -> None:
    """Build the LaTeX table of each finding from the results folders and write it."""
    args = parse_args()
    spec = read_spec(TABLES_DIR / f"{args.definition}.json")
    rows = {row.label: row for row in spec.rows}
    args.out.mkdir(parents=True, exist_ok=True)
    for finding in spec.findings:
        if finding.table is None or not finding.table.file:
            continue
        labels = {part.run for part in finding.table.parts}
        runs = {
            label: {model: selected(rows[label], model) for model in rows[label].models or spec.models}
            for label in labels
        }
        path = args.out / f"{finding.table.file}.tex"
        path.write_text(paper_latex(finding.table, runs), encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
