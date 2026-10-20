"""Independently check removal, abstention, and ticket figures in the paper."""

import statistics

from paper_support import PaperRuns, named_answers, paper_table_values

from grjev.constants import (
    FULL_LIST,
    NONE_CANDIDATES,
    NONE_NAME,
    RENORMALISED_REST,
    SECOND_TEAM_PROBABILITY,
    WITHOUT_LIST,
)
from grjev.report import paper_cells
from grjev.tables import uses


def test_removal_table_follows_the_second_correct_option_into_the_matching_list(paper_runs: PaperRuns) -> None:
    """Recalculate each before/after value, and the renormalised value, from the full and matching removal lists."""
    spec, _, chosen = paper_runs
    table = next(table for finding in spec.findings for table in finding.tables if table.file == "removal")
    actual = paper_table_values(spec, chosen, "removal")
    for model in spec.models:
        expected: list[str] = []
        for part in table.parts:
            before, after, renormalised, kept = [], [], [], []
            for row in chosen(part.run, model).rows:
                full = row.answers.get(FULL_LIST)
                if full is None or len(row.labels) < 2:
                    continue
                highest, second = sorted(row.labels, key=lambda name: full.probabilities[name], reverse=True)[:2]
                without = row.answers.get(f"{WITHOUT_LIST}_{row.labels.index(highest) + 1}")
                if without is None:
                    continue
                before.append(full.probabilities[second])
                after.append(without.probabilities[second])
                rest = 1 - full.probabilities[highest]
                if rest >= RENORMALISED_REST:
                    renormalised.append(full.probabilities[second] / rest)
                    kept.append(without.probabilities[second])
            assert before and len(before) == len(after), (part.run, model)
            expected.extend(f"{statistics.fmean(values):.2f}" for values in (before, after, renormalised, kept))
        assert actual[model] == expected, model


def test_abstention_table_counts_refusals_and_none_predictions_separately(paper_runs: PaperRuns) -> None:
    """Check confidence, refusal and None-selection cells against individual saved lists."""
    spec, _, chosen = paper_runs
    table = next(table for finding in spec.findings for table in finding.tables if table.file == "abstention")
    actual = paper_table_values(spec, chosen, "abstention")
    none_names = {NONE_NAME, *(name for name, _ in NONE_CANDIDATES.values())}
    for model in spec.models:
        expected = []
        for part in table.parts:
            own = chosen(part.run, model)
            answers = [answer for _, answer in named_answers(own)]
            refused = sum(uses(own.spec, name) for row in own.rows for name in row.refused)
            rejected = sum(uses(own.spec, name) for row in own.rows for name in row.rejected)
            for column in part.columns:
                if column == "Mean confidence":
                    value = statistics.fmean(max(answer.probabilities.values()) for answer in answers)
                    expected.append(f"{value:.2f}")
                elif column == "Lists refused":
                    expected.append(f"{refused / (len(answers) + refused + rejected):.0%}")
                elif column == "Predictions of none of the above":
                    expected.append(f"{sum(answer.choice in none_names for answer in answers) / len(answers):.0%}")
                else:
                    raise AssertionError(column)
        assert actual[model] == expected, model


def test_ticket_finding_uses_both_correct_teams_and_the_single_issue_controls(paper_runs: PaperRuns) -> None:
    """Recalculate the ticket finding's report cells from its saved full-list answers."""
    spec, _, chosen = paper_runs
    finding = next(finding for finding in spec.findings if finding.title.startswith("6."))
    table = finding.tables[0]
    runs = {part.run: {model: chosen(part.run, model) for model in spec.models} for part in table.parts}
    actual = {model: [cell for part in parts for cell in part] for model, parts in paper_cells(table, runs).items()}
    for model in spec.models:
        expected: list[str] = []
        for part in table.parts:
            measurements = []
            for row, answer in named_answers(chosen(part.run, model)):
                correct = [answer.probabilities[name] for name in row.labels if name in answer.candidates]
                distractors = [value for name, value in answer.probabilities.items() if name not in row.labels]
                measurements.append((max(correct), min(correct), max(distractors)))
            assert len(measurements) == 24, (part.run, model)
            values = {
                "Highest correct option": f"{statistics.fmean(item[0] for item in measurements):.2f}",
                "Lowest correct option": f"{statistics.fmean(item[1] for item in measurements):.2f}",
                "Highest distractor": f"{statistics.fmean(item[2] for item in measurements):.2f}",
                f"Answers with every correct option above {SECOND_TEAM_PROBABILITY}": (
                    f"{sum(item[1] > SECOND_TEAM_PROBABILITY for item in measurements) / len(measurements):.0%}"
                ),
            }
            expected.extend(values[column] for column in part.columns)
        assert actual[model] == expected, model
