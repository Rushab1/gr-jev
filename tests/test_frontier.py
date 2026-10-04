"""Tests for the parts of grjev.frontier that run without the CLI. test_frontier_live.py has the tests that call it."""

import json

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


def result_line(**changed: object) -> str:
    """Return one line of CLI output: a result object, with the given fields changed."""
    return json.dumps({"type": "result", "is_error": False, "result": "get_weather", "usage": USAGE, **changed})


def test_parse_response_returns_the_answer_and_counts_all_input_tokens() -> None:
    response = frontier.parse_response(result_line(), 2.5)
    assert (response.answer, response.seconds) == ("get_weather", 2.5)
    assert (response.input_tokens, response.output_tokens, response.thinking_tokens) == (532, 6, 0)


@pytest.mark.parametrize("stdout", [result_line(is_error=True), "Not logged in", ""])
def test_parse_response_refuses_an_error_and_output_without_a_result(stdout: str) -> None:
    with pytest.raises(RuntimeError, match="no usable result"):
        frontier.parse_response(stdout, 1.0)


def test_the_cli_gets_only_the_listed_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("CLAUDECODE", "CLAUDE_CODE_EFFORT_LEVEL", "ANTHROPIC_BASE_URL"):
        monkeypatch.setenv(name, "1")
    monkeypatch.setenv("MAX_THINKING_TOKENS", "31999")
    monkeypatch.setenv("HOME", "/home/tester")
    env = frontier.child_environment()
    assert set(env) <= {*frontier.CLAUDE_INHERITED_VARS, *frontier.CLAUDE_ENV}
    assert (env["HOME"], env["MAX_THINKING_TOKENS"]) == ("/home/tester", "0")


def test_the_hashed_request_holds_everything_we_control() -> None:
    assert json.loads(frontier.request_bytes("claude-sonnet-5", SYSTEM, PROMPT)) == {
        "cli_version": frontier.CLAUDE_CLI_VERSION,
        "args": list(frontier.CLAUDE_ARGS),
        "env": frontier.CLAUDE_ENV,
        "work_dir": str(frontier.CLAUDE_WORK_DIR),
        "model": "claude-sonnet-5",
        "system": SYSTEM,
        "prompt": PROMPT,
    }
