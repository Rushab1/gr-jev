"""Check that paper tables use aligned saved runs and reproduce their LaTeX cells."""

from paper_support import PaperRuns

from grjev.constants import PAPER_TABLES_DIR, THRESHOLD_YES_NO_RUNS, UNIFORM_RUNS
from grjev.report import paper_latex
from grjev.thresholds import paper_detail_table, paper_table, read_pairs


def numeric_latex(text: str) -> str:
    """Ignore provenance comments while retaining every table header and numeric cell."""
    return "\n".join(line for line in text.splitlines() if not line.startswith("%"))


def test_findings_tables_rebuild_from_the_saved_paper_runs(paper_runs: PaperRuns) -> None:
    """Every checked-in findings table must have the cells produced by its selected saved runs."""
    spec, _, chosen = paper_runs
    for finding in spec.findings:
        for table in finding.tables:
            if not table.file:
                continue
            runs = {part.run: {model: chosen(part.run, model) for model in spec.models} for part in table.parts}
            expected = paper_latex(table, runs)
            actual = (PAPER_TABLES_DIR / f"{table.file}.tex").read_text()
            assert numeric_latex(actual) == numeric_latex(expected), table.file

    pairs = read_pairs(UNIFORM_RUNS, THRESHOLD_YES_NO_RUNS)
    for file, build in (("thresholds", paper_table), ("threshold_detail", paper_detail_table)):
        actual = (PAPER_TABLES_DIR / f"{file}.tex").read_text()
        assert numeric_latex(actual) == numeric_latex(build(pairs)), file


def test_models_receive_the_same_examples_and_candidate_lists(paper_runs: PaperRuns) -> None:
    """A table must not compare probabilities from different examples or differently named lists."""
    spec, _, chosen = paper_runs
    labels = {part.run for finding in spec.findings for table in finding.tables for part in table.parts}
    labels.update(label for label, _ in UNIFORM_RUNS.values())
    labels.update(THRESHOLD_YES_NO_RUNS.values())
    for label in labels:
        by_model = {model: {row.id: row for row in chosen(label, model).rows} for model in spec.models}
        first, *others = by_model.values()
        for other in others:
            assert first.keys() == other.keys(), label
            for example_id, row in first.items():
                counterpart = other[example_id]
                assert row.labels == counterpart.labels, (label, example_id)
                for name in row.answers.keys() & counterpart.answers.keys():
                    assert row.answers[name].candidates == counterpart.answers[name].candidates, (
                        label,
                        example_id,
                        name,
                    )
