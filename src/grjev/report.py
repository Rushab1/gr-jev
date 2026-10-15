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
    RENORMALISED_REST,
    REPO_ROOT,
    SECOND_TEAM_PROBABILITY,
)
from grjev.distribution import (
    Distribution,
    Kind,
    Removal,
    correct_names,
    distribution,
    second_after_removal,
    yes_bins,
    yes_figures,
)
from grjev.examples import Example, read_dataset
from grjev.tables import (
    ChartSpec,
    ExampleSpec,
    FindingSpec,
    PaperTableSpec,
    RowSpec,
    Selected,
    TableSpec,
    YesBinsSpec,
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
            f"Examples in which the options other than the removed one hold {RENORMALISED_REST} or more",
            "On these examples: its mean probability in the full list, renormalised over those options",
            "On these examples: its mean probability in the list without the removed option",
        ]
    ]
    for model, own in chosen.items():
        found = second_after_removal(own.rows)
        if found is None:
            table.append([MODEL_TITLES[model], "0", NOT_MEASURED, NOT_MEASURED, "0", NOT_MEASURED, NOT_MEASURED])
            continue
        kept = [NOT_MEASURED if value is None else two(value) for value in (found.renormalised, found.after_kept)]
        counts = [f"{found.examples:,}", two(found.before), two(found.after), f"{found.kept:,}"]
        table.append([MODEL_TITLES[model], *counts, *kept])
    return table


TABLES = {"lists": lists_table, "yes_no": yes_no_table, "second_correct": second_correct_table}


def yes_bins_table(table: YesBinsSpec, runs: dict[str, dict[str, Selected]]) -> str:
    """Return the table of the yes/no answers by bin of the probability of yes, with a column for each model and run.

    A cell holds the share of the answers in the bin that are about a correct option, and the number of answers. The
    first column gives the edges of each bin and the lowest and highest mean probability of yes in its cells.
    """
    columns = [(model, name, yes_bins(own.rows)) for run, name in table.runs for model, own in runs[run].items()]
    columns.sort(key=lambda column: list(MODEL_TITLES).index(column[0]))
    names = [f"{MODEL_TITLES[model]}, {name}" for model, name, _ in columns]
    body = [["Probability of yes (mean probability)", *names]]
    for index in range(len(columns[0][2])):
        found = [bins[index] for _, _, bins in columns]
        means = [part.mean for part in found if part]
        low, high = next((part.low, part.high) for part in found if part)
        cells = [f"{part.correct:.0%} ({part.answers:,})" if part else NOT_MEASURED for part in found]
        body.append([f"{low:.1f} to {high:.1f} ({min(means):.2f} to {max(means):.2f})", *cells])
    return (
        f'<div class="paper"><h3>Yes/no answers by probability of yes</h3><p class="caption">{marked(table.caption)}'
        f"</p>{table_html(body)}</div>"
    )


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
        f"{counted} and {lists:,} lists. Each list has {spanned(found.options)} options. "
        f"The number of correct options in a list is {spanned(found.correct_options)}."
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
        kept = {
            name: {model: (pair.before, pair.after) for model, pair in models.items() if pair}
            for name, models in moved.items()
        }
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


def position_share(found: Distribution | None, place: int) -> str | None:
    """Return the share of the predictions at one position, or None for lists that have no figure by position."""
    if found is None or found.predicted_at is None:
        return None
    return f"{found.predicted_at[place] / found.answers:.1%}"


def refused_share(own: Selected) -> str:
    """Return the share of the lists of a run that the model refused."""
    refused = unanswered(own)[1]
    return f"{refused / (len(answers_of(own)) + sum(unanswered(own))):.0%}"


def removal_text(own: Selected, value: Callable[[Removal], float | None]) -> str | None:
    """Return one figure of the second correct option before and after the removal, or None without one."""
    found = second_after_removal(own.rows)
    figure = None if found is None else value(found)
    return None if figure is None else two(figure)


def of_lists(value: Callable[[Distribution], float | None]) -> Callable[[Selected, Distribution | None], str | None]:
    """Return the column of one figure of the lists of a run, with two decimals."""

    def cell(own: Selected, found: Distribution | None) -> str | None:
        figure = None if found is None else value(found)
        return None if figure is None else two(figure)

    return cell


# Column header -> the text of the column in the table of a finding, from the examples of one model in a run and
# the figures of its lists. The text is None when the run has no such figure for the model.
PAPER_COLUMNS: dict[str, Callable[[Selected, Distribution | None], str | None]] = {
    "Lists refused": lambda own, found: refused_share(own),
    "Accuracy": of_lists(lambda found: found.accuracy),
    "Mean confidence": of_lists(lambda found: found.confidence),
    "Predictions at the first position": lambda own, found: position_share(found, 0),
    "Predictions at the last position": lambda own, found: position_share(found, -1),
    "Highest correct option": of_lists(lambda found: found.highest_correct),
    "Lowest correct option": of_lists(lambda found: found.lowest_correct),
    "Highest distractor": of_lists(lambda found: found.highest_distractor),
    f"Answers with every correct option above {SECOND_TEAM_PROBABILITY}": lambda own, found: (
        None if found is None or found.every_correct_above is None else f"{found.every_correct_above:.0%}"
    ),
    "Second correct option in the full list": lambda own, found: removal_text(own, lambda moved: moved.before),
    "After the removal": lambda own, found: removal_text(own, lambda moved: moved.after),
    "Full list, renormalised": lambda own, found: removal_text(own, lambda moved: moved.renormalised),
    "After the removal, same examples": lambda own, found: removal_text(own, lambda moved: moved.after_kept),
}


def paper_cells(table: PaperTableSpec, runs: dict[str, dict[str, Selected]]) -> dict[str, list[list[str]]]:
    """Return the cells of the table of a finding: for each model, the texts of the columns of each part."""
    cells: dict[str, list[list[str]]] = {}
    for part in table.parts:
        figures = figures_of(runs[part.run])
        for model, own in runs[part.run].items():
            texts = [PAPER_COLUMNS[header](own, figures.get(model)) or NOT_MEASURED for header in part.columns]
            cells.setdefault(model, []).append(texts)
    return cells


def paper_table(table: PaperTableSpec, runs: dict[str, dict[str, Selected]]) -> str:
    """Return the table of a finding for the paper: the models as rows, and the columns of each run under its name."""
    names = "".join(f'<th class="edge" colspan="{len(part.columns)}">{marked(part.name)}</th>' for part in table.parts)
    edges = [("" if place else ' class="edge"') for part in table.parts for place in range(len(part.columns))]
    headers = [header for part in table.parts for header in part.columns]
    heads = "".join(f"<th{edge}>{marked(header)}</th>" for edge, header in zip(edges, headers, strict=True))
    body = ""
    for model, parts in paper_cells(table, runs).items():
        texts = [text for part in parts for text in part]
        row = "".join(f"<td{edge}>{text}</td>" for edge, text in zip(edges, texts, strict=True))
        body += f"<tr><th>{marked(MODEL_TITLES[model])}</th>{row}</tr>"
    return (
        f'<div class="paper"><h3>Table for the paper</h3><p class="caption">{marked(table.caption)}</p>'
        f'<table><thead><tr><th rowspan="2">Model</th>{names}</tr><tr>{heads}</tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )


# Column header -> its short header in the LaTeX table of a finding. The caption of the table in the paper says
# what each one means.
PAPER_LATEX_HEADERS = {
    "Lists refused": "Refused",
    "Accuracy": "Acc.",
    "Mean confidence": "Conf.",
    "Predictions at the first position": "First",
    "Predictions at the last position": "Last",
    "Highest correct option": "High",
    "Lowest correct option": "Low",
    "Highest distractor": "Distr.",
    f"Answers with every correct option above {SECOND_TEAM_PROBABILITY}": f"All $>${SECOND_TEAM_PROBABILITY}",
    "Second correct option in the full list": "Before",
    "After the removal": "After",
    "Full list, renormalised": "Renorm.",
    "After the removal, same examples": "After$^*$",
}


def latex(text: str) -> str:
    """Return text with the characters that LaTeX reads as commands escaped."""
    return re.sub(r"([%&#_])", r"\\\1", text)


def spans(names: list[str], widths: list[int]) -> list[str]:
    """Return a LaTeX header row of names over groups of columns, and the rules under the names that are not empty.

    Neighbouring groups with the same name share one cell. The first column of the table holds the model.
    """
    cells, rules, start = [], [], 2
    for place, name in enumerate(names):
        if place and name == names[place - 1]:
            continue
        end = start
        for later in range(place, len(names)):
            if names[later] != name:
                break
            end += widths[later]
        cells.append(rf"\multicolumn{{{end - start}}}{{c}}{{{name}}}")
        if name:
            rules.append(rf"\cmidrule(lr){{{start}-{end - 1}}}")
        start = end
    return [" & " + " & ".join(cells) + r" \\", " ".join(rules)]


def paper_latex(table: PaperTableSpec, runs: dict[str, dict[str, Selected]]) -> str:
    """Return the table of a finding as a LaTeX `tabular` with the rules of the booktabs package.

    The models are the rows. The header has the group of each part when one is given, the name of each part, and
    the short header of each column from PAPER_LATEX_HEADERS.
    """
    widths = [len(part.columns) for part in table.parts]
    lines = [rf"\begin{{tabular}}{{l{'r' * sum(widths)}}}", r"\toprule"]
    if any(part.group for part in table.parts):
        lines += spans([latex(part.group) for part in table.parts], widths)
    lines += spans([latex(part.short or part.name) for part in table.parts], widths)
    heads = [PAPER_LATEX_HEADERS[header] for part in table.parts for header in part.columns]
    lines += ["Model & " + " & ".join(heads) + r" \\", r"\midrule"]
    for model, parts in paper_cells(table, runs).items():
        texts = [latex(text) for part in parts for text in part]
        lines.append(f"{latex(MODEL_TITLES[model])} & " + " & ".join(texts) + r" \\")
    return "\n".join([*lines, r"\bottomrule", r"\end{tabular}"]) + "\n"


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
    """Return the block of one finding: the conclusion, its strength, evidence and limits, a chart and an example.

    The table of the finding for the paper follows them when the finding has one.
    """
    evidence = "".join(f"<li>{marked(text)}</li>" for text in finding.evidence)
    limits = "".join(f"<li>{marked(text)}</li>" for text in finding.limits)
    example = example_html(finding.example, specs[finding.example.run], runs[finding.example.run], root, processed)
    return (
        f'<div class="finding"><h2>{marked(finding.title)}</h2><p class="lead">{marked(finding.conclusion)}</p>'
        f"<p><b>Strength for the paper:</b> {marked(finding.strength)}</p>"
        f'<div class="pair"><div><h3>{marked(finding.chart.title)}</h3>{chart_svg(finding.chart, runs)}'
        f"<h3>Evidence</h3><ul>{evidence}</ul></div>"
        f"<div><h3>One example</h3>{example}<h3>Limits</h3><ul>{limits}</ul></div></div>"
        f"{paper_table(finding.table, runs) if finding.table else ''}"
        f"{yes_bins_table(finding.yes_bins, runs) if finding.yes_bins else ''}</div>"
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
.paper { break-inside: avoid; margin-top: 6px; }
.paper .caption { margin-top: 0; font-weight: 400; }
.paper thead th { white-space: normal; text-align: center; vertical-align: bottom; }
.paper thead tr + tr th { font-weight: 400; text-align: right; }
.paper thead tr + tr th:first-child { white-space: normal; text-align: right; }
.paper .edge { border-left: 1px solid #d3d1cb; }
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
