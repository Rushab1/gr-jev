"""Requests written for the paper. A file holds the example it comes from, what was changed, and the request."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from grjev.jev import JevRequest


class WrittenRequest(BaseModel):
    """One written request: its source, the changes made to it, and the request without the model."""

    source: str
    written: str
    request: dict[str, Any]


def read_written(path: Path, model: str) -> JevRequest:
    """Return the request of a file, addressed to the model."""
    written = WrittenRequest.model_validate_json(path.read_bytes())
    return JevRequest.model_validate(written.request | {"model": model})
