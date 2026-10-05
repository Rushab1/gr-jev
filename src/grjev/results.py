"""The folder of one run under results/: its config, the commit and model it ran with, and one row per example."""

import json
import subprocess
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from grjev.constants import REPO_ROOT, RESULTS_DIR
from grjev.examples import write_jsonl


def new_results_dir(name: str, day: date) -> Path:
    """Create and return the next folder results/<name>/<date>_<incr>/ of that day."""
    parent = RESULTS_DIR / name
    taken = len(list(parent.glob(f"{day.isoformat()}_*")))
    folder = parent / f"{day.isoformat()}_{taken + 1:02d}"
    folder.mkdir(parents=True)
    return folder


def git(*arguments: str) -> str:
    """Return the output of a git command run in the repository."""
    return subprocess.run(["git", *arguments], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()


def git_state() -> dict[str, Any]:
    """Return the commit the code is at, and whether files differ from it."""
    return {"git_commit": git("rev-parse", "HEAD"), "git_dirty": bool(git("status", "--porcelain"))}


def write_run(folder: Path, config: BaseModel, meta: dict[str, Any], rows: Iterable[BaseModel]) -> None:
    """Write config.json, meta.json and rows.jsonl, with one row per example, into the folder of a run."""
    (folder / "config.json").write_text(config.model_dump_json(indent=1) + "\n")
    (folder / "meta.json").write_text(json.dumps(meta, indent=1) + "\n")
    write_jsonl(folder / "rows.jsonl", rows)
