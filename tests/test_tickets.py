"""Tests for grjev.tickets."""

from pathlib import Path

from grjev.constants import DATASET_INSTRUCTIONS, TICKETS_FILE, TICKETS_TEST_FILES, TOOLS_FILE_NAME
from grjev.examples import read_dataset
from grjev.tickets import example_ticket, one_issue_tickets, process_tickets, read_stimuli, teams_of, two_issue_tickets

STIMULI = read_stimuli(TICKETS_FILE)


def test_the_teams_and_the_instruction_are_those_of_the_question_of_the_typesafe_example() -> None:
    question = STIMULI.typesafe_request["questions"]["department"]
    assert question["instructions"] == DATASET_INSTRUCTIONS["tickets"] == "Which team should handle this?"
    assert [(team.name, team.description) for team in teams_of(STIMULI)] == [
        ("returns", "Exchanges, wrong or damaged items"),
        ("shipping", "Delivery status, delays, lost packages"),
        ("billing", "Charges, invoices, payment problems"),
    ]
    documented = STIMULI.typesafe_documented_answer["department"]["probabilities"]
    assert documented == {"shipping": 0.04, "billing": 0.35, "returns": 0.61}


def test_every_issue_is_in_one_pair_and_every_pair_names_two_teams() -> None:
    used = [(team, number) for a, i, b, j in STIMULI.pairs for team, number in ((a, i), (b, j))]
    assert len(STIMULI.pairs) == 12 and len(used) == len(set(used)) == 24
    assert all(first != second for first, _, second, _ in STIMULI.pairs)
    assert {team: len(issues) for team, issues in STIMULI.issues.items()} == {"returns": 8, "shipping": 8, "billing": 8}
    texts = [text for issues in STIMULI.issues.values() for text in issues]
    assert len(set(texts)) == 24


def test_a_pair_gives_two_tickets_with_its_issues_in_both_orders_and_the_same_two_labels() -> None:
    tickets = two_issue_tickets(STIMULI)
    assert [ticket.id for ticket in tickets] == [f"tickets/two_issues/{number}" for number in range(24)]
    first, second = tickets[0], tickets[1]
    jacket, charged = STIMULI.issues["returns"][0], STIMULI.issues["billing"][0]
    assert (first.query, second.query) == (f"{jacket} {charged}", f"{charged} {jacket}")
    # The labels follow the order of the teams in the list, not the order of the issues in the ticket.
    assert first.labels == second.labels == ["returns", "billing"]
    assert [issue["team"] for issue in second.raw["issues"]] == ["billing", "returns"]
    assert all(len(ticket.labels or []) == 2 and len(ticket.options) == 3 for ticket in tickets)


def test_every_issue_of_a_pair_is_also_a_ticket_of_its_own_with_one_label() -> None:
    tickets = one_issue_tickets(STIMULI)
    assert len(tickets) == 24 and len({ticket.query for ticket in tickets}) == 24
    assert all(ticket.labels == [ticket.raw["issues"][0]["team"]] for ticket in tickets)
    both = {issue["text"] for ticket in two_issue_tickets(STIMULI) for issue in ticket.raw["issues"]}
    assert {ticket.query for ticket in tickets} == both


def test_the_ticket_of_the_typesafe_example_is_labelled_with_the_three_teams_that_it_names() -> None:
    ticket = example_ticket(STIMULI)
    assert ticket.query.startswith("Shoes arrived two weeks late and in the wrong size. Also I see two charges")
    assert ticket.labels == ["returns", "shipping", "billing"]


def test_the_processed_files_hold_49_tickets_and_the_three_teams(tmp_path: Path) -> None:
    written = process_tickets(TICKETS_FILE.parent, tmp_path)
    assert written == {"two_issues.jsonl": 24, "one_issue.jsonl": 24, "typesafe_example.jsonl": 1, TOOLS_FILE_NAME: 3}
    examples, teams = read_dataset(tmp_path, TICKETS_TEST_FILES)
    assert [len(examples[name]) for name in TICKETS_TEST_FILES] == [24, 24, 1] and len(teams) == 3
