"""A report of runs as a web page: one table per run, with the models as rows and the figures as columns.

A definition in TABLES_DIR gives the title, the text and the runs, as for a table of runs.
"""

import html
import re
from collections.abc import Callable
from math import log2
from pathlib import Path

from grjev.charts import bars_chart, positions_chart, spans_chart
from grjev.constants import (
    MODEL_TITLES,
    POSITIONS_SHOWN_BELOW,
    PROCESSED_DIRS,
    REPO_ROOT,
    SECOND_TEAM_PROBABILITY,
)
from grjev.distribution import Distribution, Kind, correct_names, distribution, second_after_removal, yes_figures
from grjev.examples import Example, read_dataset
from grjev.tables import (
    ChartSpec,
    ExampleSpec,
    FindingSpec,
    RowSpec,
    Selected,
    TableSpec,
    answers_of,
    config_of,
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
# An example shows this many characters of its query and of the text of an option.
EXAMPLE_QUERY, EXAMPLE_TEXT = 420, 84


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
    f"Answers with every correct option above {SECOND_TEAM_PROBABILITY}": lambda found: (
        None if found.every_correct_above is None else f"{found.every_correct_above:.0%}"
    ),
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


def figures_of(chosen: dict[str, Selected]) -> dict[str, Distribution]:
    """Return the figures of the lists of a run for each model that answered one."""
    answers = {model: list(answers_of(own).values()) for model, own in chosen.items()}
    return {model: distribution(found) for model, found in answers.items() if found}


def confidence_text(found: Distribution, own: Selected) -> str:
    """Return the mean confidence of a model, with the share of the lists that it refused when it refused one."""
    refused = sum(unanswered(own))
    share_refused = f", refused {refused / (found.answers + refused):.0%}" if refused else ""
    return two(found.confidence) + share_refused


def chart_svg(chart: ChartSpec, runs: dict[str, dict[str, Selected]]) -> str:
    """Return one chart of the report, drawn from the runs that its definition names."""
    chosen = {name: runs[run] for run, name in chart.runs}
    found = {name: figures_of(own) for name, own in chosen.items()}
    if chart.kind == "positions":
        shares = {
            name: {model: [count / own.answers for count in own.predicted_at or ()] for model, own in models.items()}
            for name, models in found.items()
        }
        return positions_chart(chart.title, shares)
    if chart.kind == "confidence":
        bars = {
            name: {model: (own.confidence, confidence_text(own, chosen[name][model])) for model, own in models.items()}
            for name, models in found.items()
        }
        return bars_chart(chart.title, bars)
    if chart.kind == "second_correct":
        moved = {
            name: {model: second_after_removal(own.rows) for model, own in models.items()}
            for name, models in chosen.items()
        }
        kept = {name: {model: pair[:2] for model, pair in models.items() if pair} for name, models in moved.items()}
        return spans_chart(chart.title, kept, ("before the removal", "after the removal"))
    if chart.kind == "calibration":
        spans = {
            name: {model: (own.accuracy or 0.0, own.confidence) for model, own in models.items()}
            for name, models in found.items()
        }
        return spans_chart(chart.title, spans, ("accuracy", "mean confidence"))
    spans = {
        name: {model: (own.lowest_correct or 0.0, own.highest_correct or 0.0) for model, own in models.items()}
        for name, models in found.items()
    }
    return spans_chart(chart.title, spans, ("lowest correct option", "highest correct option"))


def cut(text: str, characters: int) -> str:
    """Return text on one line, cut after a number of characters with an ellipsis."""
    line = " ".join(text.split())
    return line if len(line) <= characters else line[:characters].rstrip() + "…"


def example_of(folder: Path, example_id: str, processed: dict[str, Path]) -> tuple[Example, dict[str, str]]:
    """Return an example of a run from its processed dataset, and the description of every option by its name."""
    config = config_of(folder)
    examples, tools = read_dataset(processed[config.dataset], config.test_files)
    found = next(example for own in examples.values() for example in own if example.id == example_id)
    texts = {tool.name: tool.description for tool in tools} | {tool.name: tool.description for tool in found.options}
    return found, texts


def list_html(name: str, caption: str, chosen: dict[str, Selected], example_id: str, texts: dict[str, str]) -> str:
    """Return one list of an example as a table: its options in the order sent, and the probability of each model.

    The probability of the prediction of a model is bold. A model that refused the list has "refused" in its place.
    """
    rows = {model: next(row for row in own.rows if row.id == example_id) for model, own in chosen.items()}
    answers = {model: row.answers.get(name) for model, row in rows.items()}
    first_model, first = next((model, answer) for model, answer in answers.items() if answer is not None)
    correct = set(correct_names(rows[first_model], first))
    mixed = 0 < len(correct) < len(first.candidates)
    head = "".join(f"<th>{marked(MODEL_TITLES[model])}</th>" for model in chosen)
    body = ""
    for place, option in enumerate(first.candidates, 1):
        shown = " ".join(option.split())
        text = cut(texts.get(shown, ""), EXAMPLE_TEXT)
        tag = ' <span class="tag">correct</span>' if mixed and option in correct else ""
        cells = ""
        for answer in answers.values():
            value = "refused" if answer is None else two(answer.probabilities[option])
            bold = answer is not None and answer.choice == option
            cells += f"<td>{'<b>' + value + '</b>' if bold else value}</td>"
        body += f"<tr><td>{place}</td><td><b>{marked(shown)}</b>{tag} {marked(text)}</td>{cells}</tr>"
    return (
        f'<p class="caption">{marked(caption)}</p><table class="example"><thead><tr><th>#</th><th>Option</th>'
        f"{head}</tr></thead><tbody>{body}</tbody></table>"
    )


def example_html(
    example: ExampleSpec, spec: RowSpec, chosen: dict[str, Selected], root: Path, processed: dict[str, Path]
) -> str:
    """Return one example of a run: its query, the instruction, and each of its lists with the probabilities."""
    first = next(iter(chosen.values()))
    found, texts = example_of(root / first.folder, example.id, processed)
    lists = "".join(list_html(name, caption, chosen, example.id, texts) for name, caption in example.lists)
    return (
        f'<p class="about">{marked(example.about)}</p><p><b>Query.</b> {marked(cut(found.query, EXAMPLE_QUERY))}</p>'
        f"<p><b>Instruction.</b> {marked(spec.instruction)}</p>{lists}"
        f'<p class="source">{marked(f"`{example.id}` in `{first.folder}`")}</p>'
    )


def finding_html(
    finding: FindingSpec,
    specs: dict[str, RowSpec],
    runs: dict[str, dict[str, Selected]],
    root: Path,
    processed: dict[str, Path],
) -> str:
    """Return the block of one finding: the conclusion, its strength, evidence and limits, a chart and an example."""
    evidence = "".join(f"<li>{marked(text)}</li>" for text in finding.evidence)
    limits = "".join(f"<li>{marked(text)}</li>" for text in finding.limits)
    example = example_html(finding.example, specs[finding.example.run], runs[finding.example.run], root, processed)
    return (
        f'<div class="finding"><h2>{marked(finding.title)}</h2><p class="lead">{marked(finding.conclusion)}</p>'
        f"<p><b>Strength for the paper:</b> {marked(finding.strength)}</p>"
        f'<div class="pair"><div><h3>{marked(finding.chart.title)}</h3>{chart_svg(finding.chart, runs)}'
        f"<h3>Evidence</h3><ul>{evidence}</ul><h3>Limits</h3><ul>{limits}</ul></div>"
        f"<div><h3>One example</h3>{example}</div></div></div>"
    )


def run_html(spec: RowSpec, chosen: dict[str, Selected]) -> str:
    """Return the block of one run: its name, what its lists hold, its instruction and its table."""
    first = next(iter(chosen.values()))
    counted = lists_held(first) if spec.figures == "lists" else ""
    instruction = f'<p class="said">Instruction: "{marked(spec.instruction)}"</p>' if spec.instruction else ""
    return (
        f"<section><h3>{marked(spec.label)}</h3><p>{marked(' '.join(filter(None, [spec.about, counted])))}</p>"
        f"{instruction}{table_html(TABLES[spec.figures](spec, chosen))}"
        f'<p class="source">{marked(f"`{first.folder}`, {spec.lists_text}")}</p></section>'
    )


STYLE = """
@page { size: A4 portrait; margin: 13mm 12mm; }
@page tables { size: A4 landscape; margin: 11mm 10mm; }
* { box-sizing: border-box; }
body { font: 9pt/1.42 -apple-system, "Helvetica Neue", Arial, sans-serif; color: #37352f; background: #ffffff;
  margin: 0 auto; max-width: 1180px; padding: 0; }
h1 { font-size: 17pt; margin: 0 0 6px; }
h2 { font-size: 12.5pt; margin: 16px 0 5px; padding-top: 8px; border-top: 2px solid #37352f; break-after: avoid; }
h3 { font-size: 9.5pt; margin: 8px 0 3px; break-after: avoid; }
p { margin: 0 0 4px; }
ul, ol { margin: 3px 0 6px; padding-left: 16px; }
li { margin: 2px 0; }
code { font: 7.8pt ui-monospace, Menlo, monospace; background: #f1f1ef; padding: 0 3px; border-radius: 3px; }
.lead { font-size: 10pt; }
.finding { break-before: page; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 0 22px; align-items: start; margin-top: 6px; }
.pair > div + div { border-left: 1px solid #e9e9e7; padding-left: 20px; }
.pair h3:first-child { margin-top: 0; }
.about, .caption { color: #5f5e5b; }
.caption { margin-top: 7px; font-weight: 600; }
.tag { font-size: 7pt; background: #dbeddb; border-radius: 3px; padding: 0 3px; }
.source { color: #9b9a97; font-size: 7.5pt; margin-top: 3px; }
section { margin: 12px 0 16px; break-inside: avoid; }
table { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; margin-top: 4px; }
th, td { border-bottom: 1px solid #e9e9e7; padding: 4px 7px; text-align: right; vertical-align: bottom; }
thead th { background: #f7f6f3; font-weight: 600; font-size: 8pt; line-height: 1.25; border-bottom: 1px solid #d3d1cb; }
tbody th, thead th:first-child { text-align: left; white-space: nowrap; font-weight: 600; }
tbody td { white-space: nowrap; }
table.example { font-size: 7.8pt; }
table.example th, table.example td { padding: 3px 4px; vertical-align: top; }
table.example thead th { font-size: 7.2pt; white-space: normal; }
table.example td:nth-child(2), table.example th:nth-child(2) { text-align: left; white-space: normal; }
table.example td:first-child { color: #9b9a97; }
.tables { page: tables; }
@media screen { body { padding: 18px; max-width: 760px; } .tables { width: 1180px; } }
"""


def page(spec: TableSpec, root: Path = REPO_ROOT, processed: dict[str, Path] = PROCESSED_DIRS) -> str:
    """Return the report of a definition as a web page.

    The conclusions and the findings come first, each finding with a chart and an example. The terms follow, then
    the runs under their groups on pages of their own, and the notes.
    """
    runs = {row.label: {model: selected(row, model, root) for model in row.models or spec.models} for row in spec.rows}
    specs = {row.label: row for row in spec.rows}
    parts = []
    group = ""
    for row in spec.rows:
        if row.group != group:
            group = row.group
            parts.append(f"<h2>{marked(group)}</h2>")
        parts.append(run_html(row, runs[row.label]))
    points = "".join(f"<li>{marked(text)}</li>" for text in spec.conclusions)
    conclusions = f"<h2>Conclusions</h2><ol>{points}</ol>" if points else ""
    findings = "".join(finding_html(finding, specs, runs, root, processed) for finding in spec.findings)
    terms = "".join(f"<li><b>{marked(term)}</b>: {marked(text)}</li>" for term, text in spec.terms)
    notes = "".join(f"<li>{marked(text)}</li>" for text in spec.notes)
    return (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(spec.title)}</title>'
        f"<style>{STYLE}</style></head><body><h1>{marked(spec.title)}</h1><p>{marked(spec.intro)}</p>"
        f'{conclusions}{findings}<div class="finding"><h2>Terms</h2><ul>{terms}</ul>'
        f'<h2>Notes</h2><ul>{notes}</ul></div><div class="tables"><h1>Tables by run</h1>{"".join(parts)}</div>'
        "</body></html>\n"
    )
