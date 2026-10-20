"""Check the paper's numeric tables against saved model responses, without API calls.

The results folders are intentionally untracked. These checks run when the paper runs are present locally and skip
on a checkout without them. The ordinary unit tests cover the arithmetic on small, committed examples.
"""

import statistics
from collections.abc import Callable, Sequence
from functools import cache
from pathlib import Path

import pytest

from grjev.constants import (
    MODEL_TITLES,
    PAPER_TABLES_DIR,
    PROBABILITY_DECIMALS,
    REPO_ROOT,
    TABLES_DIR,
    THRESHOLD_YES_NO_RUNS,
    UNIFORM_RUNS,
    YES_BIN_EDGES,
)
from grjev.report import paper_cells, paper_latex
from grjev.runs import ListAnswer, Row
from grjev.tables import RowSpec, Selected, TableSpec, read_spec, selected, uses
from grjev.thresholds import paper_detail_table, paper_table, read_pairs

type PaperRuns = tuple[TableSpec, dict[str, RowSpec], Callable[[str, str], Selected]]


@pytest.fixture(scope="module")
def paper_runs() -> PaperRuns:
    """Read each selected run once; skip when this checkout has no saved paper results."""
    spec = read_spec(TABLES_DIR / "paper_runs.json")
    rows = {row.label: row for row in spec.rows}
    if not all((REPO_ROOT / row.folder / "rows.jsonl").is_file() for row in spec.rows):
        pytest.skip("the untracked paper results folders are not available")

    @cache
    def chosen(label: str, model: str) -> Selected:
        return selected(rows[label], model)

    return spec, rows, chosen


def numeric_latex(text: str) -> str:
    """Ignore provenance comments while retaining every table header and numeric cell."""
    return "\n".join(line for line in text.splitlines() if not line.startswith("%"))


def paper_table_values(spec: TableSpec, chosen: Callable[[str, str], Selected], file: str) -> dict[str, list[str]]:
    """Return the generated cells for each model of one named findings table."""
    table = next(table for finding in spec.findings for table in finding.tables if table.file == file)
    runs = {part.run: {model: chosen(part.run, model) for model in spec.models} for part in table.parts}
    return {model: [cell for part in parts for cell in part] for model, parts in paper_cells(table, runs).items()}


def named_answers(own: Selected) -> list[tuple[Row, ListAnswer]]:
    """Return the answers named by a paper row, preserving the saved example and list order."""
    return [(row, answer) for row in own.rows for name, answer in row.answers.items() if uses(own.spec, name)]


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


def allocation_counts(own: Selected, name: str) -> tuple[str, str, str]:
    """Calculate the gap, ranking share and below-uniform share directly from list entries."""
    gaps: list[float] = []
    ranked = below = total = 0
    for row in own.rows:
        answer = row.answers.get(name)
        if answer is None or len(row.labels) < 2 or len(answer.candidates) <= len(row.labels):
            continue
        probabilities = {key: round(value, PROBABILITY_DECIMALS) for key, value in answer.probabilities.items()}
        correct = [probabilities[key] for key in row.labels]
        distractors = [value for key, value in probabilities.items() if key not in row.labels]
        gaps.append(max(correct) - min(correct))
        total += 1
        if min(correct) > max(distractors):
            ranked += 1
            below += min(correct) < round(1 / len(answer.candidates), PROBABILITY_DECIMALS)
    return f"{100 * statistics.fmean(gaps):.0f}", f"{ranked / total:.0%}", f"{below / ranked:.0%}"


def test_allocation_table_uses_the_correct_options_and_distractors_of_each_answer(paper_runs: PaperRuns) -> None:
    """Independently recalculate all 27 cells of the main allocation table."""
    spec, _, chosen = paper_runs
    actual = paper_table_values(spec, chosen, "allocation")
    for model in spec.models:
        expected = [cell for label, name in UNIFORM_RUNS.values() for cell in allocation_counts(chosen(label, model), name)]
        assert actual[model] == expected, model


def test_copies_tables_count_all_permutations_and_the_selected_position(paper_runs: PaperRuns) -> None:
    """Independently recalculate the copy gap and first/last selection shares for every model and dataset."""
    spec, _, chosen = paper_runs
    copies = next(finding for finding in spec.findings if any(table.file == "copies" for table in finding.tables))
    labels = [part.run for part in next(table for table in copies.tables if table.file == "copies").parts]
    gaps = paper_table_values(spec, chosen, "copies")
    positions = paper_table_values(spec, chosen, "positions")
    for model in spec.models:
        expected_gaps, expected_positions = [], []
        for label in labels:
            answers = [answer for _, answer in named_answers(chosen(label, model))]
            assert answers and all(len(answer.candidates) == 5 for answer in answers)
            expected_gaps.append(
                f"{100 * statistics.fmean(max(answer.probabilities.values()) - min(answer.probabilities.values()) for answer in answers):.0f}"
            )
            expected_positions.extend(
                f"{sum(answer.candidates.index(answer.choice) == place for answer in answers) / len(answers):.0%}"
                for place in (0, 4)
            )
        assert gaps[model] == expected_gaps, model
        assert positions[model] == expected_positions, model


def independently_paired(
    listed: Selected, name: str, asked: Selected
) -> tuple[list[list[tuple[float, bool]]], list[list[tuple[float, bool]]]]:
    """Join the list and yes/no responses by example ID and keep complete multi-label examples."""
    yes = {row.id: row for row in asked.rows}
    pairs: list[tuple[list[tuple[float, bool]], list[tuple[float, bool]]]] = []
    for row in listed.rows:
        answer = row.answers.get(name)
        other = yes.get(row.id)
        if answer is None or other is None or len(row.labels) < 2 or len(answer.candidates) <= len(row.labels):
            continue
        if other.refused or set(other.yes) != set(answer.candidates):
            continue
        forms = []
        for values in (answer.probabilities, other.yes):
            forms.append([(round(value, PROBABILITY_DECIMALS), key in row.labels) for key, value in values.items()])
        pairs.append((forms[0], forms[1]))
    return [one for one, _ in pairs], [two for _, two in pairs]


def best_exact(examples: Sequence[Sequence[tuple[float, bool]]]) -> str:
    """Find the best exact set accuracy using a direct set comparison at each paper threshold."""
    scores = []
    for step in range(101):
        threshold = step / 100
        hits = sum(
            {index for index, (probability, _) in enumerate(example) if probability >= threshold}
            == {index for index, (_, correct) in enumerate(example) if correct}
            for example in examples
        )
        scores.append(hits / len(examples))
    return f"{max(scores):.2f}"


def latex_model_cells(text: str, model: str) -> list[str]:
    """Extract the numeric cells of a named model row from a LaTeX table."""
    line = next(line for line in text.splitlines() if line.startswith(f"{MODEL_TITLES[model]} & "))
    return [part.strip().rstrip("\\ ") for part in line.split("&")[1:]]


def test_threshold_table_uses_matched_examples_and_independently_best_exact_sets(paper_runs: PaperRuns) -> None:
    """Check both forms and all nine model/dataset pairs against the paper's threshold table."""
    spec, _, chosen = paper_runs
    published = (PAPER_TABLES_DIR / "thresholds.tex").read_text()
    pairs = read_pairs(UNIFORM_RUNS, THRESHOLD_YES_NO_RUNS)
    for model in spec.models:
        expected = []
        for dataset, (label, name) in UNIFORM_RUNS.items():
            forms = independently_paired(chosen(label, model), name, chosen(THRESHOLD_YES_NO_RUNS[dataset], model))
            assert forms == pairs[(dataset, model)], (dataset, model)
            assert len(forms[0]) == len(forms[1]) > 0
            expected.extend(best_exact(form) for form in forms)
        assert latex_model_cells(published, model) == expected, model


def independent_ece(pairs: Sequence[tuple[float, bool]], edges: Sequence[float], skip_first: bool = False) -> float:
    """Pool absolute calibration gaps by the number of answers in each nonempty bin."""
    groups = []
    for index, (low, high) in enumerate(zip(edges, edges[1:], strict=True)):
        if skip_first and index == 0:
            continue
        group = [(value, hit) for value, hit in pairs if low < value <= high or (index == 0 and value == 0)]
        if group:
            groups.append(group)
    total = sum(map(len, groups))
    return sum(
        len(group) / total
        * abs(statistics.fmean(value for value, _ in group) - statistics.fmean(hit for _, hit in group))
        for group in groups
    )


def test_calibration_table_uses_answer_weighted_bins_and_excludes_the_first_yes_bin(paper_runs: PaperRuns) -> None:
    """Recalculate ECE from the saved predictions for every calibration column."""
    spec, _, chosen = paper_runs
    calibration = next(table for finding in spec.findings for table in finding.tables if table.file == "calibration")
    actual = paper_table_values(spec, chosen, "calibration")
    for model in spec.models:
        expected = []
        for part in calibration.parts:
            own = chosen(part.run, model)
            if part.columns == ["ECE"]:
                pairs = [
                    (max(answer.probabilities.values()), answer.choice in row.labels)
                    for row, answer in named_answers(own)
                ]
                expected.append(f"{100 * independent_ece(pairs, YES_BIN_EDGES):.0f}")
            else:
                pairs = [
                    (round(value, PROBABILITY_DECIMALS), name in row.labels)
                    for row in own.rows
                    if len(row.labels) > 1
                    for name, value in row.yes.items()
                ]
                expected.extend(
                    f"{100 * independent_ece(pairs, YES_BIN_EDGES, skip):.0f}" for skip in (False, True)
                )
        assert actual[model] == expected, model
