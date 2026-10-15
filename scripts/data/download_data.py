"""Download the dataset files pinned in grjev.constants into data/<dataset>/raw/."""

import argparse
import logging

from grjev.constants import DOWNLOADS
from grjev.download import download_files


def parse_args() -> argparse.Namespace:
    """Read the dataset names from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("datasets", nargs="+", choices=sorted(DOWNLOADS), help="datasets to download")
    return parser.parse_args()


def main() -> None:
    """Download each named dataset and print a summary line for it."""
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    for name in args.datasets:
        base_url, sha256_by_path, raw_dir = DOWNLOADS[name]
        fetched = download_files(base_url, sha256_by_path, raw_dir)
        print(f"{name}: {len(sha256_by_path)} files verified in {raw_dir}, {fetched} downloaded in this run")


if __name__ == "__main__":
    main()
