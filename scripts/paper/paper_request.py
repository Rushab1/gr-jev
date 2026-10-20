"""Write the list of a request written for the paper as a LaTeX table: the question, the instruction and the options.

Several requests that hold the same lists give one table with the question of each. The file is named after the
first request. The requests are in scripts/run/requests/.
"""

import argparse
from pathlib import Path

from grjev.constants import JEV_MODEL, PAPER_TABLES_DIR, WRITTEN_REQUESTS_DIR
from grjev.written import read_written, request_latex


def parse_args() -> argparse.Namespace:
    """Read the names of the requests and the folder to write."""
    parser = argparse.ArgumentParser(description=__doc__)
    names = sorted(path.stem for path in WRITTEN_REQUESTS_DIR.glob("*.json"))
    parser.add_argument("requests", nargs="+", choices=names, help="requests that hold the same lists")
    parser.add_argument("--only", nargs="+", default=[], help="the options to show, default: every option")
    parser.add_argument("--cut", nargs="+", default=[], help="phrases: an option is shown up to the end of the first")
    parser.add_argument("--no-titles", action="store_true", help="one column, without the names of the options")
    parser.add_argument("--name", help="the name of the LaTeX file, default: the first request")
    parser.add_argument("--out", type=Path, default=PAPER_TABLES_DIR, help="the folder of the LaTeX file")
    return parser.parse_args()


def main() -> None:
    """Write the table of the requests."""
    args = parse_args()
    requests = [read_written(WRITTEN_REQUESTS_DIR / f"{name}.json", JEV_MODEL) for name in args.requests]
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / f"{args.name or args.requests[0]}.tex"
    path.write_text(request_latex(requests, args.only, args.cut, not args.no_titles), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
