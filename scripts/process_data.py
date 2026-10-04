"""Convert downloaded datasets into the common format in data/<dataset>/processed/."""

import argparse

from grjev.constants import DOWNLOADS, PROCESSED_DIRS
from grjev.metatool import process_metatool

PROCESSORS = {"metatool": process_metatool}


def parse_args() -> argparse.Namespace:
    """Read the dataset names from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("datasets", nargs="+", choices=sorted(PROCESSORS), help="datasets to convert")
    return parser.parse_args()


def main() -> None:
    """Convert each named dataset and print the number of rows in each file written."""
    for name in parse_args().datasets:
        raw_dir = DOWNLOADS[name][2]
        written = PROCESSORS[name](raw_dir, PROCESSED_DIRS[name])
        print(f"{name}: wrote {written} to {PROCESSED_DIRS[name]}")


if __name__ == "__main__":
    main()
