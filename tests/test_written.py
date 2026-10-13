"""Tests for grjev.written and for the requests in src/grjev/stimuli/requests/."""

import pytest

from grjev.constants import JEV_MODEL, WRITTEN_REQUESTS_DIR
from grjev.jev import ChoiceQuestion
from grjev.written import read_written


@pytest.mark.parametrize("name", sorted(path.stem for path in WRITTEN_REQUESTS_DIR.glob("*.json")))
def test_every_written_request_is_a_request_for_the_model(name: str) -> None:
    request = read_written(WRITTEN_REQUESTS_DIR / f"{name}.json", JEV_MODEL)
    assert request.model == JEV_MODEL and request.state and request.questions


def test_the_john_and_jane_request_holds_the_10_passages_and_the_two_lists_without_one_of_them() -> None:
    request = read_written(WRITTEN_REQUESTS_DIR / "john_jane.json", JEV_MODEL)
    full, without_john, without_jane = (request.questions[name] for name in ("full", "without_john", "without_jane"))
    assert isinstance(full, ChoiceQuestion) and isinstance(without_john, ChoiceQuestion)
    assert isinstance(without_jane, ChoiceQuestion)
    assert request.state == "who is older, Jane or John?" and len(full.criteria) == 10
    assert list(without_john.criteria) == [name for name in full.criteria if name != "John"]
    assert list(without_jane.criteria) == [name for name in full.criteria if name != "Jane"]
    text = request.model_dump_json()
    assert not any(name in text for name in ("Rubin", "Sharapova", "Chanda", "Maria"))
    assert "John (born February 18, 1976)" in (full.criteria["John"] or "")
    assert "Jane (born April 19, 1987)" in (full.criteria["Jane"] or "")
