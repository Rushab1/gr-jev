"""Run an experiment on Jev or a gateway model and write its results folder.

`--dry-run` prints the calls and sends nothing.
"""

import argparse
import logging
from datetime import date

from dotenv import load_dotenv

from grjev.constants import (
    DOLLARS_PER_MILLION_INPUT_TOKENS,
    EXPERIMENT_TEST_FILES,
    GATEWAY_MODELS,
    JEV_CALL_LIMIT,
    JEV_MODEL,
    PROCESSED_DIRS,
    RESULTS_MODEL_NAMES,
    TWO_TOOL_INSTRUCTIONS,
    TWO_TOOL_WORDING,
)
from grjev.examples import read_dataset
from grjev.jev import calls_saved
from grjev.results import git_state, new_results_dir, write_run
from grjev.runs import Planned, Row, RunConfig, call_counts, csr, plan, run, tied_answers


def parse_args() -> argparse.Namespace:
    """Read the experiment, the dataset, the sample size, the run number and the dry-run switch."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment", choices=sorted(EXPERIMENT_TEST_FILES))
    parser.add_argument("--dataset", default="metatool", choices=sorted(PROCESSED_DIRS))
    parser.add_argument("--test-files", nargs="+", help="default: every test file of the experiment")
    sample = parser.add_mutually_exclusive_group()
    sample.add_argument("--examples-per-file", type=int, help="run a seeded sample of this many examples per file")
    sample.add_argument("--examples", type=int, help="run a seeded sample of this many examples over all the files")
    parser.add_argument("--two-tool-wording", choices=sorted(TWO_TOOL_INSTRUCTIONS), default=TWO_TOOL_WORDING)
    parser.add_argument("--run", type=int, default=1, help="run number: a new number asks Jev the same requests again")
    parser.add_argument("--model", default=JEV_MODEL, choices=[JEV_MODEL, *GATEWAY_MODELS])
    parser.add_argument("--dry-run", action="store_true", help="print the number of Jev calls and send nothing")
    return parser.parse_args()


def print_calls(config: RunConfig, planned: list[Planned]) -> None:
    """Print the examples, questions and calls of each test file, next to the saved Jev calls and the limit."""
    counts = call_counts(config, planned)
    total = {
        key: sum(count[key] for count in counts.values()) for key in ("examples", "questions", "calls", "new_calls")
    }
    print(f"{'test file':<16}{'examples':>10}{'questions':>12}{'calls':>11}{'not saved':>11}")
    for name, count in (counts | {"total": total}).items():
        print(
            f"{name:<16}{count['examples']:>10,}{count['questions']:>12,}{count['calls']:>11,}{count['new_calls']:>11,}"
        )
    print(f"Saved Jev calls: {calls_saved():,}. Limit: {JEV_CALL_LIMIT:,}.")


def print_summary(config: RunConfig, rows: list[Row]) -> None:
    """Print the CSR of each test file and question, the answers a tie leaves open, and the price of the tokens."""
    for test_file, by_list in csr(rows).items():
        print(test_file)
        for name, percent in by_list.items():
            print(f"  {name:<28}{percent:6.1f}%")
    tokens = sum(row.input_tokens for row in rows)
    rejected = sum(len(row.rejected) for row in rows)
    print(f"Tool lists answered: {sum(len(row.answers) for row in rows):,}. Rejected by the model: {rejected:,}")
    print(
        f"Answers to a query with several correct tools where a tie leaves a place open: {tied_answers(config, rows):,}"
    )
    print(f"Input tokens: {tokens:,}, ${tokens / 1e6 * DOLLARS_PER_MILLION_INPUT_TOKENS[config.model]:.2f}")


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
        examples=args.examples,
        two_tool_wording=args.two_tool_wording,
        model=args.model,
        run=args.run,
    )
    examples, tools = read_dataset(PROCESSED_DIRS[config.dataset], config.test_files)
    planned = plan(config, examples, tools)
    print_calls(config, planned)
    if args.dry_run:
        return
    rows = run(config, planned)
    name = "_".join([config.dataset, config.experiment, *(RESULTS_MODEL_NAMES.get(config.model, ""),)]).rstrip("_")
    folder = new_results_dir(name, date.today())
    write_run(folder, config, git_state() | {"model": config.model}, rows)
    print_summary(config, rows)
    print(folder)


if __name__ == "__main__":
    main()
