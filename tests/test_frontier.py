"""Tests for grjev.frontier. subprocess.run is replaced, so the Claude Code CLI is never started."""

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from grjev import frontier

SYSTEM = "You select tools. Reply with the tool name only."
PROMPT = "Query: weather in Paris?\nTools:\n1. get_weather\n2. send_email"
USAGE = {
    "input_tokens": 2,
    "cache_creation_input_tokens": 500,
    "cache_read_input_tokens": 30,
    "output_tokens": 6,
    "output_tokens_details": {"thinking_tokens": 0},
}
STDOUT = json.dumps({"type": "result", "is_error": False, "result": "get_weather", "usage": USAGE})


class FakeCli:
    """Stands in for subprocess.run: answers the version check and records every model call."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.version = f"{frontier.CLAUDE_CLI_VERSION} (Claude Code)"
        self.exit_code = 0

    def run(self, argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if argv[1] == "--version":
            return subprocess.CompletedProcess(argv, 0, stdout=self.version, stderr="")
        self.calls.append({"argv": argv, **kwargs})
        return subprocess.CompletedProcess(argv, self.exit_code, stdout=STDOUT, stderr="refused")


@pytest.fixture
def cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FakeCli:
    """Replace the CLI and point the cache and the working folder at temporary folders."""
    fake = FakeCli()
    frontier.installed_version.cache_clear()
    monkeypatch.setattr(frontier.subprocess, "run", fake.run)
    monkeypatch.setattr(frontier, "CLAUDE_CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(frontier, "CLAUDE_WORK_DIR", tmp_path / "work")
    monkeypatch.setenv("CLAUDECODE", "1")
    return fake


def test_ask_claude_returns_the_answer_and_counts_all_input_tokens(cli: FakeCli) -> None:
    response = frontier.ask_claude("claude-sonnet-5", SYSTEM, PROMPT)
    assert response.answer == "get_weather"
    assert (response.input_tokens, response.output_tokens, response.thinking_tokens) == (532, 6, 0)


def test_claude_is_called_with_no_tools_no_thinking_and_no_saved_session(cli: FakeCli) -> None:
    frontier.ask_claude("claude-sonnet-5", SYSTEM, PROMPT)
    call = cli.calls[0]
    assert call["argv"][-4:] == ["--model", "claude-sonnet-5", "--system-prompt", SYSTEM]
    assert "--no-session-persistence" in call["argv"] and call["argv"][call["argv"].index("--tools") + 1] == ""
    assert call["input"] == PROMPT and call["timeout"] == frontier.CLAUDE_TIMEOUT_SECONDS
    assert call["env"]["MAX_THINKING_TOKENS"] == "0" and "CLAUDECODE" not in call["env"]


def test_a_saved_run_is_read_back_and_a_new_run_number_calls_again(cli: FakeCli) -> None:
    first = frontier.ask_claude("claude-sonnet-5", SYSTEM, PROMPT)
    assert frontier.ask_claude("claude-sonnet-5", SYSTEM, PROMPT) == first
    assert len(cli.calls) == 1
    frontier.ask_claude("claude-sonnet-5", SYSTEM, PROMPT, run=2)
    assert len(cli.calls) == 2


def test_the_hash_covers_the_model_the_system_prompt_and_the_prompt(cli: FakeCli) -> None:
    frontier.ask_claude("claude-sonnet-5", SYSTEM, PROMPT)
    frontier.ask_claude("claude-opus-5", SYSTEM, PROMPT)
    frontier.ask_claude("claude-sonnet-5", SYSTEM + " Be brief.", PROMPT)
    frontier.ask_claude("claude-sonnet-5", SYSTEM, PROMPT + "\n3. search_flights")
    assert len(cli.calls) == 4


def test_a_failed_call_raises_and_saves_nothing(cli: FakeCli, tmp_path: Path) -> None:
    cli.exit_code = 1
    with pytest.raises(RuntimeError, match="claude exited with 1"):
        frontier.ask_claude("claude-sonnet-5", SYSTEM, PROMPT)
    assert list(tmp_path.rglob("run-*.json")) == []


def test_a_different_cli_version_is_refused(cli: FakeCli) -> None:
    cli.version = "2.2.0 (Claude Code)"
    with pytest.raises(RuntimeError, match="pinned to"):
        frontier.ask_claude("claude-sonnet-5", SYSTEM, PROMPT)
    assert cli.calls == []
