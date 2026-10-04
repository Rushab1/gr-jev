"""Tests of grjev.frontier that call the live Claude Code CLI with this machine's sign-in.

A plain `pytest` run leaves them out. Run them with `pytest -m integration`.
"""

from pathlib import Path

import pytest

from grjev import frontier
from grjev.constants import CLAUDE_CLI_VERSION, CLAUDE_MODELS

pytestmark = pytest.mark.integration

SYSTEM = "You select tools. Reply with the tool name only."
PROMPT = "Query: weather in Paris?\nTools:\n1. get_weather\n2. send_email"
# A call with Claude Code's own system prompt and tools sends about 29,000 input tokens.
MAX_INPUT_TOKENS = 2000


@pytest.fixture(autouse=True)
def cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Save responses in an empty folder, so every test makes its own calls and none reaches data/cache."""
    monkeypatch.setattr(frontier, "CLAUDE_CACHE_DIR", tmp_path)
    return tmp_path


def saved_runs(cache: Path) -> list[str]:
    """Return the names of the saved run files."""
    return sorted(path.name for path in cache.rglob("run-*.json"))


def test_the_pinned_cli_version_is_installed() -> None:
    assert frontier.installed_version() == CLAUDE_CLI_VERSION


@pytest.mark.parametrize("model", CLAUDE_MODELS)
def test_a_model_answers_without_thinking_tools_or_the_default_system_prompt(model: str) -> None:
    response = frontier.ask_claude(model, SYSTEM, PROMPT)
    assert "get_weather" in response.answer
    assert response.thinking_tokens == 0
    assert response.input_tokens < MAX_INPUT_TOKENS


def test_variables_outside_the_list_do_not_reach_the_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://example.invalid")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "not-a-key")
    monkeypatch.setenv("CLAUDE_CODE_EFFORT_LEVEL", "max")
    monkeypatch.setenv("MAX_THINKING_TOKENS", "31999")
    response = frontier.ask_claude(CLAUDE_MODELS[0], SYSTEM, PROMPT)
    assert "get_weather" in response.answer
    assert response.thinking_tokens == 0


def test_a_saved_run_is_read_back_and_a_new_run_number_calls_again(cache: Path) -> None:
    first = frontier.ask_claude(CLAUDE_MODELS[0], SYSTEM, PROMPT)
    written = [path.stat().st_mtime_ns for path in cache.rglob("run-*.json")]
    assert frontier.ask_claude(CLAUDE_MODELS[0], SYSTEM, PROMPT) == first
    assert [path.stat().st_mtime_ns for path in cache.rglob("run-*.json")] == written
    frontier.ask_claude(CLAUDE_MODELS[0], SYSTEM, PROMPT, run=2)
    assert saved_runs(cache) == ["run-1.json", "run-2.json"]


def test_no_session_file_is_written() -> None:
    sessions = f"*{frontier.CLAUDE_WORK_DIR.name}/*.jsonl"
    before = set((Path.home() / ".claude" / "projects").glob(sessions))
    frontier.ask_claude(CLAUDE_MODELS[0], SYSTEM, PROMPT)
    assert set((Path.home() / ".claude" / "projects").glob(sessions)) == before


def test_a_failed_call_raises_and_saves_nothing(cache: Path) -> None:
    with pytest.raises(RuntimeError):
        frontier.ask_claude("claude-no-such-model", SYSTEM, PROMPT)
    assert saved_runs(cache) == []


def test_a_different_cli_version_is_refused(cache: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(frontier, "CLAUDE_CLI_VERSION", "0.0.0")
    with pytest.raises(RuntimeError, match="pinned to"):
        frontier.ask_claude(CLAUDE_MODELS[0], SYSTEM, PROMPT)
    assert saved_runs(cache) == []
