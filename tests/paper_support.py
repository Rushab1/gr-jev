"""Shared selection and table helpers for tests of the paper's numbers."""

from collections.abc import Callable

from grjev.report import paper_cells
from grjev.runs import ListAnswer, Row
from grjev.tables import RowSpec, Selected, TableSpec, uses

type PaperRuns = tuple[TableSpec, dict[str, RowSpec], Callable[[str, str], Selected]]


def paper_table_values(spec: TableSpec, chosen: Callable[[str, str], Selected], file: str) -> dict[str, list[str]]:
    """Return the generated cells for each model of one named findings table."""
    table = next(table for finding in spec.findings for table in finding.tables if table.file == file)
    runs = {part.run: {model: chosen(part.run, model) for model in spec.models} for part in table.parts}
    return {model: [cell for part in parts for cell in part] for model, parts in paper_cells(table, runs).items()}


def named_answers(own: Selected) -> list[tuple[Row, ListAnswer]]:
    """Return the answers named by a paper row, preserving the saved example and list order."""
    return [(row, answer) for row in own.rows for name, answer in row.answers.items() if uses(own.spec, name)]
