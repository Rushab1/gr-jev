"""Print the figures of runs from their results folders.

Each test file gets a table with one row per tool list and per group of tool lists. Its columns:

- examples: the examples that have every list of the group
- answers, correct, CSR: one answer per example and list, and the percentage that is correct
- 95% interval: the bootstrap interval of CSR over the examples
- "None": the answers of "None"
- confident, confident and wrong: the answers whose highest probability is at least CONFIDENT_PROBABILITY
- probabilities at 0: the share of the returned probabilities that are 0.00
- one choice, all correct, none correct: the examples with the same choice in every list of the group, and those
  answered correctly in every list and in none
- tied: for two correct tools, the answers with a tie for second place
- choice is correct: the answers whose own choice is a correct tool

The lines under a table give CSR on one group of lists minus CSR on another, in points.
"""

import argparse
from collections.abc import Callable
from pathlib import Path

from grjev.constants import BOOTSTRAP_SEED, CONFIDENT_PROBABILITY, JEV_DOLLARS_PER_MILLION_INPUT_TOKENS, LIST_LENGTHS
from grjev.examples import read_jsonl
from grjev.metrics import Figures, compared_groups, difference, figures, list_groups, list_names, row_groups
from grjev.runs import Row, RunConfig

# Column header -> the text of the column for the figures of one group of tool lists.
COLUMNS: dict[str, Callable[[Figures], str]] = {
    "examples": lambda found: f"{found.examples:,}",
    "answers": lambda found: f"{found.answers:,}",
    "correct": lambda found: f"{found.correct:,}",
    "CSR": lambda found: f"{found.csr:.1f}%",
    "95% interval": lambda found: f"{found.low:.1f} to {found.high:.1f}",
    '"None"': lambda found: f"{found.none:,}",
    "confident": lambda found: f"{found.confident:,}",
    "confident and wrong": lambda found: f"{found.confident_wrong:,}",
    "probabilities at 0": lambda found: f"{found.zero_probabilities:.1f}%",
    "one choice": lambda found: f"{found.one_choice:,}",
    "all correct": lambda found: f"{found.all_correct:,}",
    "none correct": lambda found: f"{found.none_correct:,}",
    "tied": lambda found: f"{found.tied:,}",
    "choice is correct": lambda found: f"{found.choice_correct:,}",
}


def parse_args() -> argparse.Namespace:
    """Read the results folders from the command line."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folders", nargs="+", type=Path, help="results folders, such as results/<name>/<date>_<incr>")
    return parser.parse_args()


def print_table(table: list[list[str]]) -> None:
    """Print rows of cells in aligned columns. The first column is aligned left and the others right."""
    widths = [max(len(cells[column]) for cells in table) for column in range(len(table[0]))]
    for cells in table:
        rest = [cell.rjust(width) for cell, width in zip(cells[1:], widths[1:], strict=True)]
        print("  ".join([cells[0].ljust(widths[0]), *rest]))


def print_run(folder: Path) -> None:
    """Print the input tokens of one run and their price, then the figures of each of its test files."""
    config = RunConfig.model_validate_json((folder / "config.json").read_text())
    rows = read_jsonl(folder / "rows.jsonl", Row)
    lengths = LIST_LENGTHS[config.dataset]
    tokens = sum(row.input_tokens for row in rows)
    tool_lists = sum(len(row.answers) for row in rows)
    dollars = tokens / 1e6 * JEV_DOLLARS_PER_MILLION_INPUT_TOKENS
    print(f"{folder}: {len(rows):,} examples, {tool_lists:,} tool lists, {tokens:,} input tokens, ${dollars:.2f}")
    print(f"{tokens / tool_lists:,.0f} input tokens per tool list, {tokens / len(rows):,.0f} per example")
    for name, own in row_groups(rows).items():
        groups = list_groups(list_names(own), lengths)
        table = [["tool lists", *COLUMNS]]
        for group, lists in groups.items():
            found = figures(own, lists, BOOTSTRAP_SEED, CONFIDENT_PROBABILITY)
            table.append([group, *(cell(found) for cell in COLUMNS.values())])
        print(f"\n{name}")
        print_table(table)
        for comparison, (first, second) in compared_groups(groups, lengths).items():
            points, low, high = difference(own, groups[first], groups[second], BOOTSTRAP_SEED)
            # Adding 0.0 turns a rounded -0.0 into 0.0.
            print(f"{comparison}: {round(points, 1) + 0.0:+.1f} points, 95% interval {low:.1f} to {high:.1f}")
    print()


def main() -> None:
    """Print the figures of each named results folder."""
    for folder in parse_args().folders:
        print_run(folder)


if __name__ == "__main__":
    main()
