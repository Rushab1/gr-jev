"""A run: the tool lists of each example go to Jev as choice questions, and each answer is scored."""

import logging
import random
from collections.abc import Collection, Iterable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from pydantic import BaseModel

from grjev.constants import (
    ABSENT_LIST_TOOLS,
    COPIED_TOOLS,
    COUNTED_WORDINGS,
    GROWTH_LENGTHS,
    GROWTH_WORDINGS,
    JEV_MODEL,
    JEV_REQUEST_CHARACTERS,
    JEV_WORKERS,
    LIST_LENGTHS,
    NO_ADDED_NONE_EXPERIMENTS,
    NONE_DESCRIPTION,
    NONE_NAME,
    NONE_TEST_FILES,
    NUMBER_WORDS,
    ONE_TOOL_INSTRUCTIONS,
    ORDER_SEED,
    PADDED_LIST_TOOLS,
    PROGRESS_EVERY,
    REWORDED_INSTRUCTIONS,
    REWORDED_LIST,
    REWORDING_EXPERIMENTS,
    REWORDINGS_FILES,
    SEVERAL_TOOL_TEST_FILES,
    TWO_TOOL_INSTRUCTIONS,
    TWO_TOOL_WORDING,
    UNCOUNTED_WORDINGS,
)
from grjev.examples import Example, Option, read_rewordings
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
from grjev.placement import (
    grown_orders,
    length_orders,
    orders_of,
    padded_order,
    reworded_order,
    reworded_tool,
    rotated_orders,
    spaced_copies,
    wrong_tools,
)

logger = logging.getLogger(__name__)

# The test file of an example, the example, its tool lists by name, and the instruction sent with each list.
type ExampleLists = Iterator[tuple[str, Example, dict[str, list[Option]], dict[str, str]]]


class RunConfig(BaseModel):
    """What a run sends.

    A run sends every example, or a seeded sample: `examples_per_file` examples of each test file, or `examples`
    examples over all the test files.
    """

    experiment: str
    dataset: str
    test_files: tuple[str, ...]
    examples_per_file: int | None = None
    examples: int | None = None
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


def sample_size(config: RunConfig, test_file: str) -> int | None:
    """Return the number of examples that are sampled from a test file, or None for every example.

    A total of `examples` is spread over the test files as evenly as possible, and the first files get one more.
    """
    if config.examples is None:
        return config.examples_per_file
    share, extra = divmod(config.examples, len(config.test_files))
    return share + (config.test_files.index(test_file) < extra)


def sampled(examples: list[Example], size: int | None, seed: int) -> list[Example]:
    """Return every example, or a seeded sample of the given size in the order given."""
    if size is None:
        return examples
    kept = set(random.Random(seed).sample(range(len(examples)), min(size, len(examples))))
    return [example for index, example in enumerate(examples) if index in kept]


def file_instructions(config: RunConfig, test_file: str) -> str:
    """Return the instruction of a test file: for one tool, or for two tools in the wording of the config."""
    if test_file in SEVERAL_TOOL_TEST_FILES[config.dataset]:
        return TWO_TOOL_INSTRUCTIONS[config.two_tool_wording]
    return ONE_TOOL_INSTRUCTIONS


def position_lists(config: RunConfig, examples: dict[str, list[Example]], tools: list[Option]) -> ExampleLists:
    """Yield each example with its list in the released order and with its correct tools at each placement."""
    for test_file in config.test_files:
        for example in sampled(examples[test_file], sample_size(config, test_file), config.seed):
            lists = orders_of(example, config.seed)
            yield test_file, example, lists, dict.fromkeys(lists, file_instructions(config, test_file))


def length_lists(config: RunConfig, examples: dict[str, list[Example]], tools: list[Option]) -> ExampleLists:
    """Yield each different query once, from the first test file that has it, with its lists of every length."""
    first: dict[str, tuple[str, Example]] = {}
    for test_file in config.test_files:
        for example in examples[test_file]:
            first.setdefault(example.query, (test_file, example))
    for test_file in config.test_files:
        own = [example for name, example in first.values() if name == test_file]
        for example in sampled(own, sample_size(config, test_file), config.seed):
            lists = length_orders(example, tools, LIST_LENGTHS[config.dataset], config.seed)
            yield test_file, example, lists, dict.fromkeys(lists, file_instructions(config, test_file))


def wording_instructions(example: Example, names: Collection[str]) -> dict[str, str]:
    """Return the instruction of each named wording that is sent for the example, by name of the wording.

    A wording that states the number of correct tools is sent only for a query with two or more of them.
    """
    correct = len(example.labels or [])
    counted = [name for name in names if name in COUNTED_WORDINGS and correct > 1]
    instructions = {name: COUNTED_WORDINGS[name].format(number=NUMBER_WORDS[correct]) for name in counted}
    return instructions | {name: UNCOUNTED_WORDINGS[name] for name in names if name in UNCOUNTED_WORDINGS}


def wording_lists(config: RunConfig, examples: dict[str, list[Example]], tools: list[Option]) -> ExampleLists:
    """Yield each example with one tool list, under the name of each wording of the instruction it is sent with.

    The list holds the example's tools in a seeded order, with random other tools added to a short list.
    """
    for test_file in config.test_files:
        for example in sampled(examples[test_file], sample_size(config, test_file), config.seed):
            instructions = wording_instructions(example, [*COUNTED_WORDINGS, *UNCOUNTED_WORDINGS])
            order = padded_order(example, tools, PADDED_LIST_TOOLS, config.seed)
            yield test_file, example, dict.fromkeys(instructions, order), instructions


def growth_lists(config: RunConfig, examples: dict[str, list[Example]], tools: list[Option]) -> ExampleLists:
    """Yield each example with its padded tool list and with that list grown to each length, under each wording.

    A list is named by its length, or by OWN_LIST before it is grown, and by the wording of its instruction.
    """
    for test_file in config.test_files:
        for example in sampled(examples[test_file], sample_size(config, test_file), config.seed):
            orders = grown_orders(example, tools, PADDED_LIST_TOOLS, GROWTH_LENGTHS[config.dataset], config.seed)
            wordings = wording_instructions(example, GROWTH_WORDINGS)
            lists = {f"{size}_{wording}": order for size, order in orders.items() for wording in wordings}
            instructions = {f"{size}_{wording}": text for size in orders for wording, text in wordings.items()}
            yield test_file, example, lists, instructions


def with_rewordings(
    config: RunConfig, examples: dict[str, list[Example]]
) -> Iterator[tuple[str, Example, list[Option]]]:
    """Yield each example with the rewordings of one of its correct tools, in the order in which they are written.

    The correct tool is chosen with the seed. The labels of the yielded example are the rewordings.
    """
    rewordings = read_rewordings(REWORDINGS_FILES[config.dataset])
    for test_file in config.test_files:
        for example in sampled(examples[test_file], sample_size(config, test_file), config.seed):
            written = rewordings[reworded_tool(example, config.seed)]
            yield test_file, example.model_copy(update={"labels": [tool.name for tool in written]}), written


def reworded_lists(config: RunConfig, examples: dict[str, list[Example]], tools: list[Option]) -> ExampleLists:
    """Yield each example with the rewordings of one of its correct tools as its tool list, in a seeded order."""
    for test_file, example, written in with_rewordings(config, examples):
        lists = {REWORDED_LIST: reworded_order(example, written, config.seed)}
        yield test_file, example, lists, {REWORDED_LIST: REWORDED_INSTRUCTIONS}


def rotated_lists(config: RunConfig, examples: dict[str, list[Example]], tools: list[Option]) -> ExampleLists:
    """Yield each example with the rewordings of one of its correct tools as its tool list, in every rotation."""
    for test_file, example, written in with_rewordings(config, examples):
        lists = rotated_orders(written)
        yield test_file, example, lists, dict.fromkeys(lists, REWORDED_INSTRUCTIONS)


def copied_lists(config: RunConfig, examples: dict[str, list[Example]], tools: list[Option]) -> ExampleLists:
    """Yield each example with copies of one of its correct tools as its tool list, in every rotation.

    The correct tool is chosen with the seed. The names of the copies differ only by extra spaces, and the labels of
    the yielded example are the copies.
    """
    for test_file in config.test_files:
        for example in sampled(examples[test_file], sample_size(config, test_file), config.seed):
            original = reworded_tool(example, config.seed)
            tool = next(option for option in example.options if option.name == original)
            copies = spaced_copies(tool, COPIED_TOOLS, f"{config.seed}/{example.id}/copied")
            lists = rotated_orders(copies)
            relabelled = example.model_copy(update={"labels": [copy.name for copy in copies]})
            yield test_file, relabelled, lists, dict.fromkeys(lists, REWORDED_INSTRUCTIONS)


def absent_lists(config: RunConfig, examples: dict[str, list[Example]], tools: list[Option]) -> ExampleLists:
    """Yield each example with a list that has no correct tool, in every rotation.

    The list holds tools of the example that are not correct, chosen with the seed, and the "None" candidate, which
    is last in the first rotation. The yielded example has no label, so "None" is the correct answer.
    """
    none = Option(name=NONE_NAME, description=NONE_DESCRIPTION)
    for test_file in config.test_files:
        for example in sampled(examples[test_file], sample_size(config, test_file), config.seed):
            lists = rotated_orders([*wrong_tools(example, ABSENT_LIST_TOOLS, config.seed), none])
            yield (
                test_file,
                example.model_copy(update={"labels": []}),
                lists,
                dict.fromkeys(lists, ONE_TOOL_INSTRUCTIONS),
            )


# Experiment -> the function that yields the tool lists of its examples.
LISTS = {
    "position": position_lists,
    "length": length_lists,
    "wording": wording_lists,
    "growth": growth_lists,
    "reworded": reworded_lists,
    "rotated": rotated_lists,
    "copied": copied_lists,
    "absent": absent_lists,
}


def criteria_of(config: RunConfig, test_file: str, tools: list[Option]) -> dict[str, str | None]:
    """Return the candidates of a question in the order of the list, with "None" last where it is offered.

    A tool with a blank description is sent without one. A list of rewordings or of copies offers no "None", and an
    "absent" list holds it already.
    """
    criteria: dict[str, str | None] = {
        tool.name: tool.description if tool.description.strip() else None for tool in tools
    }
    if test_file in NONE_TEST_FILES[config.dataset] and config.experiment not in NO_ADDED_NONE_EXPERIMENTS:
        criteria[NONE_NAME] = NONE_DESCRIPTION
    return criteria


def questions_of(
    config: RunConfig, test_file: str, lists: dict[str, list[Option]], instructions: dict[str, str]
) -> dict[str, ChoiceQuestion]:
    """Return one choice question per tool list, with the instruction of that list."""
    return {
        name: ChoiceQuestion(instructions=instructions[name], criteria=criteria_of(config, test_file, tools))
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
    for test_file, example, lists, instructions in LISTS[config.experiment](config, examples, tools):
        requests = requests_of(config, example.query, questions_of(config, test_file, lists, instructions))
        planned.append(Planned(test_file, example, lists, requests))
    return planned


def call_counts(config: RunConfig, planned: Iterable[Planned]) -> dict[str, dict[str, int]]:
    """Return, for each test file, its examples, questions and Jev calls, and the calls with no saved response."""
    counts: dict[str, dict[str, int]] = {}
    for item in planned:
        count = counts.setdefault(item.test_file, {"examples": 0, "questions": 0, "calls": 0, "new_calls": 0})
        count["examples"] += 1
        count["questions"] += len(item.lists)
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
    """Say whether Jev's answer matches the labels.

    In a test file with several correct tools, and for a list of rewordings, its k highest-probability tools are the k
    correct tools. Elsewhere its choice is the correct tool, or "None" when no tool is correct.
    """
    if test_file in SEVERAL_TOOL_TEST_FILES[config.dataset] or config.experiment in REWORDING_EXPERIMENTS:
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
        if row.test_file in SEVERAL_TOOL_TEST_FILES[config.dataset]
        for answer in row.answers.values()
    )
