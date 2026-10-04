"""Saved model responses: one file per request hash and run number, so a rerun reads the file and calls nothing."""

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any


def run_path(root: Path, request: bytes, run: int) -> Path:
    """Return where the record for these request bytes and this run number is saved under root."""
    return root / hashlib.sha256(request).hexdigest() / f"run-{run}.json"


def load_or_compute(path: Path, compute: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """Return the record saved at path. If there is none, compute it and save it first."""
    if not path.exists():
        record = compute()
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_suffix(".part")
        partial.write_text(json.dumps(record, ensure_ascii=False, indent=1))
        partial.replace(path)
    return json.loads(path.read_text())
