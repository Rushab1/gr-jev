"""Build the support tickets for the team question of TypeSafe's documentation, in the common format."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from grjev.constants import TICKETS_EXAMPLE_FILE, TICKETS_ONE_FILE, TICKETS_TWO_FILE, TOOLS_FILE_NAME
from grjev.examples import Example, Option, write_jsonl


class Stimuli(BaseModel):
    """The file of the tickets: TypeSafe's example request and answer, the issues of each team, and their pairs.

    A pair names two issues of two teams: a team and the number of one of its issues, twice. `typesafe_teams` holds
    the teams that the ticket of TypeSafe's example names an issue for.
    """

    source: str
    written: str
    typesafe_request: dict[str, Any]
    typesafe_documented_answer: dict[str, Any]
    typesafe_teams: list[str]
    issues: dict[str, list[str]]
    pairs: list[tuple[str, int, str, int]]


def read_stimuli(path: Path) -> Stimuli:
    """Read the file of the tickets."""
    return Stimuli.model_validate_json(path.read_bytes())


def teams_of(stimuli: Stimuli) -> list[Option]:
    """Return the teams of TypeSafe's question in its order, each with its description."""
    criteria = stimuli.typesafe_request["questions"]["department"]["criteria"]
    return [Option(name=name, description=text) for name, text in criteria.items()]


def ticket(file: str, number: int, issues: list[tuple[str, str]], teams: list[Option]) -> Example:
    """Return one ticket: its issues joined in the order given, and as labels their teams in the order of the list."""
    named = {team for team, _ in issues}
    return Example(
        id=f"tickets/{file}/{number}",
        query=" ".join(text for _, text in issues),
        options=teams,
        labels=[team.name for team in teams if team.name in named],
        raw={"issues": [{"team": team, "text": text} for team, text in issues]},
    )


def two_issue_tickets(stimuli: Stimuli) -> list[Example]:
    """Return a ticket for each pair of issues in each of its two orders. The second order follows the first."""
    teams = teams_of(stimuli)
    tickets: list[Example] = []
    for first_team, first, second_team, second in stimuli.pairs:
        pair = [(first_team, stimuli.issues[first_team][first]), (second_team, stimuli.issues[second_team][second])]
        tickets += [ticket(TICKETS_TWO_FILE, len(tickets), pair, teams)]
        tickets += [ticket(TICKETS_TWO_FILE, len(tickets), pair[::-1], teams)]
    return tickets


def one_issue_tickets(stimuli: Stimuli) -> list[Example]:
    """Return a ticket for each issue of a pair alone, in the order of the pairs."""
    teams = teams_of(stimuli)
    alone = [(team, stimuli.issues[team][number]) for a, i, b, j in stimuli.pairs for team, number in ((a, i), (b, j))]
    return [ticket(TICKETS_ONE_FILE, number, [issue], teams) for number, issue in enumerate(alone)]


def example_ticket(stimuli: Stimuli) -> Example:
    """Return the ticket of TypeSafe's example, labelled with the teams that it names an issue for."""
    teams = teams_of(stimuli)
    return Example(
        id=f"tickets/{TICKETS_EXAMPLE_FILE}/0",
        query=stimuli.typesafe_request["state"],
        options=teams,
        labels=[team.name for team in teams if team.name in stimuli.typesafe_teams],
        raw={"source": stimuli.source},
    )


def process_tickets(stimuli_dir: Path, processed_dir: Path) -> dict[str, int]:
    """Write the tickets with two issues, with one issue, TypeSafe's ticket and the teams. Return the rows written."""
    stimuli = read_stimuli(stimuli_dir / "tickets.json")
    files = {
        TICKETS_TWO_FILE: two_issue_tickets(stimuli),
        TICKETS_ONE_FILE: one_issue_tickets(stimuli),
        TICKETS_EXAMPLE_FILE: [example_ticket(stimuli)],
    }
    for name, tickets in files.items():
        write_jsonl(processed_dir / f"{name}.jsonl", tickets)
    write_jsonl(processed_dir / TOOLS_FILE_NAME, teams_of(stimuli))
    return {f"{name}.jsonl": len(tickets) for name, tickets in files.items()} | {TOOLS_FILE_NAME: 3}
