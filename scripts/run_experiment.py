"""Run an experiment on Jev and write its results folder. `--dry-run` prints the Jev calls and sends nothing."""

import argparse
import logging
from datetime import date

from dotenv import load_dotenv

from grjev.constants import (
    EXPERIMENT_TEST_FILES,
    JEV_CALL_LIMIT,
    JEV_DOLLARS_PER_MILLION_INPUT_TOKENS,
    PROCESSED_DIRS,
    TWO_TOOL_INSTRUCTIONS,
    TWO_TOOL_WORDING,
)
from grjev.examples import read_dataset
from grjev.jev import calls_saved
from grjev.results import git_state, new_results_dir, write_run
from grjev.runs import Planned, Row, RunConfig, call_counts, csr, plan, run, tied_answers


def parse_args() -> argparse.Namespace:
    """Read the experiment, the dataset, the sample size and the dry-run switch from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment", choices=sorted(EXPERIMENT_TEST_FILES))
    parser.add_argument("--dataset", default="metatool", choices=sorted(PROCESSED_DIRS))
    parser.add_argument("--test-files", nargs="+", help="default: every test file of the experiment")
    parser.add_argument("--examples-per-file", type=int, help="run a seeded sample of this many examples per file")
    parser.add_argument("--two-tool-wording", choices=sorted(TWO_TOOL_INSTRUCTIONS), default=TWO_TOOL_WORDING)
    parser.add_argument("--dry-run", action="store_true", help="print the number of Jev calls and send nothing")
    return parser.parse_args()


def print_calls(config: RunConfig, planned: list[Planned]) -> None:
    """Print the examples, tool lists and Jev calls of each test file, next to the saved calls and the limit."""
    counts = call_counts(config, planned)
    total = {
        key: sum(count[key] for count in counts.values()) for key in ("examples", "tool_lists", "calls", "new_calls")
    }
    print(f"{'test file':<16}{'examples':>10}{'tool lists':>12}{'Jev calls':>11}{'not saved':>11}")
    for name, count in (counts | {"total": total}).items():
        print(
            f"{name:<16}{count['examples']:>10,}{count['tool_lists']:>12,}{count['calls']:>11,}{count['new_calls']:>11,}"
        )
    print(f"Saved Jev calls: {calls_saved():,}. Limit: {JEV_CALL_LIMIT:,}.")


def print_summary(config: RunConfig, rows: list[Row]) -> None:
    """Print the CSR of each test file and tool list, the tied two-tool answers, and the price of the input tokens."""
    for test_file, by_list in csr(rows).items():
        print(test_file)
        for name, percent in by_list.items():
            print(f"  {name:<28}{percent:6.1f}%")
    tokens = sum(row.input_tokens for row in rows)
    print(f"Two-tool answers with a tie for second place: {tied_answers(config, rows):,}")
    print(f"Input tokens: {tokens:,}, ${tokens / 1e6 * JEV_DOLLARS_PER_MILLION_INPUT_TOKENS:.2f}")


def main() -> None:
    """Plan the run, print its Jev calls, and unless it is a dry run, ask Jev and write the results folder."""
    args = parse_args()
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    config = RunConfig(
        experiment=args.experiment,
        dataset=args.dataset,
        test_files=tuple(args.test_files or EXPERIMENT_TEST_FILES[args.experiment][args.dataset]),
        examples_per_file=args.examples_per_file,
        two_tool_wording=args.two_tool_wording,
    )
    examples, tools = read_dataset(PROCESSED_DIRS[config.dataset], config.test_files)
    planned = plan(config, examples, tools)
    print_calls(config, planned)
    if args.dry_run:
        return
    rows = run(config, planned)
    folder = new_results_dir(f"{config.dataset}_{config.experiment}", date.today())
    write_run(folder, config, git_state() | {"model": config.model}, rows)
    print_summary(config, rows)
    print(folder)


if __name__ == "__main__":
    main()
