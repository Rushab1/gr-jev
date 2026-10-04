"""Statistics of a dataset in the common format. Nothing here knows which dataset it is given."""

import math
import re
import statistics
from collections import defaultdict
from collections.abc import Callable, Sequence
from itertools import pairwise
from typing import Any

import numpy as np

from grjev.constants import EXTREMES_SHOWN, HISTOGRAM_BINS, LOG_BINS_RATIO, STOP_WORDS_TEXT, WORD_PATTERN
from grjev.examples import Example, Option

WORD = re.compile(WORD_PATTERN)
STOP_WORDS = frozenset(STOP_WORDS_TEXT.split())
# Returns the tool names that an example counts towards.
type NamesOf = Callable[[Example], list[str]]


def words(text: str) -> list[str]:
    """Split text into lower-case words."""
    return WORD.findall(text.lower())


def content_words(text: str) -> list[str]:
    """Return the words of text that are not stop words."""
    return [word for word in words(text) if word not in STOP_WORDS]


def option_text(option: Option) -> str:
    """Return the text a model reads for one option."""
    return f"{option.name} {option.description}"


def input_words(example: Example) -> int:
    """Count the words of the query and of every option."""
    return len(words(example.query)) + sum(len(words(option_text(option))) for option in example.options)


def label_positions(example: Example) -> list[int]:
    """Return the positions of the correct options in the list, counting from 1."""
    return [position for position, option in enumerate(example.options, 1) if option.name in example.labels]


def overlap_scores(example: Example) -> list[int]:
    """Count, for each option, the content words it shares with the query."""
    query = set(content_words(example.query))
    return [len(query & set(content_words(option_text(option)))) for option in example.options]


def overlap_accuracy(examples: list[Example]) -> float | None:
    """Return the accuracy of selecting the option that shares the most words with the query.

    Ties are split evenly, so list order gives no advantage. Only examples with one correct option count.
    """
    credits = []
    for example in examples:
        if len(example.labels) != 1 or not example.options:
            continue
        scores = overlap_scores(example)
        best = [option.name for option, score in zip(example.options, scores, strict=True) if score == max(scores)]
        credits.append(1 / len(best) if example.labels[0] in best else 0.0)
    return statistics.mean(credits) if credits else None


def label_description_words(examples: list[Example]) -> tuple[list[int], list[int]]:
    """Return the description lengths, in words, of the correct options and of the other options."""
    correct: list[int] = []
    other: list[int] = []
    for example in examples:
        for option in example.options:
            (correct if option.name in example.labels else other).append(len(words(option.description)))
    return correct, other


def integer_bins(values: Sequence[int]) -> list[dict[str, int]]:
    """Group values into bins that each cover the integers `from` to `to`, with the number of values inside.

    A small range gets one bin per value. A long right tail gets bins that widen geometrically, so the bulk of the
    values is not squeezed into the first bin.
    """
    low, high = min(values), max(values)
    if low > 0 and high > LOG_BINS_RATIO * statistics.median(values):
        edges = sorted({round(edge) for edge in np.geomspace(low, high + 1, HISTOGRAM_BINS + 1)})
    else:
        width = math.ceil((high - low + 1) / HISTOGRAM_BINS)
        edges = list(range(low, high + width + 1, width))
    counts = np.histogram(values, bins=edges)[0]
    bins = zip(pairwise(edges), counts, strict=True)
    return [{"from": start, "to": end - 1, "count": int(count)} for (start, end), count in bins]


def distribution(values: Sequence[int]) -> dict[str, Any] | None:
    """Return the median, the range and the bins of the values, or None when there are no values."""
    if not values:
        return None
    return {"median": statistics.median(values), "min": min(values), "max": max(values), "bins": integer_bins(values)}


def mean_or_none(values: Sequence[int]) -> float | None:
    """Return the mean rounded to one decimal, or None when there are no values."""
    return round(statistics.mean(values), 1) if values else None


def file_stats(examples: list[Example]) -> dict[str, Any]:
    """Return the statistics of one test file."""
    correct, other = label_description_words(examples)
    accuracy = overlap_accuracy(examples)
    return {
        "examples": len(examples),
        "query_words": distribution([len(words(example.query)) for example in examples]),
        "input_words": distribution([input_words(example) for example in examples]),
        "options": distribution([len(example.options) for example in examples]),
        "correct_options": distribution([len(example.labels) for example in examples]),
        "position": distribution([position for example in examples for position in label_positions(example)]),
        "overlap_accuracy": None if accuracy is None else round(100 * accuracy, 1),
        "correct_description_words": mean_or_none(correct),
        "other_description_words": mean_or_none(other),
    }


def option_names(example: Example) -> list[str]:
    """Return the names of the options in the example's list."""
    return [option.name for option in example.options]


def correct_option_names(example: Example) -> list[str]:
    """Return the names of the correct options. An example without a list has none: its label is yes or no."""
    return example.labels if example.options else []


def examples_by_name(examples: list[Example], names_of: NamesOf) -> dict[str, list[Example]]:
    """Group the examples under each tool name that names_of returns for them."""
    grouped: dict[str, list[Example]] = defaultdict(list)
    for example in examples:
        for name in names_of(example):
            grouped[name].append(example)
    return grouped


def tool_row(name: str, by_file: dict[str, dict[str, list[Example]]]) -> dict[str, Any]:
    """Count the examples grouped under one tool: in each test file, in total, and as different queries."""
    found = {file: grouped.get(name, []) for file, grouped in by_file.items()}
    return {
        "name": name,
        "examples": sum(len(examples) for examples in found.values()),
        "queries": len({example.query for examples in found.values() for example in examples}),
        "by_file": {file: len(examples) for file, examples in found.items()},
    }


def tool_usage(dataset: dict[str, list[Example]], tools: list[Option], names_of: NamesOf) -> dict[str, Any]:
    """Describe the examples that names_of ties to each tool: the spread over the tools and the tools at both ends.

    A test file where names_of ties no example to a tool is left out. The tools at the lowest count are named only
    when there are at most EXTREMES_SHOWN of them.
    """
    by_file = {file: examples_by_name(examples, names_of) for file, examples in dataset.items()}
    by_file = {file: grouped for file, grouped in by_file.items() if grouped}
    rows = sorted((tool_row(tool.name, by_file) for tool in tools), key=lambda row: (-row["examples"], row["name"]))
    lowest = rows[-1]["examples"]
    at_lowest = [row["name"] for row in rows if row["examples"] == lowest]
    tied = [example for examples in dataset.values() for example in examples if names_of(example)]
    return {
        "examples": len(tied),
        "queries": len({example.query for example in tied}),
        "per_tool": distribution([row["examples"] for row in rows]),
        "highest": rows[:EXTREMES_SHOWN],
        "lowest": lowest,
        "tools_at_lowest": len(at_lowest),
        "lowest_names": at_lowest if len(at_lowest) <= EXTREMES_SHOWN else [],
    }


def dataset_stats(dataset: dict[str, list[Example]], tools: list[Option]) -> dict[str, Any]:
    """Return every statistic the dashboard shows for a dataset."""
    return {
        "files": {name: file_stats(file_examples) for name, file_examples in dataset.items()},
        "tools": len(tools),
        "tool_description_words": distribution([len(words(tool.description)) for tool in tools]),
        "listed": tool_usage(dataset, tools, option_names),
        "correct": tool_usage(dataset, tools, correct_option_names),
    }
