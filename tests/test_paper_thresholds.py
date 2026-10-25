"""Independently check threshold and calibration figures in the paper."""

import statistics
from collections.abc import Callable, Sequence

from paper_support import PaperRuns, named_answers, paper_table_values

from grjev.constants import (
    MODEL_TITLES,
    PAPER_TABLES_DIR,
    PROBABILITY_DECIMALS,
    THRESHOLD_YES_NO_RUNS,
    UNIFORM_RUNS,
    YES_BIN_EDGES,
)
from grjev.tables import Selected, TableSpec
from grjev.thresholds import read_pairs

Marked = list[tuple[float, bool]]


def marked(values: dict[str, float], labels: Sequence[str]) -> Marked:
    """Round each probability and say whether its choice is a label."""
    return [(round(value, PROBABILITY_DECIMALS), key in labels) for key, value in values.items()]


def independently_paired(
    listed: Selected, names: tuple[str, ...] | None, asked: Selected
) -> tuple[list[list[Marked]], list[list[Marked]]]:
    """Join the lists and yes/no responses by example ID and keep complete multi-label examples, with every answered
    list of an example together."""
    yes = {row.id: row for row in asked.rows}
    sent: list[list[Marked]] = []
    questioned: list[list[Marked]] = []
    for row in listed.rows:
        other = yes.get(row.id)
        keys = list(row.answers) if names is None else names
        answers = [row.answers[key] for key in keys if key in row.answers]
        answers = [answer for answer in answers if len(answer.candidates) > len(row.labels)]
        if other is None or other.refused or len(row.labels) < 2 or not answers:
            continue
        if any(set(other.yes) != set(answer.candidates) for answer in answers):
            continue
        sent.append([marked(answer.probabilities, row.labels) for answer in answers])
        questioned.append([marked(other.yes, row.labels)])
    return sent, questioned


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
        expected: list[str] = []
        for dataset, (label, names) in UNIFORM_RUNS.items():
            forms = independently_paired(chosen(label, model), names, chosen(THRESHOLD_YES_NO_RUNS[dataset], model))
            assert forms == pairs[(dataset, model)], (dataset, model)
            assert len(forms[0]) == len(forms[1]) > 0
            expected.extend(best_exact([lists for group in form for lists in group]) for form in forms)
        assert latex_model_cells(published, model) == expected, model


def independent_ece(pairs: Sequence[tuple[float, bool]], edges: Sequence[float], skip_first: bool = False) -> float:
    """Pool absolute calibration gaps by the number of answers in each nonempty bin."""
    groups = []
    for index, (low, high) in enumerate(zip(edges[:-1], edges[1:], strict=True)):
        if skip_first and index == 0:
            continue
        group = [(value, hit) for value, hit in pairs if low < value <= high or (index == 0 and value == 0)]
        if group:
            groups.append(group)
    total = sum(map(len, groups))
    return (
        sum(
            len(group) * abs(statistics.fmean(value for value, _ in group) - statistics.fmean(hit for _, hit in group))
            for group in groups
        )
        / total
    )


def test_calibration_table_uses_answer_weighted_bins_and_excludes_the_first_yes_bin(paper_runs: PaperRuns) -> None:
    """Recalculate ECE from the saved predictions for every calibration column."""
    spec, _, chosen = paper_runs
    for file in ("calibration_one", "calibration"):
        check_calibration(spec, chosen, file)


def check_calibration(spec: TableSpec, chosen: Callable[[str, str], Selected], file: str) -> None:
    """Compare the cells of one calibration table with ECE recalculated from the saved predictions."""
    calibration = next(table for finding in spec.findings for table in finding.tables if table.file == file)
    actual = paper_table_values(spec, chosen, file)
    for model in spec.models:
        expected: list[str] = []
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
                expected.extend(f"{100 * independent_ece(pairs, YES_BIN_EDGES, skip):.0f}" for skip in (False, True))
        assert actual[model] == expected, model
