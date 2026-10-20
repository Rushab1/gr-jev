"""Fixtures shared by tests that recalculate the paper's numbers."""

from functools import cache

import pytest
from paper_support import PaperRuns

from grjev.constants import REPO_ROOT, TABLES_DIR, THRESHOLD_YES_NO_RUNS, UNIFORM_RUNS
from grjev.tables import Selected, read_spec, selected


@pytest.fixture(scope="session")
def paper_runs() -> PaperRuns:
    """Read each selected run once; skip when this checkout has no saved paper results."""
    spec = read_spec(TABLES_DIR / "paper_runs.json")
    rows = {row.label: row for row in spec.rows}
    labels = {part.run for finding in spec.findings for table in finding.tables for part in table.parts}
    labels.update(label for label, _ in UNIFORM_RUNS.values())
    labels.update(THRESHOLD_YES_NO_RUNS.values())
    if not all((REPO_ROOT / rows[label].folder / "rows.jsonl").is_file() for label in labels):
        pytest.skip("the untracked paper results folders are not available")

    @cache
    def chosen(label: str, model: str) -> Selected:
        return selected(rows[label], model)

    return spec, rows, chosen
