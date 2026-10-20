"""Tests for grjev.store."""

import contextlib
import json
import threading
from pathlib import Path
from typing import Any

from grjev.store import load_or_compute, next_run, run_path


def test_a_saved_record_is_read_back_without_computing_again(tmp_path: Path) -> None:
    path = run_path(tmp_path, b"request", 1)
    calls: list[int] = []

    def compute() -> dict[str, Any]:
        calls.append(1)
        return {"answer": "a"}

    assert load_or_compute(path, compute) == load_or_compute(path, compute) == {"answer": "a"}
    assert len(calls) == 1


def test_the_next_run_is_the_lowest_number_without_a_saved_record(tmp_path: Path) -> None:
    assert next_run(tmp_path, b"request") == 1
    for run in (1, 3):
        load_or_compute(run_path(tmp_path, b"request", run), lambda: {"answer": "a"})
    assert next_run(tmp_path, b"request") == 2
    assert next_run(tmp_path, b"another request") == 1


def test_two_threads_that_want_the_same_record_compute_it_once(tmp_path: Path) -> None:
    path = run_path(tmp_path, b"request", 1)
    both_computing = threading.Barrier(2)
    calls: list[str] = []
    errors: list[Exception] = []

    def compute() -> dict[str, Any]:
        calls.append(threading.current_thread().name)
        # Without the lock of the path both threads meet here. With it the first waits alone until the timeout.
        with contextlib.suppress(threading.BrokenBarrierError):
            both_computing.wait(timeout=0.2)
        return {"answer": threading.current_thread().name}

    def work() -> None:
        try:
            load_or_compute(path, compute)
        except Exception as error:
            errors.append(error)

    workers = [threading.Thread(target=work, name=name) for name in ("first", "second")]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    assert errors == [] and len(calls) == 1
    assert json.loads(path.read_text())["answer"] == calls[0]
    assert list(path.parent.glob("*.part")) == []
