"""Tests for grjev.written and for the requests in scripts/run/requests/."""

import pytest

from grjev.constants import JEV_MODEL, WRITTEN_REQUESTS_DIR
from grjev.jev import ChoiceQuestion
from grjev.written import read_written, request_latex, typeset


@pytest.mark.parametrize("name", sorted(path.stem for path in WRITTEN_REQUESTS_DIR.glob("*.json")))
def test_every_written_request_is_a_request_for_the_model(name: str) -> None:
    request = read_written(WRITTEN_REQUESTS_DIR / f"{name}.json", JEV_MODEL)
    assert request.model == JEV_MODEL and request.state and request.questions


REAL_NAMES = ("Rubin", "Sharapova", "Chanda", "Maria", "WTA", "Wimbledon", "Russia", "Linz", "Olympic")


@pytest.mark.parametrize(
    ("name", "state"),
    [("john_jane", "who is older, Jane or John?"), ("john_jane_younger", "who is younger, Jane or John?")],
)
def test_a_john_and_jane_request_holds_the_10_invented_passages_and_the_two_lists_without_one(
    name: str, state: str
) -> None:
    request = read_written(WRITTEN_REQUESTS_DIR / f"{name}.json", JEV_MODEL)
    full, without_john, without_jane = (request.questions[name] for name in ("full", "without_john", "without_jane"))
    assert isinstance(full, ChoiceQuestion) and isinstance(without_john, ChoiceQuestion)
    assert isinstance(without_jane, ChoiceQuestion)
    assert request.state == state and len(full.criteria) == 10
    assert list(without_john.criteria) == [name for name in full.criteria if name != "John"]
    assert list(without_jane.criteria) == [name for name in full.criteria if name != "Jane"]
    assert not any(name in request.model_dump_json() for name in REAL_NAMES)
    assert "John (born December 12, 1976)" in (full.criteria["John"] or "")
    assert "Jane (born January 13, 1990)" in (full.criteria["Jane"] or "")
    for shorter in (without_john, without_jane):
        assert all(text == full.criteria[title] for title, text in shorter.criteria.items())


def test_the_two_john_and_jane_requests_differ_only_in_the_question() -> None:
    older = read_written(WRITTEN_REQUESTS_DIR / "john_jane.json", JEV_MODEL)
    younger = read_written(WRITTEN_REQUESTS_DIR / "john_jane_younger.json", JEV_MODEL)
    assert older.questions == younger.questions and older.state != younger.state


def test_the_table_of_two_requests_holds_both_questions_the_instruction_and_the_10_passages() -> None:
    older = read_written(WRITTEN_REQUESTS_DIR / "john_jane.json", JEV_MODEL)
    younger = read_written(WRITTEN_REQUESTS_DIR / "john_jane_younger.json", JEV_MODEL)
    lines = request_latex([older, younger]).splitlines()
    assert lines[2:5] == [
        "Question & who is older, Jane or John? \\\\",
        "Question & who is younger, Jane or John? \\\\",
        "Instruction & Choose every passage in the list that supports the answer to the question. \\\\",
    ]
    assert sum(line.endswith("\\\\") for line in lines) == 3 + 1 + 10
    assert any(line.startswith("John & John (born December 12, 1976)") for line in lines)
    short = request_latex([older, younger], ["John", "Jane"]).splitlines()
    assert sum(line.endswith("\\\\") for line in short) == 3 + 1 + 2
    changed = older.model_copy(update={"questions": {"full": older.questions["without_john"]}})
    with pytest.raises(ValueError, match="same lists"):
        request_latex([older, changed])


def test_a_table_shows_cyrillic_words_as_an_ellipsis_and_escapes_commands() -> None:
    assert typeset("Sharapova (Russian: Мари́я Ю́рьевна Шара́пова ; born 1987) & co") == (
        "Sharapova (Russian: [...] ; born 1987) \\& co"
    )
    assert typeset("1997 Open – Sánchez") == "1997 Open -- S\\'{a}nchez"
    with pytest.raises(ValueError, match="no LaTeX"):
        typeset("日本")


def test_the_released_question_holds_the_passages_of_hotpotqa_unchanged() -> None:
    request = read_written(WRITTEN_REQUESTS_DIR / "sharapova_rubin.json", JEV_MODEL)
    full = request.questions["full"]
    assert isinstance(full, ChoiceQuestion) and len(full.criteria) == 10
    assert request.state == "who is older, Maria Sharapova or Chanda Rubin?"
    assert (full.criteria["Chanda Rubin"] or "").startswith("Chanda Rubin (born February 18, 1976)")
