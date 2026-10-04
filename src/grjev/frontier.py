"""Bridge to Claude models through the Claude Code CLI: one prompt in, one answer out, no tools and no thinking."""

import functools
import json
import os
import re
import subprocess
import time
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from grjev.constants import (
    CLAUDE_ARGS,
    CLAUDE_CACHE_DIR,
    CLAUDE_CLI_VERSION,
    CLAUDE_ENV,
    CLAUDE_INHERITED_VARS,
    CLAUDE_TIMEOUT_SECONDS,
    CLAUDE_WORK_DIR,
)
from grjev.store import load_or_compute, run_path


class FrontierResponse(BaseModel):
    """The answer of one CLI call. `output_tokens` includes `thinking_tokens`."""

    answer: str
    input_tokens: int
    output_tokens: int
    thinking_tokens: int
    seconds: float


@functools.cache
def installed_version() -> str:
    """Return the version number printed by `claude --version`."""
    command = ["claude", "--version"]
    output = subprocess.run(command, capture_output=True, text=True, check=True, env=child_environment()).stdout
    match = re.search(r"\d+\.\d+\.\d+", output)
    if match is None:
        raise RuntimeError(f"No version number in the output of claude --version: {output!r}")
    return match.group(0)


def child_environment() -> dict[str, str]:
    """Return the whole environment of a CLI call: the few variables it needs from ours, and thinking switched off."""
    inherited = {name: os.environ[name] for name in CLAUDE_INHERITED_VARS if name in os.environ}
    return {**inherited, **CLAUDE_ENV}


def run_claude(model: str, system: str, prompt: str) -> dict[str, Any]:
    """Run one CLI call with the prompt on stdin. Return its stdout, the seconds it took and when it was made."""
    if installed_version() != CLAUDE_CLI_VERSION:
        raise RuntimeError(f"claude is version {installed_version()}, but results are pinned to {CLAUDE_CLI_VERSION}")
    CLAUDE_WORK_DIR.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    completed = subprocess.run(
        ["claude", *CLAUDE_ARGS, "--model", model, "--system-prompt", system],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=CLAUDE_TIMEOUT_SECONDS,
        env=child_environment(),
        cwd=CLAUDE_WORK_DIR,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"claude exited with {completed.returncode}: {completed.stderr[-500:]}")
    called_at = datetime.now(UTC).isoformat(timespec="seconds")
    return {"stdout": completed.stdout, "seconds": round(time.perf_counter() - start, 3), "called_at": called_at}


def parse_response(stdout: str, seconds: float) -> FrontierResponse:
    """Read the result object printed by `claude -p --output-format json`."""
    events = (json.loads(line) for line in stdout.splitlines() if line.startswith("{"))
    result = next((event for event in events if event.get("type") == "result"), None)
    if result is None or result["is_error"]:
        raise RuntimeError(f"claude returned no usable result: {stdout[-500:]}")
    usage = result["usage"]
    return FrontierResponse(
        answer=result["result"],
        input_tokens=usage["input_tokens"] + usage["cache_creation_input_tokens"] + usage["cache_read_input_tokens"],
        output_tokens=usage["output_tokens"],
        thinking_tokens=usage["output_tokens_details"]["thinking_tokens"],
        seconds=seconds,
    )


def request_bytes(model: str, system: str, prompt: str) -> bytes:
    """Return the bytes that identify a call: everything we control that can change the answer."""
    request = {
        "cli_version": CLAUDE_CLI_VERSION,
        "args": CLAUDE_ARGS,
        "env": CLAUDE_ENV,
        "work_dir": str(CLAUDE_WORK_DIR),
        "model": model,
        "system": system,
        "prompt": prompt,
    }
    return json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode()


def ask_claude(model: str, system: str, prompt: str, run: int = 1) -> FrontierResponse:
    """Return Claude's answer for this request and run number. The CLI is called only if that run is not saved."""
    request = request_bytes(model, system, prompt)

    def call() -> dict[str, Any]:
        output = run_claude(model, system, prompt)
        parse_response(output["stdout"], output["seconds"])
        return {"request": json.loads(request), "run": run, **output}

    record = load_or_compute(run_path(CLAUDE_CACHE_DIR / model, request, run), call)
    return parse_response(record["stdout"], record["seconds"])
