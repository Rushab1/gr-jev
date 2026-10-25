"""Independently check the paper's allocation, copy, and position figures."""

import statistics

from paper_support import PaperRuns, named_answers, paper_table_values

from grjev.constants import ALLOCATION_RUNS, PROBABILITY_DECIMALS
from grjev.tables import Selected


def allocation_counts(own: Selected, names: tuple[str, ...] | None) -> tuple[str, str, str]:
    """Calculate the gap, ranking share and below-uniform share directly from list entries."""
    gaps: list[float] = []
    for row, answer in named_answers(own):
        if len(row.labels) < 2 or len(answer.candidates) <= len(row.labels):
            continue
        correct = [round(answer.probabilities[key], PROBABILITY_DECIMALS) for key in row.labels]
        gaps.append(max(correct) - min(correct))
    ranked = below = total = 0
    for row in own.rows:
        for name in names or row.answers:
            listed = row.answers.get(name)
            if listed is None or len(row.labels) < 2 or len(listed.candidates) <= len(row.labels):
                continue
            probabilities = {key: round(v, PROBABILITY_DECIMALS) for key, v in listed.probabilities.items()}
            correct = [probabilities[key] for key in row.labels]
            distractors = [value for key, value in probabilities.items() if key not in row.labels]
            total += 1
            if min(correct) > max(distractors):
                ranked += 1
                below += min(correct) < round(1 / len(listed.candidates), PROBABILITY_DECIMALS)
    return f"{100 * statistics.fmean(gaps):.0f}", f"{ranked / total:.0%}", f"{below / ranked:.0%}"


def test_allocation_table_uses_the_correct_options_and_distractors_of_each_answer(paper_runs: PaperRuns) -> None:
    """Independently recalculate all 27 cells of the main allocation table."""
    spec, _, chosen = paper_runs
    actual = paper_table_values(spec, chosen, "allocation")
    for model in spec.models:
        expected = [
            cell for label, names in ALLOCATION_RUNS.values() for cell in allocation_counts(chosen(label, model), names)
        ]
        assert actual[model] == expected, model


def test_copies_tables_count_all_permutations_and_the_selected_position(paper_runs: PaperRuns) -> None:
    """Independently recalculate the copy gap and first/last selection shares for every model and dataset."""
    spec, _, chosen = paper_runs
    copies = next(finding for finding in spec.findings if any(table.file == "copies" for table in finding.tables))
    labels = [part.run for part in next(table for table in copies.tables if table.file == "copies").parts]
    gaps = paper_table_values(spec, chosen, "copies")
    positions = paper_table_values(spec, chosen, "positions")
    for model in spec.models:
        expected_gaps: list[str] = []
        expected_positions: list[str] = []
        for label in labels:
            answers = [answer for _, answer in named_answers(chosen(label, model))]
            assert answers and all(len(answer.candidates) == 5 for answer in answers)
            differences = [
                max(answer.probabilities.values()) - min(answer.probabilities.values()) for answer in answers
            ]
            expected_gaps.append(f"{100 * statistics.fmean(differences):.0f}")
            expected_positions.extend(
                f"{sum(answer.candidates.index(answer.choice) == place for answer in answers) / len(answers):.0%}"
                for place in (0, 4)
            )
        assert gaps[model] == expected_gaps, model
        assert positions[model] == expected_positions, model
