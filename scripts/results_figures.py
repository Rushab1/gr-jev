"""Print the figures of runs from their results folders.

Each test file gets a table with one row per tool list and per group of tool lists. In a wording run a row is one
wording of the instruction. Its columns:

- examples: the examples that have every list of the group
- answers, correct, CSR: one answer per example and list, and the percentage that is correct
- 95% interval: the bootstrap interval of CSR over the examples
- "None": the answers of "None"
- confident, confident and wrong: the answers whose highest probability is at least CONFIDENT_PROBABILITY
- probabilities at 0: the share of the returned probabilities that are 0.00
- entropy: the mean entropy of an answer's probabilities, in bits
- top minus second: the mean of an answer's highest probability minus its second-highest
- highest correct, lowest correct, correct together: for the queries with several correct tools, the mean probability
  of the correct tool with the highest probability, of the one with the lowest, and of all the correct tools summed
- one choice, all correct, none correct: the examples with the same choice in every list of the group, and those
  answered correctly in every list and in none
- second tool wrong, second place tied, top tool wrong: for a query with two correct tools, the answers that miss
  them. The top tool has the highest probability. In a tie, several tools share the second-highest probability.

The lines under a table give CSR on one group of lists minus CSR on another, in points.

A run whose lists hold rewordings or copies of one tool also gets the mean probability of the entries from the highest
of an answer to the lowest, the mean probability at each place of the list, and the answers that select each place.
A run with rotated orders gets the last two by entry too, in the order of the first list, and the examples by the
number of orders that select their most selected entry.
"""

import argparse
from collections.abc import Callable
from pathlib import Path

from grjev.constants import (
    BOOTSTRAP_SEED,
    CONFIDENT_PROBABILITY,
    DOLLARS_PER_MILLION_INPUT_TOKENS,
    LIST_LENGTHS,
    REWORDED_LIST,
    ROTATED_LIST,
)
from grjev.examples import read_jsonl
from grjev.metrics import (
    Figures,
    compared_groups,
    difference,
    figures,
    list_groups,
    list_names,
    most_selected,
    placed,
    ranked_means,
    row_groups,
)
from grjev.runs import Row, RunConfig


def mean_text(value: float | None) -> str:
    """Return a mean with two decimals, or "none" for a group with no query that has several correct tools."""
    return "none" if value is None else f"{value:.2f}"


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
    "entropy": lambda found: f"{found.entropy:.2f}",
    "top minus second": lambda found: f"{found.gap:.2f}",
    "highest correct": lambda found: mean_text(found.highest_correct),
    "lowest correct": lambda found: mean_text(found.lowest_correct),
    "correct together": lambda found: mean_text(found.correct_together),
    "one choice": lambda found: f"{found.one_choice:,}",
    "all correct": lambda found: f"{found.all_correct:,}",
    "none correct": lambda found: f"{found.none_correct:,}",
    "second tool wrong": lambda found: f"{found.second_wrong:,}",
    "second place tied": lambda found: f"{found.second_tied:,}",
    "top tool wrong": lambda found: f"{found.top_wrong:,}",
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


def print_rewordings(rows: list[Row], lists: list[str]) -> None:
    """Print the figures of lists that hold rewordings or copies of one tool: by rank, by place, and by entry."""
    ranked = ", ".join(f"{value:.3f}" for value in ranked_means(rows, lists))
    print(f"\nmean probability of the entries, from the highest of an answer to the lowest: {ranked}")
    by_place = {"at each place of the list": placed(rows, lists)}
    if len(lists) > 1:
        # The first rotation lists the entries in the order in which they are written or made.
        by_place["for each entry, in the order of the first list"] = placed(rows, lists, lists[0])
    for label, (means, selected) in by_place.items():
        print(f"mean probability {label}: {', '.join(f'{value:.3f}' for value in means)}")
        print(f"answers that select it, {label}: {', '.join(map(str, selected))}")
    if len(lists) > 1:
        print(f"examples by the number of orders that select their most selected entry: {most_selected(rows, lists)}")


def print_run(folder: Path) -> None:
    """Print the input tokens of one run and their price, then the figures of each of its test files."""
    config = RunConfig.model_validate_json((folder / "config.json").read_text())
    rows = read_jsonl(folder / "rows.jsonl", Row)
    lengths = LIST_LENGTHS.get(config.dataset, ())
    tokens = sum(row.input_tokens for row in rows)
    questions = sum(len(row.answers) for row in rows)
    dollars = tokens / 1e6 * DOLLARS_PER_MILLION_INPUT_TOKENS[config.model]
    print(f"{folder}: {len(rows):,} examples, {questions:,} questions, {tokens:,} input tokens, ${dollars:.2f}")
    print(f"{tokens / questions:,.0f} input tokens per question, {tokens / len(rows):,.0f} per example")
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
    rewordings = [name for name in list_names(rows) if name.split("_")[0] in (REWORDED_LIST, ROTATED_LIST)]
    if rewordings:
        print_rewordings(rows, rewordings)
    print()


def main() -> None:
    """Print the figures of each named results folder."""
    for folder in parse_args().folders:
        print_run(folder)


if __name__ == "__main__":
    main()
