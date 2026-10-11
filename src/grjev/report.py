"""A report of runs as a web page: one table per run, with the models as rows and the figures as columns.

A definition in TABLES_DIR gives the title, the text and the runs, as for a table of runs.
"""

import html
import re
from collections.abc import Callable
from math import log2
from pathlib import Path

from grjev.constants import MODEL_TITLES, POSITIONS_SHOWN_BELOW, REPO_ROOT
from grjev.distribution import Distribution, Kind, distribution, second_after_removal, yes_figures
from grjev.tables import (
    RowSpec,
    Selected,
    TableSpec,
    answers_of,
    selected,
    signed,
    spanned,
    three,
    two,
    unanswered,
    uses,
)

NOT_MEASURED = "none"
ENTROPY_HEADER = "Mean entropy in bits"
MEASURED_HEADER = "Lists with a correct option and a distractor"
POSITION_HEADERS = ("Mean probability at each position", "Predictions at each position")


def ranked(found: Distribution) -> str | None:
    """Return the mean probability of each correct option, or of the highest and the lowest, or None without one."""
    if found.highest_correct is None or found.lowest_correct is None:
        return None
    if found.ranked_correct is not None:
        return three(found.ranked_correct)
    return f"highest {found.highest_correct:.3f}, lowest {found.lowest_correct:.3f}"


def by_position(found: Distribution, values: tuple[float, ...] | tuple[int, ...] | None) -> str | None:
    """Return one value per position, for lists of one length below POSITIONS_SHOWN_BELOW, or None."""
    if values is None or len(values) >= POSITIONS_SHOWN_BELOW:
        return None
    return ", ".join(f"{value:.2f}" if isinstance(value, float) else f"{value:,}" for value in values)


def with_correct(found: Distribution, value: float | None, text: Callable[[float], str]) -> str | None:
    """Return a figure about the prediction, or None for lists with no correct option or with only correct ones."""
    return None if value is None or found.kind in (Kind.NONE, Kind.ALL) else text(value)


def several(found: Distribution, value: float | None) -> str | None:
    """Return a difference that needs several correct options in a list, or None."""
    return None if value is None or found.kind in (Kind.NONE, Kind.ONE) else signed(value)


def margin(found: Distribution, value: float | None) -> str | None:
    """Return a difference between a correct option and the highest distractor, or None without both."""
    return None if value is None else signed(value)


def measured(found: Distribution) -> str | None:
    """Return the number of answers that the differences are measured on, when they leave out answers."""
    return None if found.measured == found.answers else f"{found.measured:,}"


# Column header -> the text of the column for the figures of one model, or None when the lists have no option that
# the figure needs. A column that is None for every model is left out of the table of a run.
COLUMNS: dict[str, Callable[[Distribution], str | None]] = {
    MEASURED_HEADER: measured,
    "Accuracy": lambda found: with_correct(found, found.accuracy, two),
    "Exact match": lambda found: None if found.exact_match is None else two(found.exact_match),
    "Mean confidence": lambda found: two(found.confidence),
    "Overconfidence": lambda found: with_correct(found, found.overconfidence, signed),
    "ECE": lambda found: with_correct(found, found.ece, two),
    "Prediction minus runner-up": lambda found: two(found.runner_up),
    "Highest correct minus lowest correct": lambda found: several(found, found.spread),
    "Highest correct minus highest distractor": lambda found: margin(found, found.highest_margin),
    "Lowest correct minus highest distractor": lambda found: (
        margin(found, found.lowest_margin) if found.kind is Kind.SEVERAL else None
    ),
    "Mean probability of each correct option, from the highest": ranked,
    "Mean probability of the highest distractor": lambda found: (
        None if found.highest_distractor is None or found.kind is Kind.NONE else f"{found.highest_distractor:.3f}"
    ),
    ENTROPY_HEADER: lambda found: two(found.entropy),
    POSITION_HEADERS[0]: lambda found: by_position(found, found.by_position),
    POSITION_HEADERS[1]: lambda found: by_position(found, found.predicted_at),
}


def entropy_header(found: Distribution) -> str:
    """Return the header of the entropy column with the entropy of equal probabilities over the options of a list."""
    low, high = (log2(options) for options in found.options)
    highest = f"{low:.2f}" if low == high else f"{low:.2f} to {high:.2f}"
    return f"{ENTROPY_HEADER} (maximum {highest})"


def lists_table(spec: RowSpec, chosen: dict[str, Selected]) -> list[list[str]]:
    """Return the table of the lists of a run: a header, then one row per model with the figures that exist.

    The figures by position are given for a run whose definition asks for them.
    """
    found = {model: [pair for pair in answers_of(own).values()] for model, own in chosen.items()}
    figures = {model: distribution(answers) for model, answers in found.items() if answers}
    wanted = {header: cell for header, cell in COLUMNS.items() if spec.positions or header not in POSITION_HEADERS}
    cells = {header: {model: cell(own) for model, own in figures.items()} for header, cell in wanted.items()}
    shown = [header for header, column in cells.items() if any(text is not None for text in column.values())]
    first = next(iter(figures.values()), None)
    headers = [entropy_header(first) if header == ENTROPY_HEADER and first else header for header in shown]
    table = [["Model", "Lists answered", "Lists refused", *headers]]
    for model, own in chosen.items():
        counts = [f"{len(found[model]):,}", f"{sum(unanswered(own)):,}"]
        texts = [cells[header].get(model) or NOT_MEASURED for header in shown]
        table.append([MODEL_TITLES[model], *counts, *texts])
    return table


def share(count: int, total: int) -> str:
    """Return a count out of a total."""
    return f"{count:,} of {total:,}"


def yes_no_table(spec: RowSpec, chosen: dict[str, Selected]) -> list[list[str]]:
    """Return the table of the yes/no answers of a run: a header, then one row per model."""
    table = [
        [
            "Model",
            "Questions answered",
            "Questions refused",
            "Correct options: mean probability of yes",
            "Correct options with yes at 0.50 or more",
            "Distractors: mean probability of yes",
            "Distractors with yes at 0.50 or more",
        ]
    ]
    for model, own in chosen.items():
        found = yes_figures(own.rows)
        table.append(
            [
                MODEL_TITLES[model],
                f"{found.correct + found.distractors:,}",
                f"{sum(unanswered(own)):,}",
                NOT_MEASURED if found.correct_mean is None else two(found.correct_mean),
                share(found.correct_yes, found.correct),
                NOT_MEASURED if found.distractor_mean is None else two(found.distractor_mean),
                share(found.distractor_yes, found.distractors),
            ]
        )
    return table


def second_correct_table(spec: RowSpec, chosen: dict[str, Selected]) -> list[list[str]]:
    """Return the table of the second correct option before and after the top one is removed, one row per model."""
    table = [
        [
            "Model",
            "Examples with both lists answered",
            "Mean probability of the second correct option in the full list",
            "Its mean probability in the list without the correct option that has the highest probability",
        ]
    ]
    for model, own in chosen.items():
        found = second_after_removal(own.rows)
        texts = [f"{found[2]:,}", two(found[0]), two(found[1])] if found else ["0", NOT_MEASURED, NOT_MEASURED]
        table.append([MODEL_TITLES[model], *texts])
    return table


TABLES = {"lists": lists_table, "yes_no": yes_no_table, "second_correct": second_correct_table}


def lists_held(chosen: Selected) -> str:
    """Return the sentence with the examples and the lists of a run, and the options that a list holds."""
    answers = list(answers_of(chosen).values())
    lists = len(answers) + sum(unanswered(chosen))
    asked = [[*row.answers, *row.refused, *row.rejected] for row in chosen.rows]
    examples = sum(any(uses(chosen.spec, name) for name in names) for names in asked)
    counted = f"{examples:,} examples"
    if not answers:
        return counted + "."
    found = distribution(answers)
    return (
        f"{counted}, {lists:,} lists. Options in a list: {spanned(found.options)}. "
        f"Correct options in a list: {spanned(found.correct_options)}."
    )


def marked(text: str) -> str:
    """Return text as HTML, with the parts between backticks as code."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(text, quote=False))


def table_html(table: list[list[str]]) -> str:
    """Return a table as HTML. The first row is the header and the first column names the model."""
    head = "".join(f"<th>{marked(header)}</th>" for header in table[0])
    body = "".join(
        f"<tr><th>{marked(row[0])}</th>" + "".join(f"<td>{marked(cell)}</td>" for cell in row[1:]) + "</tr>"
        for row in table[1:]
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def run_html(spec: RowSpec, models: tuple[str, ...], root: Path) -> str:
    """Return the block of one run: its name, what its lists hold, its instruction and its table."""
    chosen = {model: selected(spec, model, root) for model in spec.models or models}
    first = next(iter(chosen.values()))
    counted = lists_held(first) if spec.figures == "lists" else ""
    instruction = f'<p class="said">Instruction: "{marked(spec.instruction)}"</p>' if spec.instruction else ""
    return (
        f"<section><h3>{marked(spec.label)}</h3><p>{marked(' '.join(filter(None, [spec.about, counted])))}</p>"
        f"{instruction}{table_html(TABLES[spec.figures](spec, chosen))}"
        f'<p class="source">{marked(f"`{first.folder}`, {spec.lists_text}")}</p></section>'
    )


STYLE = """
@page { size: A4 landscape; margin: 11mm 10mm; }
* { box-sizing: border-box; }
body { font: 9.5pt/1.45 -apple-system, "Helvetica Neue", Arial, sans-serif; color: #37352f; background: #ffffff;
  margin: 0 auto; max-width: 1180px; padding: 16px; }
h1 { font-size: 19pt; margin: 0 0 6px; }
h2 { font-size: 13.5pt; margin: 22px 0 4px; padding-top: 8px; border-top: 2px solid #37352f; break-after: avoid; }
h3 { font-size: 10.5pt; margin: 0 0 2px; }
p { margin: 0 0 4px; }
ul { margin: 4px 0 8px; padding-left: 18px; }
li { margin: 1px 0; }
code { font: 8.5pt ui-monospace, Menlo, monospace; background: #f1f1ef; padding: 0 3px; border-radius: 3px; }
section { margin: 12px 0 16px; break-inside: avoid; }
.said { color: #5f5e5b; }
.source { color: #9b9a97; font-size: 8pt; margin-top: 3px; }
table { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; margin-top: 4px; }
th, td { border-bottom: 1px solid #e9e9e7; padding: 4px 7px; text-align: right; vertical-align: bottom; }
thead th { background: #f7f6f3; font-weight: 600; font-size: 8pt; line-height: 1.25; border-bottom: 1px solid #d3d1cb; }
tbody th, thead th:first-child { text-align: left; white-space: nowrap; font-weight: 600; }
tbody td { white-space: nowrap; }
"""


def page(spec: TableSpec, root: Path = REPO_ROOT) -> str:
    """Return the report of a definition as a web page: the terms, the runs under their groups, and the notes."""
    parts = []
    group = ""
    for row in spec.rows:
        if row.group != group:
            group = row.group
            parts.append(f"<h2>{marked(group)}</h2>")
        parts.append(run_html(row, spec.models, root))
    terms = "".join(f"<li><b>{marked(term)}</b>: {marked(text)}</li>" for term, text in spec.terms)
    notes = "".join(f"<li>{marked(text)}</li>" for text in spec.notes)
    return (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(spec.title)}</title>'
        f"<style>{STYLE}</style></head><body><h1>{marked(spec.title)}</h1><p>{marked(spec.intro)}</p>"
        f"<h2>Terms</h2><ul>{terms}</ul>{''.join(parts)}<h2>Notes</h2><ul>{notes}</ul></body></html>\n"
    )
