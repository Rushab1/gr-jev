"""Run every run of docs/paper_plan.md on one model, one after the other, with scripts/run/run_experiment.py.

`--dry-run` prints the calls of each run and sends nothing. A run whose responses are saved calls nothing, so the
command can be started again after a failure. It stops at the first run that fails.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from grjev.constants import GATEWAY_MODELS, JEV_MODEL, PAPER_RUNS, REPO_ROOT

RUN_SCRIPT = Path(__file__).with_name("run_experiment.py")


def parse_args() -> argparse.Namespace:
    """Read the model and the dry-run switch."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=JEV_MODEL, choices=[JEV_MODEL, *GATEWAY_MODELS])
    parser.add_argument("--dry-run", action="store_true", help="print the calls of each run and send nothing")
    return parser.parse_args()


def main() -> None:
    """Start each run of the plan for the model and stop if one fails."""
    args = parse_args()
    for experiment, dataset, *rest in PAPER_RUNS:
        command = [experiment, "--dataset", dataset, *rest, "--model", args.model, *["--dry-run"] * args.dry_run]
        print(f"### {' '.join(command)}", flush=True)
        subprocess.run([sys.executable, str(RUN_SCRIPT), *command], cwd=REPO_ROOT, check=True)


if __name__ == "__main__":
    main()
