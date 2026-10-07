"""Compare the answers of two results folders to the same examples, such as two runs of the same requests.

Each line is one tool list: the answers compared, those with the same selected tool, those with the same probability
for every tool, the largest change of one tool's probability, and the largest lead that a first answer gives its
selected tool over the tool that the second answer selects. `--lists` names one list of each folder, for two folders
that name the same list differently.
"""

import argparse
from pathlib import Path

from grjev.examples import read_jsonl
from grjev.metrics import list_names, repeated
from grjev.runs import Row


def parse_args() -> argparse.Namespace:
    """Read the two results folders and the lists to compare from the command line."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("first", type=Path, help="a results folder, such as results/<name>/<date>_<incr>")
    parser.add_argument("second", type=Path, help="a results folder with the same examples")
    parser.add_argument("--lists", nargs=2, metavar=("FIRST", "SECOND"), help="one list of each folder to compare")
    return parser.parse_args()


def main() -> None:
    """Print one line per tool list that both folders answer."""
    args = parse_args()
    first, second = (read_jsonl(folder / "rows.jsonl", Row) for folder in (args.first, args.second))
    shared = [(name, name) for name in list_names(first) if name in list_names(second)]
    for name, other in [tuple(args.lists)] if args.lists else shared:
        found = repeated(first, second, name, other)
        print(
            f"{name} and {other}: {found.answers:,} answers, the same selected tool in {found.same_choice:,}, "
            f"identical in {found.identical:,}, largest change of a probability {found.largest_change:.2f}, "
            f"largest lead overtaken {found.overtaken:.2f}"
        )


if __name__ == "__main__":
    main()
