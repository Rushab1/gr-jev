"""Saved model responses: one file per request hash and run number, so a rerun reads the file and calls nothing."""

import hashlib
import itertools
import json
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any


def run_path(root: Path, request: bytes, run: int) -> Path:
    """Return where the record for these request bytes and this run number is saved under root."""
    return root / hashlib.sha256(request).hexdigest() / f"run-{run}.json"


def next_run(root: Path, request: bytes) -> int:
    """Return the lowest run number that has no record saved under root for these request bytes."""
    return next(run for run in itertools.count(1) if not run_path(root, request, run).exists())


# One lock per record path, so two threads that want the same record compute it once.
PATH_LOCKS: dict[Path, threading.Lock] = {}
PATH_LOCKS_GUARD = threading.Lock()


def load_or_compute(path: Path, compute: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """Return the record saved at path. If there is none, compute it and save it first.

    A thread that asks for a record while another thread of the process computes it waits and reads the saved file.
    """
    with PATH_LOCKS_GUARD:
        lock = PATH_LOCKS.setdefault(path, threading.Lock())
    with lock:
        if not path.exists():
            record = compute()
            path.parent.mkdir(parents=True, exist_ok=True)
            # Each writer gets its own temporary file, so two processes that write the same record cannot collide.
            with tempfile.NamedTemporaryFile("w", dir=path.parent, suffix=".part", delete=False) as partial:
                partial.write(json.dumps(record, ensure_ascii=False, indent=1))
            Path(partial.name).replace(path)
    return json.loads(path.read_text())
