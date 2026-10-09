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
    LAYA_MODEL,
    LIST_LENGTHS,
    LUNA_MODEL,
    NONE_NAME,
    ONE_TOOL_INSTRUCTIONS,
    OWN_LIST,
    PADDED_LIST_TOOLS,
    PLACEMENTS,
    PROCESSED_DIRS,
    RELEASED_ORDER,
    REWORDED_LIST,
    REWORDINGS_FILES,
    TWO_TOOL_INSTRUCTIONS,
    UNCOUNTED_WORDINGS,
)
from grjev.examples import Example, Option, read_dataset, read_rewordings
from grjev.placement import reworded_order, reworded_tool
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
    sample_size,
    sampled,
    tied_answers,
    top_tools,
)

TOOLS = [Option(name=f"tool_{tool}", description=f"Does thing {tool}.") for tool in range(1, 11)]
CHOICES = [Option(name=choice, description="") for choice in ("3", "4", "5", "6")]


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
    monkeypatch.setattr(jev, "GATEWAY_CACHE_DIR", tmp_path / "gateway")
    monkeypatch.setenv(jev.JEV_KEY_ENV, "test-key")
    monkeypatch.setenv(jev.GATEWAY_KEY_ENV, "gateway-key")
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


def test_a_reworded_run_asks_a_list_that_holds_only_the_rewordings_of_one_correct_tool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    two_correct = Example(
        id="set/G1_tool/0", query="Do two things.", options=TOOLS[:3], labels=["tool_1", "tool_3"], raw={}
    )
    rewordings = {
        name: [Option(name=f"{name}_reworded_{number}", description=f"Said way {number}.") for number in range(1, 6)]
        for name in ("tool_1", "tool_3")
    }
    saved = {name: [tool.model_dump() for tool in tools] for name, tools in rewordings.items()}
    (tmp_path / "rewordings.json").write_text(json.dumps(saved))
    monkeypatch.setitem(REWORDINGS_FILES, "stabletoolbench", tmp_path / "rewordings.json")
    run_config = config("reworded", "G1_tool", dataset="stabletoolbench")
    (item,) = plan(run_config, {"G1_tool": [two_correct]}, TOOLS)
    (request,) = item.requests
    (question,) = request.questions.values()
    assert request.state == "Do two things." and list(request.questions) == [REWORDED_LIST]
    assert question.instructions == "Pick all the tools in the list that are relevant to the task at hand."
    written = rewordings[reworded_tool(two_correct, run_config.seed)]
    listed = reworded_order(two_correct, written, run_config.seed)
    assert item.lists[REWORDED_LIST] == listed and len(listed) == 5
    assert list(criteria_of(run_config, "G1_tool", listed)) == [tool.name for tool in listed]
    assert item.example.labels == [tool.name for tool in written]
    assert two_correct.labels == ["tool_1", "tool_3"]


def test_a_rotated_run_asks_the_rewordings_in_every_rotation_as_questions_of_one_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    one_correct = Example(id="set/G1_tool/0", query="Do one thing.", options=TOOLS[:3], labels=["tool_2"], raw={})
    written = [Option(name=f"tool_2_reworded_{number}", description=f"Said way {number}.") for number in range(1, 6)]
    (tmp_path / "rewordings.json").write_text(json.dumps({"tool_2": [tool.model_dump() for tool in written]}))
    monkeypatch.setitem(REWORDINGS_FILES, "stabletoolbench", tmp_path / "rewordings.json")
    (item,) = plan(config("rotated", "G1_tool", dataset="stabletoolbench"), {"G1_tool": [one_correct]}, TOOLS)
    (request,) = item.requests
    assert list(request.questions) == [f"rotated_{moved}" for moved in range(5)]
    assert {question.instructions for question in request.questions.values()} == {
        "Pick all the tools in the list that are relevant to the task at hand."
    }
    assert item.lists["rotated_0"] == written and item.lists["rotated_2"] == written[2:] + written[:2]
    assert item.example.labels == [tool.name for tool in written]


def test_a_copied_run_asks_five_copies_of_one_correct_tool_in_every_rotation() -> None:
    two_correct = Example(
        id="set/multi_tool/0", query="Do two things.", options=TOOLS[:4], labels=["tool_1", "tool_3"], raw={}
    )
    run_config = config("copied", "multi_tool")
    (item,) = plan(run_config, {"multi_tool": [two_correct]}, TOOLS)
    (request,) = item.requests
    assert list(request.questions) == [f"rotated_{moved}" for moved in range(5)]
    copies = item.lists["rotated_0"]
    original = reworded_tool(two_correct, run_config.seed)
    assert len({copy.name for copy in copies}) == 5 and {copy.name.strip() for copy in copies} == {original}
    assert {copy.description for copy in copies} == {f"Does thing {original.removeprefix('tool_')}."}
    assert item.lists["rotated_3"] == copies[3:] + copies[:3]
    assert item.example.labels == [copy.name for copy in copies]
    for question in request.questions.values():
        assert isinstance(question, jev.ChoiceQuestion) and sorted(question.criteria) == sorted(item.example.labels)


def test_an_absent_run_asks_wrong_tools_and_none_in_every_rotation_and_none_is_correct() -> None:
    one_correct = Example(id="set/similar_tools/0", query="Do one thing.", options=TOOLS, labels=["tool_2"], raw={})
    run_config = config("absent", "similar_tools")
    (item,) = plan(run_config, {"similar_tools": [one_correct]}, TOOLS)
    (request,) = item.requests
    assert list(request.questions) == [f"rotated_{moved}" for moved in range(5)]
    assert {question.instructions for question in request.questions.values()} == {ONE_TOOL_INSTRUCTIONS}
    places = []
    for name, question in request.questions.items():
        assert isinstance(question, jev.ChoiceQuestion)
        candidates = list(question.criteria)
        assert len(candidates) == 5 and candidates.count(NONE_NAME) == 1 and "tool_2" not in candidates
        assert candidates == [tool.name for tool in item.lists[name]]
        places.append(candidates.index(NONE_NAME) + 1)
    assert places == [5, 4, 3, 2, 1] and item.example.labels == []
    assert is_correct(run_config, "similar_tools", [], choice({"tool_1": 0.2, NONE_NAME: 0.8}))
    assert not is_correct(run_config, "similar_tools", [], choice({"tool_1": 0.8, NONE_NAME: 0.2}))


def test_a_dataset_whose_options_are_not_tools_has_its_own_instruction_and_none_candidate() -> None:
    question = Example(id="mmlu/test/0", query="What is 2 + 2?", options=CHOICES, labels=["4"], raw={})
    pool = [Option(name=f"choice {number}", description="") for number in range(20)]
    asked = "Choose the correct answer to the question."
    for experiment, entries in (("own", 4), ("copied", 5), ("unrelated", 5), ("absent_random", 5)):
        run_config = config(experiment, dataset="mmlu")
        (item,) = plan(run_config, {"test_standalone": [question]}, pool)
        (request,) = item.requests
        assert list(request.questions) == [f"rotated_{moved}" for moved in range(entries)]
        for question_sent in request.questions.values():
            assert isinstance(question_sent, jev.ChoiceQuestion) and question_sent.instructions == asked
            assert len(question_sent.criteria) == entries and set(question_sent.criteria.values()) == {None}
    own = plan(config("own", dataset="mmlu"), {"test_standalone": [question]}, pool)[0]
    assert own.lists["rotated_0"] == CHOICES and own.lists["rotated_1"] == CHOICES[1:] + CHOICES[:1]
    absent = plan(config("absent_random", dataset="mmlu"), {"test_standalone": [question]}, pool)[0]
    assert [tool.name for tool in absent.lists["rotated_0"]][-1] == "None of the above"
    none_config = config("absent_random", dataset="mmlu")
    assert is_correct(none_config, "test_standalone", [], choice({"choice 1": 0.2, "None of the above": 0.8}))
    assert not is_correct(none_config, "test_standalone", [], choice({"choice 1": 0.8, "None of the above": 0.2}))
    assert is_correct(config("own", dataset="mmlu"), "test_standalone", ["4"], choice({"3": 0.2, "4": 0.8}))


def test_a_list_of_rewordings_offers_no_none_and_every_entry_is_correct() -> None:
    rotated = config("rotated", "similar_tools")
    assert list(criteria_of(rotated, "similar_tools", TOOLS[:2])) == ["tool_1", "tool_2"]
    assert list(criteria_of(config(), "similar_tools", TOOLS[:2])) == ["tool_1", "tool_2", NONE_NAME]
    assert is_correct(rotated, "similar_tools", ["a", "b"], choice({"a": 0.2, "b": 0.8}))
    assert not is_correct(config(), "similar_tools", ["a"], choice({"a": 0.2, "b": 0.8}))


def test_every_tool_in_the_metatool_rewordings_file_has_five_rewordings_with_names_of_their_own() -> None:
    rewordings = read_rewordings(REWORDINGS_FILES["metatool"])
    names = [tool.name for tools in rewordings.values() for tool in tools]
    assert len(names) == len(set(names)) == 5 * len(rewordings) and not set(names) & set(rewordings)
    assert all(tool.description.strip() for tools in rewordings.values() for tool in tools)


def test_every_tool_in_the_stabletoolbench_rewordings_file_has_five_rewordings_with_its_category_and_tool() -> None:
    rewordings = read_rewordings(REWORDINGS_FILES["stabletoolbench"])
    for original, tools in rewordings.items():
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names)) == 5 and original not in names
        assert all(name.split(" / ")[:2] == original.split(" / ")[:2] for name in names)


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


def test_laya_gets_one_request_per_list_and_a_rejected_list_has_no_answer(
    fake: FakeJev, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_config = config("position", "similar_tools", model=LAYA_MODEL)
    (planned,) = plan(run_config, {"similar_tools": [example(0, ["tool_4"])]}, TOOLS)
    assert [list(request.questions) for request in planned.requests] == [
        [name] for name in [RELEASED_ORDER, *PLACEMENTS]
    ]
    accepted = fake.post

    def post(url: str, content: bytes, headers: dict[str, str], timeout: float) -> httpx.Response:
        if "last" in json.loads(content)["questions"]:
            return httpx.Response(422, json={"error": "too long"}, request=httpx.Request("POST", url))
        return accepted(url, content, headers, timeout)

    monkeypatch.setattr(jev.httpx, "post", post)
    (row,) = run(run_config, [planned])
    assert list(row.answers) == [name for name in [RELEASED_ORDER, *PLACEMENTS] if name != "last"]
    assert row.rejected == ["last"] and row.input_tokens == 10 * len(row.answers)
    assert jev.calls_saved() == 0


def test_a_refused_list_has_no_answer_and_is_named_in_the_row(fake: FakeJev, monkeypatch: pytest.MonkeyPatch) -> None:
    run_config = config("position", "similar_tools", model=LUNA_MODEL)
    planned = plan(run_config, {"similar_tools": [example(0, ["tool_4"])]}, TOOLS)
    accepted = fake.post

    def post(url: str, content: bytes, headers: dict[str, str], timeout: float) -> httpx.Response:
        payload = accepted(url, content, headers, timeout).json()
        payload["answers"]["middle"] = {"type": "refusal"}
        return httpx.Response(200, json=payload, request=httpx.Request("POST", url))

    monkeypatch.setattr(jev.httpx, "post", post)
    (row,) = run(run_config, planned)
    assert row.refused == ["middle"] and row.rejected == [] and "middle" not in row.answers
    assert len(row.answers) == len(PLACEMENTS)


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
    assert sampled(examples, None, seed=7) == examples
    sample = sampled(examples, 3, seed=7)
    assert len(sample) == 3 and sample == sampled(examples, 3, seed=7)
    assert [item.id for item in sample] == sorted(item.id for item in sample)
    assert sampled(examples, 50, seed=7) == examples
    assert set(item.id for item in sample) <= set(item.id for item in sampled(examples, 4, seed=7))


def test_a_total_number_of_examples_is_spread_over_the_test_files_and_the_first_files_get_one_more() -> None:
    files = ("a", "b", "c", "d", "e", "f")
    total = config("position", *files, examples=50)
    assert [sample_size(total, name) for name in files] == [9, 9, 8, 8, 8, 8]
    assert [sample_size(config("position", *files, examples_per_file=8), name) for name in files] == [8] * 6
    assert [sample_size(config("position", *files), name) for name in files] == [None] * 6


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


def test_fifty_stabletoolbench_queries_hold_the_eight_of_each_test_file(
    stabletoolbench: tuple[dict[str, list[Example]], list[Option]],
) -> None:
    fifty = plan(config("growth", dataset="stabletoolbench", examples=50), *stabletoolbench)
    eight_per_file = plan(config("growth", dataset="stabletoolbench", examples_per_file=8), *stabletoolbench)
    assert len(fifty) == 50
    assert {item.example.id for item in eight_per_file} < {item.example.id for item in fifty}


def test_fifty_reworded_stabletoolbench_lists_hold_only_the_five_rewordings_of_one_relevant_api(
    stabletoolbench: tuple[dict[str, list[Example]], list[Option]],
) -> None:
    examples, apis = stabletoolbench
    run_config = config("reworded", dataset="stabletoolbench", examples=50)
    planned = plan(run_config, examples, apis)
    growth = plan(config("growth", dataset="stabletoolbench", examples=50), examples, apis)
    rewordings = read_rewordings(REWORDINGS_FILES["stabletoolbench"])
    by_names = {frozenset(tool.name for tool in tools): original for original, tools in rewordings.items()}
    described = {api.name: bool(api.description.strip()) for api in apis}
    assert sum(count["calls"] for count in call_counts(run_config, planned).values()) == len(planned) == 50
    reworded = set()
    for item, grown in zip(planned, growth, strict=True):
        listed = item.lists[REWORDED_LIST]
        original = by_names[frozenset(tool.name for tool in listed)]
        reworded.add(original)
        assert item.example.id == grown.example.id and original in (grown.example.labels or [])
        assert len(listed) == 5 and item.example.labels == [tool.name for tool in rewordings[original]]
        # A rewording has no name of the dataset, and a description exactly when the API it rewords has one.
        assert all(tool.name not in described for tool in listed)
        assert all(bool(tool.description.strip()) == described[original] for tool in listed)
    # The 50 queries reword 45 different APIs, and the file holds no other.
    assert reworded == set(rewordings) and len(reworded) == 45


def test_fifty_rotated_stabletoolbench_queries_send_one_request_with_five_orders_each(
    stabletoolbench: tuple[dict[str, list[Example]], list[Option]],
) -> None:
    run_config = config("rotated", dataset="stabletoolbench", examples=50)
    planned = plan(run_config, *stabletoolbench)
    counts = call_counts(run_config, planned)
    assert sum(count["calls"] for count in counts.values()) == len(planned) == 50
    assert sum(count["questions"] for count in counts.values()) == 250
    rewordings = read_rewordings(REWORDINGS_FILES["stabletoolbench"])
    for item in planned:
        written = item.lists["rotated_0"]
        assert written in rewordings.values() and len(item.lists) == 5
        assert all(
            sorted(tool.name for tool in tools) == sorted(tool.name for tool in written)
            for tools in item.lists.values()
        )


def test_fifty_rotated_metatool_queries_send_five_rewordings_of_a_correct_tool_and_no_none(
    metatool: tuple[dict[str, list[Example]], list[Option]],
) -> None:
    examples, tools = metatool
    run_config = config("rotated", examples=50)
    planned = plan(run_config, examples, tools)
    counts = call_counts(run_config, planned)
    assert {name: count["examples"] for name, count in counts.items()} == {
        "similar_tools": 17,
        "scenario": 17,
        "multi_tool": 16,
    }
    assert sum(count["calls"] for count in counts.values()) == 50
    rewordings = read_rewordings(REWORDINGS_FILES["metatool"])
    by_names = {frozenset(tool.name for tool in written): original for original, written in rewordings.items()}
    known = {tool.name for tool in tools}
    correct = {example.id: example.labels or [] for own in examples.values() for example in own}
    reworded = set()
    for item in planned:
        original = by_names[frozenset(item.example.labels or [])]
        reworded.add(original)
        assert original in correct[item.example.id] and not set(item.example.labels or []) & known
        for request in item.requests:
            for question in request.questions.values():
                assert isinstance(question, jev.ChoiceQuestion) and len(question.criteria) == 5
                assert set(question.criteria) == set(item.example.labels or [])
    # The 50 queries reword 38 different tools, and the file holds no other.
    assert reworded == set(rewordings) and len(reworded) == 38


@pytest.mark.parametrize("dataset", ["metatool", "stabletoolbench"])
def test_fifty_copied_queries_send_one_request_with_five_copies_of_a_correct_tool(
    dataset: str, request: pytest.FixtureRequest
) -> None:
    examples, tools = request.getfixturevalue(dataset)
    run_config = config("copied", dataset=dataset, examples=50)
    planned = plan(run_config, examples, tools)
    counts = call_counts(run_config, planned)
    assert sum(count["calls"] for count in counts.values()) == len(planned) == 50
    assert sum(count["questions"] for count in counts.values()) == 250
    correct = {example.id: example.labels or [] for own in examples.values() for example in own}
    for item in planned:
        copies = item.lists["rotated_0"]
        (original,) = {tuple(copy.name.split()) for copy in copies}
        assert len({copy.name for copy in copies}) == 5 and len({copy.description for copy in copies}) == 1
        assert original in {tuple(label.split()) for label in correct[item.example.id]}
        for question in item.requests[0].questions.values():
            assert isinstance(question, jev.ChoiceQuestion) and len(question.criteria) == 5


def test_fifty_absent_metatool_queries_send_four_similar_tools_and_none_without_the_correct_tool(
    metatool: tuple[dict[str, list[Example]], list[Option]],
) -> None:
    examples, tools = metatool
    run_config = config("absent", examples=50)
    planned = plan(run_config, examples, tools)
    counts = call_counts(run_config, planned)
    assert counts["similar_tools"]["examples"] == counts["similar_tools"]["calls"] == 50
    assert counts["similar_tools"]["questions"] == 250
    released = {example.id: example for example in examples["similar_tools"]}
    for item in planned:
        own = released[item.example.id]
        for listed in item.lists.values():
            names = [tool.name for tool in listed]
            assert len(names) == 5 and names.count(NONE_NAME) == 1 and not set(names) & set(own.labels or [])
            assert set(names) - {NONE_NAME} < {option.name for option in own.options}


def test_fifty_absent_random_metatool_queries_send_four_tools_from_outside_their_list_and_none(
    metatool: tuple[dict[str, list[Example]], list[Option]],
) -> None:
    examples, tools = metatool
    run_config = config("absent_random", examples=50)
    planned = plan(run_config, examples, tools)
    similar = {item.example.id for item in plan(config("absent", examples=50), examples, tools)}
    assert {item.example.id for item in planned} == similar
    assert sum(count["calls"] for count in call_counts(run_config, planned).values()) == 50
    released = {example.id: example for example in examples["similar_tools"]}
    known = {tool.name for tool in tools}
    for item in planned:
        own = {option.name for option in released[item.example.id].options}
        for listed in item.lists.values():
            names = [tool.name for tool in listed]
            assert len(names) == 5 and names.count(NONE_NAME) == 1 and item.example.labels == []
            assert not set(names) & own and set(names) - {NONE_NAME} < known


def test_fifty_unrelated_metatool_queries_send_five_tools_from_outside_their_list_and_no_none(
    metatool: tuple[dict[str, list[Example]], list[Option]],
) -> None:
    examples, tools = metatool
    run_config = config("unrelated", examples=50)
    planned = plan(run_config, examples, tools)
    copied = plan(config("copied", examples=50), examples, tools)
    assert [item.example.id for item in planned] == [item.example.id for item in copied]
    assert sum(count["calls"] for count in call_counts(run_config, planned).values()) == 50
    released = {example.id: example for own in examples.values() for example in own}
    for item in planned:
        own = {option.name for option in released[item.example.id].options}
        assert item.example.labels == [] and list(item.lists) == [f"rotated_{moved}" for moved in range(5)]
        for listed in item.lists.values():
            names = [tool.name for tool in listed]
            assert len(set(names)) == 5 and NONE_NAME not in names and not set(names) & own
            assert list(criteria_of(run_config, item.test_file, listed)) == names
            assert not is_correct(run_config, item.test_file, [], choice(dict.fromkeys(names, 0.2)))
            assert not is_correct(
                run_config, item.test_file, [], choice({names[0]: 0.6} | dict.fromkeys(names[1:], 0.1))
            )


@pytest.fixture(scope="module")
def mmlu() -> tuple[dict[str, list[Example]], list[Option]]:
    """The standalone questions of the processed MMLU test file, and the list of their choices."""
    folder = PROCESSED_DIRS["mmlu"]
    test_files = EXPERIMENT_TEST_FILES["own"]["mmlu"]
    if not all((folder / f"{name}.jsonl").exists() for name in test_files):
        pytest.skip("MMLU is not processed")
    return read_dataset(folder, test_files)


@pytest.mark.parametrize(
    ("experiment", "entries"), [("own", 4), ("copied", 5), ("unrelated", 5), ("absent_random", 5), ("absent", 4)]
)
def test_fifty_mmlu_questions_send_one_request_with_every_rotation(
    experiment: str, entries: int, mmlu: tuple[dict[str, list[Example]], list[Option]]
) -> None:
    examples, choices = mmlu
    run_config = config(experiment, dataset="mmlu", examples=50)
    planned = plan(run_config, examples, choices)
    own = plan(config("own", dataset="mmlu", examples=50), examples, choices)
    assert [item.example.id for item in planned] == [item.example.id for item in own] and len(planned) == 50
    counts = call_counts(run_config, planned)
    assert sum(count["calls"] for count in counts.values()) == 50
    assert sum(count["questions"] for count in counts.values()) == 50 * entries
    for item, question in zip(planned, own, strict=True):
        released = [option.name for option in question.example.options]
        for listed in item.lists.values():
            names = [tool.name for tool in listed]
            assert len(set(names)) == entries
            if experiment == "own":
                assert sorted(names) == sorted(released)
            elif experiment == "copied":
                (correct,) = question.example.labels or []
                assert {" ".join(name.split()) for name in names} == {" ".join(correct.split())}
            elif experiment == "absent":
                (correct,) = question.example.labels or []
                assert sorted(names) == sorted(
                    [*(choice for choice in released if choice != correct), "None of the above"]
                )
            else:
                assert not set(names) & set(released)
                assert ("None of the above" in names) == (experiment == "absent_random")
