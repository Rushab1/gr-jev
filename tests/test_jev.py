"""Tests for grjev.jev. httpx.post is replaced, so nothing reaches the Jev API."""

import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from grjev import jev
from grjev.constants import D1_MODEL, GATEWAY_URL, LAYA_MODEL
from grjev.store import run_path

KEY = "test-key"
GATEWAY_KEY = "gateway-key"
ANSWER = {
    "model": "jev-1.13.0",
    "answers": {"tool": {"type": "choice", "choice": "a", "probabilities": {"a": 0.9, "b": 0.1}, "confidence": 0.8}},
    "usage": {"input_tokens": 30, "output_tokens": 5},
}


class FakeJev:
    """Stands in for httpx.post: records each call and replies with the queued status codes, then with 200."""

    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []
        self.urls: list[str] = []
        self.statuses: list[int] = []

    def post(self, url: str, content: bytes, headers: dict[str, str], timeout: float) -> httpx.Response:
        self.calls.append(headers)
        self.urls.append(url)
        status = self.statuses.pop(0) if self.statuses else 200
        payload = ANSWER if status == 200 else {"error": "refused"}
        return httpx.Response(status, json=payload, request=httpx.Request("POST", url))


@pytest.fixture
def fake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FakeJev:
    """Replace the API, point the cache at a temporary folder, set a key, and skip the backoff sleeps."""
    fake_jev = FakeJev()
    monkeypatch.setattr(jev.httpx, "post", fake_jev.post)
    monkeypatch.setattr(jev, "JEV_CACHE_DIR", tmp_path)
    monkeypatch.setattr(jev, "GATEWAY_CACHE_DIR", tmp_path / "gateway")
    monkeypatch.setattr(jev.time, "sleep", lambda seconds: None)
    monkeypatch.setenv(jev.JEV_KEY_ENV, KEY)
    monkeypatch.setenv(jev.GATEWAY_KEY_ENV, GATEWAY_KEY)
    return fake_jev


def request(options: dict[str, str | None]) -> jev.JevRequest:
    question = jev.ChoiceQuestion(instructions="Which tool handles the query?", criteria=options)
    return jev.JevRequest(state="Find a flight to Paris.", questions={"tool": question})


def test_option_order_changes_the_request_and_its_path() -> None:
    forward = jev.request_body(request({"a": "first", "b": "second"}))
    reverse = jev.request_body(request({"b": "second", "a": "first"}))
    assert forward != reverse
    assert run_path(Path("cache"), forward, 1) != run_path(Path("cache"), reverse, 1)


def test_ask_saves_the_response_and_reads_it_back_without_a_second_call(fake: FakeJev) -> None:
    first = jev.ask(request({"a": None, "b": None}))
    second = jev.ask(request({"a": None, "b": None}))
    assert first is not None and first == second
    assert first.answers["tool"].type == "choice" and first.usage.input_tokens == 30
    assert len(fake.calls) == 1


def test_a_new_run_number_is_a_new_call_saved_separately(fake: FakeJev, tmp_path: Path) -> None:
    jev.ask(request({"a": None, "b": None}), run=1)
    jev.ask(request({"a": None, "b": None}), run=2)
    assert len(fake.calls) == 2
    assert sorted(path.name for path in tmp_path.rglob("run-*.json")) == ["run-1.json", "run-2.json"]


def test_the_key_goes_in_the_header_and_is_not_saved(fake: FakeJev, tmp_path: Path) -> None:
    jev.ask(request({"a": None, "b": None}))
    assert fake.calls[0]["Authorization"] == f"Bearer {KEY}"
    saved = next(tmp_path.rglob("run-1.json")).read_text()
    assert KEY not in saved
    assert json.loads(saved)["request"]["questions"]["tool"]["criteria"] == {"a": None, "b": None}


def test_post_retries_while_jev_is_overloaded(fake: FakeJev) -> None:
    fake.statuses = [529, 429]
    assert jev.post(b"{}") == ANSWER
    assert len(fake.calls) == 3


def test_an_error_status_raises_and_saves_nothing(fake: FakeJev, tmp_path: Path) -> None:
    fake.statuses = [401]
    with pytest.raises(RuntimeError, match="jev-1.13.0 returned 401"):
        jev.ask(request({"a": None, "b": None}))
    assert list(tmp_path.rglob("*.json")) == []


def test_a_response_of_an_unexpected_shape_raises_and_saves_nothing(
    fake: FakeJev, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(jev, "post", lambda body, model: {"unexpected": True})
    with pytest.raises(ValidationError):
        jev.ask(request({"a": None, "b": None}))
    assert list(tmp_path.rglob("*.json")) == []


def test_a_gateway_model_is_asked_at_the_gateway_with_its_key_and_saved_outside_the_jev_folder(
    fake: FakeJev, tmp_path: Path
) -> None:
    question = jev.ChoiceQuestion(instructions="Which tool handles the query?", criteria={"a": None, "b": None})
    jev.ask(jev.JevRequest(state="Find a flight.", model=D1_MODEL, questions={"tool": question}))
    assert fake.urls == [GATEWAY_URL] and fake.calls[0]["Authorization"] == f"Bearer {GATEWAY_KEY}"
    assert len(list((tmp_path / "gateway" / D1_MODEL).rglob("run-1.json"))) == 1
    jev.check_call_limit(10**9, D1_MODEL)


def test_a_list_that_laya_rejects_is_saved_as_rejected_and_not_asked_again(fake: FakeJev, tmp_path: Path) -> None:
    question = jev.ChoiceQuestion(instructions="Which tool handles the query?", criteria={"a": None, "b": None})
    asked = jev.JevRequest(state="Find a flight.", model=LAYA_MODEL, questions={"tool": question})
    fake.statuses = [422]
    assert jev.ask(asked) is None and jev.ask(asked) is None
    assert len(fake.calls) == 1
    assert json.loads(next((tmp_path / "gateway").rglob("run-1.json")).read_text())["response"]["rejected"] == 422


def test_a_rejection_of_a_model_that_takes_whole_requests_raises(fake: FakeJev) -> None:
    question = jev.ChoiceQuestion(instructions="Which tool handles the query?", criteria={"a": None, "b": None})
    fake.statuses = [422]
    with pytest.raises(RuntimeError, match="returned 422"):
        jev.ask(jev.JevRequest(state="Find a flight.", model=D1_MODEL, questions={"tool": question}))


def test_a_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(jev.JEV_KEY_ENV, raising=False)
    with pytest.raises(RuntimeError, match=jev.JEV_KEY_ENV):
        jev.api_key()


def test_a_choice_with_more_than_255_options_is_rejected() -> None:
    with pytest.raises(ValidationError):
        request({f"tool_{n}": None for n in range(jev.JEV_MAX_OPTIONS + 1)})
