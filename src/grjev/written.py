"""Requests written for the paper. A file holds the example it comes from, what was changed, and the request."""

import re
from collections.abc import Collection
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from grjev.jev import ChoiceQuestion, JevRequest
from grjev.report import latex

# A run of Cyrillic words, with their stress marks. The fonts of the paper do not hold these letters.
CYRILLIC = re.compile(r"[\u0400-\u04FF\u0300-\u036F]+(?:\s+[\u0400-\u04FF\u0300-\u036F]+)*")


# The characters outside ASCII that a table can hold, with the LaTeX that typesets them in the fonts of the paper.
TYPESET = {
    "–": "--",
    "á": "\\'{a}",
    "é": "\\'{e}",
    "í": "\\'{\\i}",
    "ó": "\\'{o}",
    "ú": "\\'{u}",
    "ñ": "\\~{n}",
    "ü": '\\"{u}',
}


def typeset(text: str) -> str:
    """Return text for a LaTeX table: commands escaped, and a run of Cyrillic words shown as "[...]".

    A character outside ASCII that has no entry in TYPESET raises an error, since the fonts would drop it.
    """
    escaped = latex(CYRILLIC.sub("[...]", text))
    unknown = sorted({char for char in escaped if ord(char) > 127 and char not in TYPESET})
    if unknown:
        raise ValueError(f"no LaTeX for the characters {unknown}")
    return "".join(TYPESET.get(char, char) for char in escaped)


class WrittenRequest(BaseModel):
    """One written request: its source, the changes made to it, and the request without the model."""

    source: str
    written: str
    request: dict[str, Any]


def read_written(path: Path, model: str) -> JevRequest:
    """Return the request of a file, addressed to the model."""
    written = WrittenRequest.model_validate_json(path.read_bytes())
    return JevRequest.model_validate(written.request | {"model": model})


def request_latex(requests: list[JevRequest], only: Collection[str] = ()) -> str:
    """Return a LaTeX tabular with the query of each request, and the instruction and the options that they share.

    The options are those of the first list of the requests, or the named ones of them. The requests must hold the
    same lists.
    """
    lists = requests[0].questions
    first = next(iter(lists.values()))
    if any(request.questions != lists for request in requests) or not isinstance(first, ChoiceQuestion):
        raise ValueError("the requests of one table hold the same lists, and the first is a list of options")
    rows = [f"Question & {typeset(request.state)} \\\\" for request in requests]
    rows += [f"Instruction & {typeset(first.instructions)} \\\\", "\\midrule", "Title & Passage \\\\", "\\midrule"]
    rows += [
        f"{typeset(name)} & {typeset(description or '')} \\\\"
        for name, description in first.criteria.items()
        if not only or name in only
    ]
    top = ["\\begin{tabular}{@{}p{0.25\\linewidth}p{0.68\\linewidth}@{}}", "\\toprule"]
    return "\n".join([*top, *rows, "\\bottomrule", "\\end{tabular}"]) + "\n"
