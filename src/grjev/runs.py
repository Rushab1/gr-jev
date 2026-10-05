"""A run: the tool lists of each example go to Jev as choice questions, and each answer is scored."""

import logging
import random
from collections.abc import Iterable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from pydantic import BaseModel

from grjev.constants import (
    JEV_MODEL,
    JEV_REQUEST_CHARACTERS,
    JEV_WORKERS,
    LIST_LENGTHS,
    NONE_DESCRIPTION,
    NONE_NAME,
    NONE_TEST_FILES,
    ONE_TOOL_INSTRUCTIONS,
    ORDER_SEED,
    PROGRESS_EVERY,
    TWO_TOOL_INSTRUCTIONS,
    TWO_TOOL_TEST_FILES,
    TWO_TOOL_WORDING,
)
from grjev.examples import Example, Option
from grjev.jev import (
    ChoiceAnswer,
    ChoiceQuestion,
    JevRequest,
    JevResponse,
    NoulQuestion,
    ask,
    check_call_limit,
    response_path,
)
from grjev.placement import length_orders, orders_of

logger = logging.getLogger(__name__)

# The test file of an example, the example, and its tool lists by name.
type ExampleLists = Iterator[tuple[str, Example, dict[str, list[Option]]]]


class RunConfig(BaseModel):
    """What a run sends. `examples_per_file` is None for every example, or the size of a seeded sample."""

    experiment: str
    dataset: str
    test_files: tuple[str, ...]
    examples_per_file: int | None = None
    two_tool_wording: str = TWO_TOOL_WORDING
    seed: int = ORDER_SEED
    model: str = JEV_MODEL
    run: int = 1


class ListAnswer(BaseModel):
    """Jev's answer for one tool list. `candidates` holds the names in the order sent."""

    candidates: list[str]
    choice: str
    probabilities: dict[str, float]
    confidence: float
    correct: bool


class Row(BaseModel):
    """One example of a run: its labels and Jev's answer for each of its tool lists."""

    id: str
    test_file: str
    labels: list[str]
    answers: dict[str, ListAnswer]
    input_tokens: int


@dataclass(frozen=True)
class Planned:
    """One example with its tool lists by name and the requests that ask Jev about them."""

    test_file: str
    example: Example
    lists: dict[str, list[Option]]
    requests: list[JevRequest]


def sampled(examples: list[Example], config: RunConfig) -> list[Example]:
    """Return every example, or a seeded sample of the configured size in the order given."""
    if config.examples_per_file is None:
        return examples
    size = min(config.examples_per_file, len(examples))
    kept = set(random.Random(config.seed).sample(range(len(examples)), size))
    return [example for index, example in enumerate(examples) if index in kept]


def position_lists(config: RunConfig, examples: dict[str, list[Example]], tools: list[Option]) -> ExampleLists:
    """Yield each example with its list in the released order and with its correct tools at each placement."""
    for test_file in config.test_files:
        for example in sampled(examples[test_file], config):
            yield test_file, example, orders_of(example, config.seed)


def length_lists(config: RunConfig, examples: dict[str, list[Example]], tools: list[Option]) -> ExampleLists:
    """Yield each different query once, from the first test file that has it, with its lists of every length."""
    first: dict[str, tuple[str, Example]] = {}
    for test_file in config.test_files:
        for example in examples[test_file]:
            first.setdefault(example.query, (test_file, example))
    for test_file in config.test_files:
        own = [example for name, example in first.values() if name == test_file]
        for example in sampled(own, config):
            yield test_file, example, length_orders(example, tools, LIST_LENGTHS[config.dataset], config.seed)


# Experiment -> the function that yields the tool lists of its examples.
LISTS = {"position": position_lists, "length": length_lists}


def criteria_of(config: RunConfig, test_file: str, tools: list[Option]) -> dict[str, str | None]:
    """Return the candidates of a question in the order of the list, with "None" last where it is offered."""
    criteria: dict[str, str | None] = {tool.name: tool.description for tool in tools}
    if test_file in NONE_TEST_FILES[config.dataset]:
        criteria[NONE_NAME] = NONE_DESCRIPTION
    return criteria


def questions_of(config: RunConfig, test_file: str, lists: dict[str, list[Option]]) -> dict[str, ChoiceQuestion]:
    """Return one choice question per tool list, with the instruction of the test file."""
    two_tools = test_file in TWO_TOOL_TEST_FILES[config.dataset]
    instructions = TWO_TOOL_INSTRUCTIONS[config.two_tool_wording] if two_tools else ONE_TOOL_INSTRUCTIONS
    return {
        name: ChoiceQuestion(instructions=instructions, criteria=criteria_of(config, test_file, tools))
        for name, tools in lists.items()
    }


def requests_of(config: RunConfig, query: str, questions: dict[str, ChoiceQuestion]) -> list[JevRequest]:
    """Return the requests of one example: the query as the state, and its questions split to fit a request."""
    groups: list[dict[str, ChoiceQuestion | NoulQuestion]] = [{}]
    size = 0
    for name, question in questions.items():
        characters = sum(len(candidate) + len(text or "") for candidate, text in question.criteria.items())
        if groups[-1] and size + characters > JEV_REQUEST_CHARACTERS:
            groups.append({})
            size = 0
        groups[-1][name] = question
        size += characters
    return [JevRequest(state=query, model=config.model, questions=group) for group in groups]


def plan(config: RunConfig, examples: dict[str, list[Example]], tools: list[Option]) -> list[Planned]:
    """Return every example of the run with its tool lists and requests."""
    planned = []
    for test_file, example, lists in LISTS[config.experiment](config, examples, tools):
        requests = requests_of(config, example.query, questions_of(config, test_file, lists))
        planned.append(Planned(test_file, example, lists, requests))
    return planned


def call_counts(config: RunConfig, planned: Iterable[Planned]) -> dict[str, dict[str, int]]:
    """Return, for each test file, its examples, tool lists and Jev calls, and the calls with no saved response."""
    counts: dict[str, dict[str, int]] = {}
    for item in planned:
        count = counts.setdefault(item.test_file, {"examples": 0, "tool_lists": 0, "calls": 0, "new_calls": 0})
        count["examples"] += 1
        count["tool_lists"] += len(item.lists)
        count["calls"] += len(item.requests)
        count["new_calls"] += sum(not response_path(request, config.run).exists() for request in item.requests)
    return counts


def top_tools(probabilities: dict[str, float], count: int) -> list[str] | None:
    """Return the candidates with the `count` highest probabilities, or None when a tie leaves the last place open."""
    ranked = sorted(probabilities, key=lambda name: probabilities[name], reverse=True)
    if len(ranked) > count and probabilities[ranked[count - 1]] == probabilities[ranked[count]]:
        return None
    return ranked[:count]


def is_correct(config: RunConfig, test_file: str, labels: list[str], answer: ChoiceAnswer) -> bool:
    """Say whether Jev's answer matches the labels: one tool, two tools, or "None" when no tool is correct."""
    if test_file in TWO_TOOL_TEST_FILES[config.dataset]:
        top = top_tools(answer.probabilities, len(labels))
        return top is not None and set(top) == set(labels)
    return answer.choice == (labels[0] if labels else NONE_NAME)


def row_of(config: RunConfig, item: Planned, responses: list[JevResponse]) -> Row:
    """Return the row of one example from Jev's responses to its requests."""
    labels = item.example.labels or []
    given = {name: answer for response in responses for name, answer in response.answers.items()}
    answers = {}
    for name, tools in item.lists.items():
        answer = given[name]
        if not isinstance(answer, ChoiceAnswer):
            raise TypeError(f"{item.example.id}: the answer for {name} is not a choice")
        answers[name] = ListAnswer(
            candidates=list(criteria_of(config, item.test_file, tools)),
            choice=answer.choice,
            probabilities=answer.probabilities,
            confidence=answer.confidence,
            correct=is_correct(config, item.test_file, labels, answer),
        )
    tokens = sum(response.usage.input_tokens for response in responses)
    return Row(id=item.example.id, test_file=item.test_file, labels=labels, answers=answers, input_tokens=tokens)


def run(config: RunConfig, planned: list[Planned]) -> list[Row]:
    """Ask Jev every planned request and return one row per example. The run does not start past the call limit."""
    requests = [request for item in planned for request in item.requests]
    check_call_limit(sum(not response_path(request, config.run).exists() for request in requests))
    responses: list[JevResponse] = []
    with ThreadPoolExecutor(JEV_WORKERS) as workers:
        for response in workers.map(lambda request: ask(request, config.run), requests):
            responses.append(response)
            if len(responses) % PROGRESS_EVERY == 0:
                logger.info("%d of %d requests answered", len(responses), len(requests))
    answered = iter(responses)
    return [row_of(config, item, [next(answered) for _ in item.requests]) for item in planned]


def csr(rows: Iterable[Row]) -> dict[str, dict[str, float]]:
    """Return, for each test file and tool list name, the percentage of examples that Jev answered correctly."""
    outcomes: dict[str, dict[str, list[bool]]] = {}
    for row in rows:
        for name, answer in row.answers.items():
            outcomes.setdefault(row.test_file, {}).setdefault(name, []).append(answer.correct)
    return {
        test_file: {name: 100 * sum(correct) / len(correct) for name, correct in by_list.items()}
        for test_file, by_list in outcomes.items()
    }


def tied_answers(config: RunConfig, rows: Iterable[Row]) -> int:
    """Return the number of two-tool answers in which a tie leaves the second place open."""
    return sum(
        top_tools(answer.probabilities, len(row.labels)) is None
        for row in rows
        if row.test_file in TWO_TOOL_TEST_FILES[config.dataset]
        for answer in row.answers.values()
    )
