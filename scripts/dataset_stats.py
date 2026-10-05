"""Write the statistics of processed datasets to docs/stats/, where the dashboard loads them."""

import argparse
import json

from grjev.bfcl_values import value_stats
from grjev.constants import DASHBOARD_STATS_DIR, PROCESSED_DIRS, TEST_FILES
from grjev.examples import read_dataset
from grjev.stats import dataset_stats

# Statistics that only one dataset has: dataset name -> the key they are written under and the function that counts.
EXTRA_STATS = {"bfcl": {"values": value_stats}}


def parse_args() -> argparse.Namespace:
    """Read the dataset names from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("datasets", nargs="+", choices=sorted(PROCESSED_DIRS), help="datasets to describe")
    return parser.parse_args()


def main() -> None:
    """Write one JavaScript file per named dataset and print where it is."""
    DASHBOARD_STATS_DIR.mkdir(parents=True, exist_ok=True)
    for name in parse_args().datasets:
        examples, tools = read_dataset(PROCESSED_DIRS[name], TEST_FILES[name])
        extra = {key: count(examples) for key, count in EXTRA_STATS.get(name, {}).items()}
        stats = json.dumps(dataset_stats(examples, tools) | extra, ensure_ascii=False)
        path = DASHBOARD_STATS_DIR / f"{name}.js"
        path.write_text(f"window.STATS = window.STATS || {{}};\nwindow.STATS[{json.dumps(name)}] = {stats};\n")
        print(path)


if __name__ == "__main__":
    main()
