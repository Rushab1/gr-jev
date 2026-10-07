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
- one choice, all correct, none correct: the examples with the same choice in every list of the group, and those
  answered correctly in every list and in none
- second tool wrong, second place tied, top tool wrong: for a query with two correct tools, the answers that miss
  them. The top tool has the highest probability. In a tie, several tools share the second-highest probability.

The lines under a table give CSR on one group of lists minus CSR on another, in points.

A reworded run also gets the figures of the rewordings of each example's reworded tool. `--before` names a results
folder and a tool list of a run that asked the same examples before the tool was reworded, and adds the mean
probability of that tool in those answers.
"""

import argparse
from collections.abc import Callable
from pathlib import Path

from grjev.constants import (
    BOOTSTRAP_SEED,
    CONFIDENT_PROBABILITY,
    JEV_DOLLARS_PER_MILLION_INPUT_TOKENS,
    LIST_LENGTHS,
    REWORDED_LIST,
    REWORDINGS_FILES,
)
from grjev.examples import read_jsonl, read_rewordings
from grjev.metrics import (
    Figures,
    compared_groups,
    difference,
    figures,
    group_figures,
    list_groups,
    list_names,
    reworded_tools,
    row_groups,
    tool_probability,
)
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
    "entropy": lambda found: f"{found.entropy:.2f}",
    "top minus second": lambda found: f"{found.gap:.2f}",
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
    parser.add_argument("--before", nargs=2, metavar=("FOLDER", "LIST"), help="a run and its list before the rewording")
    return parser.parse_args()


def print_table(table: list[list[str]]) -> None:
    """Print rows of cells in aligned columns. The first column is aligned left and the others right."""
    widths = [max(len(cells[column]) for cells in table) for column in range(len(table[0]))]
    for cells in table:
        rest = [cell.rjust(width) for cell, width in zip(cells[1:], widths[1:], strict=True)]
        print("  ".join([cells[0].ljust(widths[0]), *rest]))


def print_rewordings(config: RunConfig, rows: list[Row], before: list[str] | None) -> None:
    """Print the figures of the rewordings of a reworded run, and the probability of the reworded tools before it."""
    rewordings = read_rewordings(REWORDINGS_FILES[config.dataset])
    originals = {tool.name: original for original, tools in rewordings.items() for tool in tools}
    found = group_figures(rows, REWORDED_LIST, originals)
    print(f"\nrewordings of one correct tool, {found.answers:,} answers")
    print(f"mean probability, from the top rewording of an answer down: {', '.join(f'{p:.3f}' for p in found.ranked)}")
    print(f"mean probability of the rewordings together: {found.total:.3f}")
    print(f"answers that give every rewording 0: {found.empty:,}")
    print(f"mean share of the rewordings' probability that the top rewording has: {found.top_share:.1f}%")
    print(f"mean entropy of the rewordings' probabilities divided by their sum: {found.entropy:.2f} bits")
    if before:
        folder, name = before
        mean = tool_probability(read_jsonl(Path(folder) / "rows.jsonl", Row), name, reworded_tools(rows, originals))
        print(f"mean probability of the tool before it is reworded, in the list {name} of {folder}: {mean:.3f}")


def print_run(folder: Path, before: list[str] | None) -> None:
    """Print the input tokens of one run and their price, then the figures of each of its test files."""
    config = RunConfig.model_validate_json((folder / "config.json").read_text())
    rows = read_jsonl(folder / "rows.jsonl", Row)
    lengths = LIST_LENGTHS.get(config.dataset, ())
    tokens = sum(row.input_tokens for row in rows)
    questions = sum(len(row.answers) for row in rows)
    dollars = tokens / 1e6 * JEV_DOLLARS_PER_MILLION_INPUT_TOKENS
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
    if REWORDED_LIST in list_names(rows):
        print_rewordings(config, rows, before)
    print()


def main() -> None:
    """Print the figures of each named results folder."""
    args = parse_args()
    for folder in args.folders:
        print_run(folder, args.before)


if __name__ == "__main__":
    main()
