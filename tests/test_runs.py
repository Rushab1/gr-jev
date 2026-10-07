"""Tests for grjev.runs and grjev.results. httpx.post is replaced, so nothing reaches the Jev API.

The last three tests plan the runs on the processed MetaTool files and are skipped without them.
"""

import json
from collections import Counter
from datetime import date
from pathlib import Path

import httpx
import pytest

from grjev import jev, results, runs
from grjev.constants import (
    COUNTED_WORDINGS,
    EXPERIMENT_TEST_FILES,
    GROWTH_LENGTHS,
    GROWTH_WORDINGS,
    JEV_MAX_OPTIONS,
    LIST_LENGTHS,
    NONE_NAME,
    ONE_TOOL_INSTRUCTIONS,
    OWN_LIST,
    PADDED_LIST_TOOLS,
    PLACEMENTS,
    PROCESSED_DIRS,
    RELEASED_ORDER,
    TWO_TOOL_INSTRUCTIONS,
    UNCOUNTED_WORDINGS,
)
from grjev.examples import Example, Option, read_dataset
from grjev.runs import (
    ListAnswer,
    Planned,
    Row,
    RunConfig,
    call_counts,
    criteria_of,
    csr,
    is_correct,
    plan,
    run,
    sampled,
    tied_answers,
    top_tools,
)

TOOLS = [Option(name=f"tool_{tool}", description=f"Does thing {tool}.") for tool in range(1, 11)]


class FakeJev:
    """Stands in for httpx.post: records each call and gives the first candidate of every question probability 1."""

    def __init__(self) -> None:
        self.calls: list[bytes] = []

    def post(self, url: str, content: bytes, headers: dict[str, str], timeout: float) -> httpx.Response:
        self.calls.append(content)
        answers = {}
        for name, question in json.loads(content)["questions"].items():
            first, *rest = question["criteria"]
            probabilities = {first: 1.0} | dict.fromkeys(rest, 0.0)
            answers[name] = {"type": "choice", "choice": first, "confidence": 1.0, "probabilities": probabilities}
        payload = {"model": "jev-1.13.0", "answers": answers, "usage": {"input_tokens": 10, "output_tokens": 1}}
        return httpx.Response(200, json=payload, request=httpx.Request("POST", url))


@pytest.fixture
def fake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FakeJev:
    """Replace the API, point the saved responses at a temporary folder, and set a key."""
    fake_jev = FakeJev()
    monkeypatch.setattr(jev.httpx, "post", fake_jev.post)
    monkeypatch.setattr(jev, "JEV_CACHE_DIR", tmp_path / "cache")
    monkeypatch.setenv(jev.JEV_KEY_ENV, "test-key")
    return fake_jev


def config(experiment: str = "position", *test_files: str, dataset: str = "metatool", **changes: object) -> RunConfig:
    files = test_files or EXPERIMENT_TEST_FILES[experiment][dataset]
    return RunConfig.model_validate({"experiment": experiment, "dataset": dataset, "test_files": files} | changes)


def example(number: int, labels: list[str], query: str | None = None) -> Example:
    return Example(id=f"set/file/{number}", query=query or f"Do thing {number}.", options=TOOLS, labels=labels, raw={})


def choice(probabilities: dict[str, float]) -> jev.ChoiceAnswer:
    selected = max(probabilities, key=lambda name: probabilities[name])
    return jev.ChoiceAnswer(type="choice", choice=selected, probabilities=probabilities, confidence=1.0)


def test_candidates_keep_the_order_of_the_list_and_end_with_none_where_it_is_offered() -> None:
    assert list(criteria_of(config(), "similar_tools", TOOLS[:3])) == ["tool_1", "tool_2", "tool_3", NONE_NAME]
    assert list(criteria_of(config(), "reliability", TOOLS[:3])) == ["tool_1", "tool_2", "tool_3", NONE_NAME]
    assert criteria_of(config(), "multi_tool", TOOLS[:2]) == {"tool_1": "Does thing 1.", "tool_2": "Does thing 2."}


def test_a_position_run_asks_one_question_per_order_with_the_query_as_state() -> None:
    examples = {"similar_tools": [example(0, ["tool_4"])], "multi_tool": [example(1, ["tool_7", "tool_8"])]}
    one_tool, two_tools = plan(config("position", "similar_tools", "multi_tool"), examples, TOOLS)
    (request,) = one_tool.requests
    assert request.state == "Do thing 0." and request.model == config().model
    assert list(request.questions) == [RELEASED_ORDER, *PLACEMENTS]
    assert {question.instructions for question in request.questions.values()} == {ONE_TOOL_INSTRUCTIONS}
    questions = two_tools.requests[0].questions
    assert len(questions) == 9
    assert {question.instructions for question in questions.values()} == {TWO_TOOL_INSTRUCTIONS["one"]}


def test_the_wording_for_two_tools_is_set_by_the_config() -> None:
    examples = {"multi_tool": [example(1, ["tool_7", "tool_8"])]}
    (both,) = plan(config("position", "multi_tool", two_tool_wording="both"), examples, TOOLS)
    assert {question.instructions for question in both.requests[0].questions.values()} == {
        TWO_TOOL_INSTRUCTIONS["both"]
    }


def test_questions_are_split_into_requests_that_fit_the_character_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    one_list = sum(
        len(candidate) + len(text or "") for candidate, text in criteria_of(config(), "similar_tools", TOOLS).items()
    )
    monkeypatch.setattr(runs, "JEV_REQUEST_CHARACTERS", 2 * one_list)
    (item,) = plan(config("position", "similar_tools"), {"similar_tools": [example(0, ["tool_4"])]}, TOOLS)
    assert [list(request.questions) for request in item.requests] == [
        [RELEASED_ORDER, "first"],
        ["quarter", "middle"],
        ["three_quarters", "last"],
    ]
    assert {request.state for request in item.requests} == {"Do thing 0."}


def test_a_length_run_sends_each_different_query_once_from_the_first_file_that_has_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(runs.LIST_LENGTHS, "metatool", (5, 10))
    examples = {
        "similar_tools": [example(0, ["tool_4"], "shared query"), example(1, ["tool_2"])],
        "scenario": [
            example(2, ["tool_4"], "shared query"),
            example(3, ["tool_9"]),
            example(4, ["tool_9"], "Do thing 3."),
        ],
    }
    planned = plan(config("length"), examples, TOOLS)
    assert [(item.test_file, item.example.id) for item in planned] == [
        ("similar_tools", "set/file/0"),
        ("similar_tools", "set/file/1"),
        ("scenario", "set/file/3"),
    ]
    assert list(planned[0].lists) == [f"{length}_{name}" for length in (5, 10) for name in PLACEMENTS]
    assert all(
        list(criteria_of(config("length"), "scenario", tools))[-1] == NONE_NAME for tools in planned[2].lists.values()
    )


def wording_config() -> RunConfig:
    return config("wording", "G1_tool", dataset="stabletoolbench")


def test_a_wording_run_asks_one_padded_list_with_each_wording_and_names_the_number_of_correct_tools() -> None:
    three_correct = Example(
        id="set/G1_tool/0", query="Do three things.", options=TOOLS[:4], labels=["tool_1", "tool_3", "tool_4"], raw={}
    )
    (item,) = plan(wording_config(), {"G1_tool": [three_correct]}, TOOLS)
    (request,) = item.requests
    assert request.state == "Do three things."
    assert list(request.questions) == [*COUNTED_WORDINGS, *UNCOUNTED_WORDINGS] == ["one", "all", "equal", "every"]
    opening = "Three tools in the list are appropriate to solve the user's query."
    assert [question.instructions for question in request.questions.values()] == [
        f"{opening} Choose one of them.",
        f"{opening} Choose all of them.",
        f"{opening} Choose all of them with equal probability.",
        "Choose every tool in the list that is needed to solve the user's query.",
    ]
    lists = [[tool.name for tool in tools] for tools in item.lists.values()]
    assert all(candidates == lists[0] for candidates in lists)
    assert lists[0] == list(criteria_of(wording_config(), "G1_tool", item.lists["one"]))
    assert len(lists[0]) == PADDED_LIST_TOOLS and NONE_NAME not in lists[0]
    assert {"tool_1", "tool_2", "tool_3", "tool_4"} < set(lists[0]) <= {tool.name for tool in TOOLS}


def test_a_wording_run_asks_a_query_with_one_correct_tool_only_without_the_number() -> None:
    one_correct = Example(id="set/G1_tool/1", query="Do one thing.", options=TOOLS[:7], labels=["tool_2"], raw={})
    (item,) = plan(wording_config(), {"G1_tool": [one_correct]}, TOOLS)
    assert list(item.requests[0].questions) == list(UNCOUNTED_WORDINGS)
    assert sorted(tool.name for tool in item.lists["every"]) == sorted(tool.name for tool in TOOLS[:7])


def test_a_growth_run_asks_the_padded_list_and_every_grown_list_with_both_wordings() -> None:
    apis = [Option(name=f"api_{number}", description=f"Does thing {number}.") for number in range(1, 251)]
    two_correct = Example(
        id="set/G1_tool/0", query="Do two things.", options=apis[:3], labels=["api_1", "api_3"], raw={}
    )
    run_config = config("growth", "G1_tool", dataset="stabletoolbench")
    (item,) = plan(run_config, {"G1_tool": [two_correct]}, apis)
    sizes = [OWN_LIST, *map(str, GROWTH_LENGTHS["stabletoolbench"])]
    assert list(item.lists) == [f"{size}_{wording}" for size in sizes for wording in GROWTH_WORDINGS]
    assert [len(item.lists[f"{size}_all"]) for size in sizes] == [PADDED_LIST_TOOLS, 20, 50, 100, 199]
    assert all(item.lists[f"{size}_all"] == item.lists[f"{size}_every"] for size in sizes)
    asked = {name: question.instructions for request in item.requests for name, question in request.questions.items()}
    assert asked["199_all"] == "Two tools in the list are appropriate to solve the user's query. Choose all of them."
    assert asked["own_every"] == UNCOUNTED_WORDINGS["every"]
    (single,) = plan(run_config, {"G1_tool": [two_correct.model_copy(update={"labels": ["api_1"]})]}, apis)
    assert list(single.lists) == [f"{size}_every" for size in sizes]


def test_a_wording_answer_is_correct_when_the_highest_probabilities_are_the_correct_tools() -> None:
    run_config = wording_config()
    three = choice({"a": 0.4, "b": 0.3, "c": 0.2, "d": 0.1})
    assert is_correct(run_config, "G1_tool", ["a", "b", "c"], three)
    assert not is_correct(run_config, "G1_tool", ["a", "b", "d"], three)
    assert is_correct(run_config, "G1_tool", ["a"], three)
    assert not is_correct(run_config, "G1_tool", ["a", "b", "c"], choice({"a": 0.8, "b": 0.1, "c": 0.05, "d": 0.05}))


def test_a_tool_with_a_blank_description_is_sent_without_one() -> None:
    blank = [Option(name="tool_a", description=" "), Option(name="tool_b", description="Does thing b.")]
    assert criteria_of(wording_config(), "G1_tool", blank) == {"tool_a": None, "tool_b": "Does thing b."}


def test_top_tools_are_the_highest_probabilities_unless_a_tie_leaves_the_last_place_open() -> None:
    assert top_tools({"a": 0.3, "b": 0.6, "c": 0.1}, 2) == ["b", "a"]
    assert top_tools({"a": 0.5, "b": 0.5, "c": 0.0}, 2) == ["a", "b"]
    assert top_tools({"a": 0.9, "b": 0.05, "c": 0.05}, 2) is None
    assert top_tools({"a": 1.0, "b": 0.0}, 2) == ["a", "b"]


def test_an_answer_is_scored_as_one_tool_two_tools_or_none() -> None:
    assert is_correct(config(), "similar_tools", ["a"], choice({"a": 0.7, "b": 0.2, NONE_NAME: 0.1}))
    assert not is_correct(config(), "similar_tools", ["b"], choice({"a": 0.7, "b": 0.2, NONE_NAME: 0.1}))
    assert is_correct(config(), "reliability", [], choice({"a": 0.2, NONE_NAME: 0.8}))
    assert not is_correct(config(), "reliability", [], choice({"a": 0.8, NONE_NAME: 0.2}))
    assert is_correct(config(), "multi_tool", ["a", "b"], choice({"a": 0.3, "b": 0.6, "c": 0.1}))
    assert not is_correct(config(), "multi_tool", ["a", "c"], choice({"a": 0.3, "b": 0.6, "c": 0.1}))
    assert not is_correct(config(), "multi_tool", ["a", "b"], choice({"a": 0.9, "b": 0.05, "c": 0.05}))


def planned_examples() -> tuple[RunConfig, list[Planned]]:
    run_config = config("position", "similar_tools", "reliability")
    examples = {"similar_tools": [example(0, ["tool_4"]), example(1, ["tool_9"])], "reliability": [example(2, [])]}
    return run_config, plan(run_config, examples, TOOLS)


def test_a_run_asks_once_per_request_and_scores_every_list(fake: FakeJev) -> None:
    run_config, planned = planned_examples()
    assert call_counts(run_config, planned) == {
        "similar_tools": {"examples": 2, "questions": 12, "calls": 2, "new_calls": 2},
        "reliability": {"examples": 1, "questions": 1, "calls": 1, "new_calls": 1},
    }
    first, _, none_correct = run(run_config, planned)
    assert len(fake.calls) == 3
    assert first.id == "set/file/0" and first.test_file == "similar_tools" and first.labels == ["tool_4"]
    assert first.input_tokens == 10
    assert list(first.answers) == [RELEASED_ORDER, *PLACEMENTS]
    # The fake selects the first candidate, so only the placement that puts the correct tool first is correct.
    assert [name for name, answer in first.answers.items() if answer.correct] == ["first"]
    assert first.answers["last"].candidates[-2:] == ["tool_4", NONE_NAME]
    assert first.answers["last"].choice == first.answers["last"].candidates[0]
    assert none_correct.answers[RELEASED_ORDER].candidates[-1] == NONE_NAME
    assert not none_correct.answers[RELEASED_ORDER].correct


def test_the_answers_of_split_requests_are_joined_in_one_row(fake: FakeJev, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runs, "JEV_REQUEST_CHARACTERS", 1)
    run_config = config("position", "similar_tools")
    planned = plan(run_config, {"similar_tools": [example(0, ["tool_4"])]}, TOOLS)
    (row,) = run(run_config, planned)
    assert len(fake.calls) == 6 and row.input_tokens == 60
    assert list(row.answers) == [RELEASED_ORDER, *PLACEMENTS]


def test_a_second_run_reads_the_saved_responses(fake: FakeJev) -> None:
    run_config, planned = planned_examples()
    assert run(run_config, planned) == run(run_config, planned)
    assert len(fake.calls) == 3
    assert sum(count["new_calls"] for count in call_counts(run_config, planned).values()) == 0
    repeat = run_config.model_copy(update={"run": 2})
    assert sum(count["new_calls"] for count in call_counts(repeat, planned).values()) == 3


def test_a_run_past_the_call_limit_does_not_start(fake: FakeJev, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jev, "JEV_CALL_LIMIT", 2)
    with pytest.raises(RuntimeError, match="limit of 2"):
        run(*planned_examples())
    assert fake.calls == []
    assert jev.calls_saved() == 0


def test_a_sample_is_seeded_and_keeps_the_order_given() -> None:
    examples = [example(number, ["tool_1"]) for number in range(10)]
    assert sampled(examples, config()) == examples
    sample = sampled(examples, config(examples_per_file=3))
    assert len(sample) == 3 and sample == sampled(examples, config(examples_per_file=3))
    assert [item.id for item in sample] == sorted(item.id for item in sample)
    assert sampled(examples, config(examples_per_file=50)) == examples


def row(test_file: str, labels: list[str], answers: dict[str, tuple[dict[str, float], bool]]) -> Row:
    list_answers = {
        name: ListAnswer(
            candidates=list(probabilities),
            choice=max(probabilities, key=lambda candidate: probabilities[candidate]),
            probabilities=probabilities,
            confidence=1.0,
            correct=correct,
        )
        for name, (probabilities, correct) in answers.items()
    }
    return Row(id="set/file/0", test_file=test_file, labels=labels, answers=list_answers, input_tokens=10)


def test_csr_is_the_percentage_correct_for_each_test_file_and_list() -> None:
    rows = [
        row("similar_tools", ["a"], {"first": ({"a": 1.0, "b": 0.0}, True), "last": ({"b": 1.0, "a": 0.0}, False)}),
        row("similar_tools", ["a"], {"first": ({"a": 1.0, "b": 0.0}, True), "last": ({"b": 0.0, "a": 1.0}, True)}),
        row("multi_tool", ["a", "b"], {"adjacent_first": ({"a": 0.9, "b": 0.05, "c": 0.05}, False)}),
    ]
    assert csr(rows) == {"similar_tools": {"first": 100.0, "last": 50.0}, "multi_tool": {"adjacent_first": 0.0}}
    assert tied_answers(config(), rows) == 1


def test_results_folders_are_numbered_within_a_day(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(results, "RESULTS_DIR", tmp_path)
    day = date(2026, 10, 4)
    first = results.new_results_dir("metatool_position", day)
    second = results.new_results_dir("metatool_position", day)
    assert (first, second) == (
        tmp_path / "metatool_position" / "2026-10-04_01",
        tmp_path / "metatool_position" / "2026-10-04_02",
    )
    rows = [row("similar_tools", ["a"], {"first": ({"a": 1.0, "b": 0.0}, True)})]
    results.write_run(first, config(), {"model": "jev-1.13.0"}, rows)
    assert sorted(path.name for path in first.iterdir()) == ["config.json", "meta.json", "rows.jsonl"]
    assert RunConfig.model_validate_json((first / "config.json").read_text()) == config()
    assert json.loads((first / "meta.json").read_text()) == {"model": "jev-1.13.0"}
    assert [Row.model_validate_json(line) for line in (first / "rows.jsonl").read_text().splitlines()] == rows


def test_the_state_of_the_repository_names_a_commit() -> None:
    state = results.git_state()
    assert len(state["git_commit"]) == 40 and isinstance(state["git_dirty"], bool)


@pytest.fixture(scope="module")
def metatool() -> tuple[dict[str, list[Example]], list[Option]]:
    """The examples of the processed MetaTool test files that the experiments send, and the tool list."""
    folder = PROCESSED_DIRS["metatool"]
    test_files = EXPERIMENT_TEST_FILES["position"]["metatool"]
    if not all((folder / f"{name}.jsonl").exists() for name in test_files):
        pytest.skip("MetaTool is not processed")
    return read_dataset(folder, test_files)


def test_the_metatool_position_run_has_the_planned_requests_and_tool_lists(
    metatool: tuple[dict[str, list[Example]], list[Option]],
) -> None:
    planned = plan(config("position"), *metatool)
    assert {name: count["examples"] for name, count in call_counts(config(), planned).items()} == {
        "similar_tools": 995,
        "scenario": 1800,
        "multi_tool": 497,
        "reliability": 995,
    }
    assert Counter({name: count["questions"] for name, count in call_counts(config(), planned).items()}) == {
        "similar_tools": 5970,
        "scenario": 10800,
        "multi_tool": 4473,
        "reliability": 995,
    }
    assert len({jev.request_body(request) for item in planned for request in item.requests}) == 4287


def test_every_metatool_order_holds_the_released_tools_with_the_correct_ones_at_their_positions(
    metatool: tuple[dict[str, list[Example]], list[Option]],
) -> None:
    placed_at: dict[str, set[tuple[int, ...]]] = {}
    for item in plan(config("position"), *metatool):
        labels = item.example.labels or []
        released = sorted(tool.name for tool in item.lists[RELEASED_ORDER])
        assert NONE_NAME not in released and len(released) < JEV_MAX_OPTIONS
        for name, tools in item.lists.items():
            assert sorted(tool.name for tool in tools) == released
            if name != RELEASED_ORDER:
                where = tuple(position for position, tool in enumerate(tools, start=1) if tool.name in labels)
                placed_at.setdefault(f"{item.test_file} {len(tools)} {name}", set()).add(where)
    assert all(len(where) == 1 for where in placed_at.values())
    assert [placed_at[f"similar_tools 10 {name}"] for name in PLACEMENTS] == [{(1,)}, {(3,)}, {(5,)}, {(8,)}, {(10,)}]
    assert [placed_at[f"scenario 15 {name}"] for name in PLACEMENTS] == [{(1,)}, {(4,)}, {(8,)}, {(11,)}, {(15,)}]
    assert placed_at["multi_tool 10 adjacent_last"] == {(9, 10)}
    assert placed_at["multi_tool 10 separated_first_middle"] == {(1, 5)}


def test_the_metatool_length_run_sends_1790_queries_in_two_requests_each(
    metatool: tuple[dict[str, list[Example]], list[Option]],
) -> None:
    planned = plan(config("length"), *metatool)
    counts = call_counts(config("length"), planned)
    assert {name: count["examples"] for name, count in counts.items()} == {"similar_tools": 995, "scenario": 795}
    assert sum(count["questions"] for count in counts.values()) == 53700
    assert {len(item.requests) for item in planned} == {2}
    assert len({item.example.query for item in planned}) == 1790
    for item in planned[:: len(planned) // 20]:
        (label,) = item.example.labels or []
        for length in LIST_LENGTHS["metatool"]:
            for name, position in zip(PLACEMENTS, [1, 3, 5, 8, 10] if length == 10 else [None] * 5, strict=True):
                tools = [tool.name for tool in item.lists[f"{length}_{name}"]]
                assert len(tools) == len(set(tools)) == length and label in tools
                assert position is None or tools.index(label) + 1 == position


@pytest.fixture(scope="module")
def stabletoolbench() -> tuple[dict[str, list[Example]], list[Option]]:
    """The examples of the processed StableToolBench test files, and the list of all APIs."""
    folder = PROCESSED_DIRS["stabletoolbench"]
    test_files = EXPERIMENT_TEST_FILES["wording"]["stabletoolbench"]
    if not all((folder / f"{name}.jsonl").exists() for name in test_files):
        pytest.skip("StableToolBench is not processed")
    return read_dataset(folder, test_files)


def test_the_stabletoolbench_wording_subset_sends_one_request_per_example(
    stabletoolbench: tuple[dict[str, list[Example]], list[Option]],
) -> None:
    run_config = config("wording", dataset="stabletoolbench", examples_per_file=50)
    planned = plan(run_config, *stabletoolbench)
    counts = call_counts(run_config, planned)
    assert {name: count["examples"] for name, count in counts.items()} == dict.fromkeys(run_config.test_files, 50)
    assert sum(count["calls"] for count in counts.values()) == 300
    # 6 of the 300 queries have one relevant API and get the one wording that does not state the number.
    assert sum(count["questions"] for count in counts.values()) == 6 * 1 + 294 * 4
    for item in planned:
        labels = item.example.labels or []
        (apis,) = {tuple(tool.name for tool in tools) for tools in item.lists.values()}
        assert len(apis) == len(set(apis)) == max(len(item.example.options), PADDED_LIST_TOOLS)
        assert {option.name for option in item.example.options} <= set(apis) and set(labels) <= set(apis)
        assert list(item.lists) == (
            [*COUNTED_WORDINGS, *UNCOUNTED_WORDINGS] if len(labels) > 1 else [*UNCOUNTED_WORDINGS]
        )


def test_the_stabletoolbench_growth_subset_grows_the_list_that_the_wording_run_sends(
    stabletoolbench: tuple[dict[str, list[Example]], list[Option]],
) -> None:
    planned = plan(config("growth", dataset="stabletoolbench", examples_per_file=8), *stabletoolbench)
    assert len(planned) == 48
    wording = {item.example.id: item for item in plan(config("wording", dataset="stabletoolbench"), *stabletoolbench)}
    for item in planned:
        labels = item.example.labels or []
        assert item.lists[f"{OWN_LIST}_every"] == wording[item.example.id].lists["every"]
        for size in GROWTH_LENGTHS["stabletoolbench"]:
            apis = [tool.name for tool in item.lists[f"{size}_every"]]
            assert len(apis) == len(set(apis)) == size and set(labels) <= set(apis)
