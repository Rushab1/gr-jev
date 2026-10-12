"""Convert downloaded datasets into the common format in data/<dataset>/processed/."""

import argparse

from grjev.bfcl import process_bfcl
from grjev.constants import DOWNLOADS, PROCESSED_DIRS, TICKETS_FILE
from grjev.ecthr import process_ecthr
from grjev.hotpotqa import process_hotpotqa
from grjev.metatool import process_metatool
from grjev.mmlu import process_mmlu, process_mmlu_na
from grjev.stabletoolbench import process_stabletoolbench
from grjev.tickets import process_tickets

PROCESSORS = {
    "metatool": process_metatool,
    "stabletoolbench": process_stabletoolbench,
    "bfcl": process_bfcl,
    "mmlu": process_mmlu,
    "mmlu_na": process_mmlu_na,
    "hotpotqa": process_hotpotqa,
    "ecthr": process_ecthr,
    "tickets": process_tickets,
}


def parse_args() -> argparse.Namespace:
    """Read the dataset names from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("datasets", nargs="+", choices=sorted(PROCESSORS), help="datasets to convert")
    return parser.parse_args()


def main() -> None:
    """Convert each named dataset and print the number of rows in each file written."""
    for name in parse_args().datasets:
        # The tickets are written in the repository and have no download.
        raw_dir = DOWNLOADS[name][2] if name in DOWNLOADS else TICKETS_FILE.parent
        written = PROCESSORS[name](raw_dir, PROCESSED_DIRS[name])
        print(f"{name}: wrote {written} to {PROCESSED_DIRS[name]}")


if __name__ == "__main__":
    main()
