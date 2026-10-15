"""A table of runs: one row per run with the figures of its probability distribution, and one table per model.

A definition in TABLES_DIR gives the title, the text and the rows. A row names a results folder of a Jev run, and
for another model the folder in which that model repeats the run.
"""

from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from grjev.constants import (
    JEV_MODEL,
    MODEL_TITLES,
    POSITIONS_SHOWN_BELOW,
    PROCESSED_DIRS,
    REPO_ROOT,
    RESULTS_MODEL_NAMES,
)
from grjev.distribution import Distribution, Kind, distribution, rounded
from grjev.examples import Example, read_jsonl
from grjev.runs import ListAnswer, Row, RunConfig

NO_ANSWER = "no list answered"
NO_CORRECT = "no correct option"
ONE_CORRECT = "one correct option"
ALL_CORRECT = "every option is correct"
NO_DISTRACTOR = "no distractor"
LEADING_HEADERS = [
    "Run",
    "Examples",
    "Answers",
    "Lists that the model rejected",
    "Lists that the model refused to answer",
]
LAST_HEADER = "Results folder and lists"


class RowSpec(BaseModel):
    """One row of a table: a results folder of Jev, and the examples and the lists of it that the row uses.

    `folder` is relative to the repository. `lists_text` names the examples and lists in the last column. A row
    uses the examples of `test_file` whose number of labels is within `labels`, and the lists named in `lists` or
    whose name starts with `list_prefix`. Without one of these it uses all of them. `raw_type` keeps the examples
    whose raw row has that `type`, such as the bridge and comparison questions of HotpotQA. `models` limits the row
    to some models.

    A report shows a row as a table of its own, under the heading `group`, with `about`, which says what the lists
    hold, and `instruction`, the instruction sent with them. `figures` names the figures of that table: those of
    the lists, of the yes/no answers, or of the second correct option before and after the top one is removed.
    `positions` says that the table gives the figures by position, which a run with cyclic permutations has.
    """

    label: str
    folder: str
    lists_text: str
    test_file: str | None = None
    labels: tuple[int, int] | None = None
    raw_type: str | None = None
    lists: tuple[str, ...] | None = None
    list_prefix: str = ""
    models: tuple[str, ...] | None = None
    group: str = ""
    about: str = ""
    instruction: str = ""
    figures: Literal["lists", "yes_no", "second_correct"] = "lists"
    positions: bool = False


class ChartSpec(BaseModel):
    """One chart of a report. `runs` holds the label of each run that it draws and the name of the run in the chart.

    `kind` names the figure: the share of the predictions at each position, the mean probability of the lowest and
    of the highest correct option, the mean confidence, the accuracy next to the mean confidence, or the second
    correct option before and after the top one is removed.
    """

    kind: Literal["positions", "correct_span", "confidence", "calibration", "second_correct"]
    title: str
    runs: list[tuple[str, str]]


class ExampleSpec(BaseModel):
    """One example of a run that a report shows with its options and the probabilities of each model.

    `run` is the label of the run and `id` the id of the example. `lists` holds the name of each list of the example
    that is shown, with the text written over it. `about` says how the example was chosen.
    """

    run: str
    id: str
    lists: list[tuple[str, str]]
    about: str


class PartSpec(BaseModel):
    """The columns that one run gives to the table of a finding. `name` is the heading over them.

    The LaTeX table uses `short` in place of `name` when it is given, and puts `group` over the parts that share it.
    """

    run: str
    name: str
    columns: list[str]
    short: str = ""
    group: str = ""


class PaperTableSpec(BaseModel):
    """The table of a finding for the paper: the models as rows, and the figures of each of its runs as columns.

    `file` names the LaTeX file of the table in the folder of the paper.
    """

    caption: str
    parts: list[PartSpec]
    file: str = ""


class YesBinsSpec(BaseModel):
    """A table of the yes/no answers to examples with two or more labels, by bin of the probability of yes.

    `runs` holds the label of each yes/no run and the name of its examples. The table has a column for each model and
    run.
    """

    title: str
    caption: str
    runs: list[tuple[str, str]]


class FindingSpec(BaseModel):
    """One finding of a report: the conclusion, how strong it is for the paper, its evidence and its limits.

    The finding is shown with a chart and with one example, and with its table for the paper and its tables of the
    yes/no answers by bin when it has them.
    """

    title: str
    strength: str
    conclusion: str
    evidence: list[str]
    limits: list[str]
    chart: ChartSpec
    example: ExampleSpec
    table: PaperTableSpec | None = None
    yes_bins: list[YesBinsSpec] = []


class FigureRowSpec(BaseModel):
    """One group of rows of the figure of the paper: a run with full lists, and the run with the removal."""

    name: str
    run: str
    removal: str


class FigureSpec(BaseModel):
    """The figure of the paper. `file` names its LaTeX file in the folder of the paper."""

    file: str
    rows: list[FigureRowSpec]


class TableSpec(BaseModel):
    """The definition of a document with one table per model, or of a report with findings and one table per run.

    A report can also define the figure of the paper.
    """

    title: str
    intro: str
    terms: list[tuple[str, str]]
    notes: list[str]
    models: tuple[str, ...]
    rows: list[RowSpec]
    conclusions: list[str] = []
    findings: list[FindingSpec] = []
    figure: FigureSpec | None = None


def read_spec(path: Path) -> TableSpec:
    """Read the definition of a table."""
    return TableSpec.model_validate_json(path.read_bytes())


def config_of(folder: Path) -> RunConfig:
    """Read the config of a results folder."""
    return RunConfig.model_validate_json((folder / "config.json").read_bytes())


def model_folder(folder: str, model: str, root: Path = REPO_ROOT) -> str:
    """Return the results folder in which the model repeats the Jev run of `folder`, relative to the repository.

    It is the latest folder of the model whose config differs from the config of the Jev run only by the model.
    """
    if model == JEV_MODEL:
        return folder
    wanted = config_of(root / folder).model_copy(update={"model": model})
    runs = (root / folder).parent
    parent = runs.with_name(f"{runs.name}_{RESULTS_MODEL_NAMES[model]}")
    same = [found for found in sorted(parent.iterdir()) if config_of(found) == wanted]
    if not same:
        raise FileNotFoundError(f"no folder in {parent} repeats {folder}")
    return str(same[-1].relative_to(root))


def uses(spec: RowSpec, name: str) -> bool:
    """Say whether the row uses the list of that name."""
    return name in spec.lists if spec.lists is not None else name.startswith(spec.list_prefix)


def keeps(spec: RowSpec, row: Row) -> bool:
    """Say whether the row uses the example."""
    low, high = spec.labels or (0, len(row.labels))
    return spec.test_file in (None, row.test_file) and low <= len(row.labels) <= high


def two(value: float) -> str:
    """Return a value with two decimals."""
    return f"{value:.2f}"


def signed(value: float) -> str:
    """Return a difference with its sign and two decimals, and 0.00 without a sign."""
    text = f"{value:+.2f}"
    return "0.00" if text in ("+0.00", "-0.00") else text


def three(values: tuple[float, ...]) -> str:
    """Return values with three decimals, separated by commas."""
    return ", ".join(f"{value:.3f}" for value in values)


def spanned(ends: tuple[int, int]) -> str:
    """Return a lowest and a highest count as one number or as a range."""
    return str(ends[0]) if ends[0] == ends[1] else f"{ends[0]} to {ends[1]}"


def note(found: Distribution) -> str:
    """Return the number of answers that a figure is measured on, when it leaves out answers."""
    return "" if found.measured == found.answers else f" ({found.measured} answers)"


def scored(found: Distribution, text: Callable[[Distribution], str]) -> str:
    """Return a cell about the prediction, which has no figure when every option is correct."""
    return ALL_CORRECT if found.kind is Kind.ALL else text(found)


def exact_text(found: Distribution) -> str:
    """Return the cell of the exact match, which exists for lists with several correct options."""
    texts = {Kind.ONE: ONE_CORRECT, Kind.ALL: ALL_CORRECT, Kind.NONE: NO_CORRECT}
    return two(found.exact_match) if found.exact_match is not None else texts[found.kind]


def margin_text(found: Distribution, value: float | None) -> str:
    """Return the cell of a difference between a correct option and the highest distractor."""
    if value is None:
        return NO_CORRECT if found.kind is Kind.NONE else NO_DISTRACTOR
    return signed(value) + note(found)


def spread_text(found: Distribution) -> str:
    """Return the cell of the highest probability of a correct option minus the lowest."""
    if found.kind in (Kind.NONE, Kind.ONE) or found.spread is None:
        return NO_CORRECT if found.kind is Kind.NONE else ONE_CORRECT
    return signed(found.spread) + note(found)


def ranked_text(found: Distribution) -> str:
    """Return the cell of the mean probability of each correct option, or of the highest and the lowest."""
    if found.highest_correct is None or found.lowest_correct is None:
        return NO_CORRECT
    if found.ranked_correct is not None:
        return three(found.ranked_correct) + note(found)
    return f"highest {found.highest_correct:.3f}, lowest {found.lowest_correct:.3f}" + note(found)


def distractor_text(found: Distribution) -> str:
    """Return the cell of the mean probability of the highest distractor."""
    return NO_DISTRACTOR if found.highest_distractor is None else f"{found.highest_distractor:.3f}" + note(found)


def position_text(found: Distribution, text: Callable[[Distribution], str]) -> str:
    """Return a cell with one value per position, for lists of one length below POSITIONS_SHOWN_BELOW."""
    if found.by_position is None or len(found.by_position) >= POSITIONS_SHOWN_BELOW:
        return f"not listed, {spanned(found.options)} options"
    return text(found)


# Column header -> the text of the column for the figures of the answers of one row.
COLUMNS: dict[str, Callable[[Distribution], str]] = {
    "Options in a list": lambda found: spanned(found.options),
    "Correct options in a list": lambda found: spanned(found.correct_options),
    "Accuracy": lambda found: scored(found, lambda found: two(found.accuracy or 0.0)),
    "Exact match": exact_text,
    "Mean confidence": lambda found: two(found.confidence),
    "Overconfidence": lambda found: scored(found, lambda found: signed(found.overconfidence or 0.0)),
    "ECE": lambda found: scored(found, lambda found: two(found.ece or 0.0)),
    "Mean entropy in bits": lambda found: two(found.entropy),
    "Highest correct minus lowest correct": spread_text,
    "Lowest correct minus highest distractor": lambda found: margin_text(found, found.lowest_margin),
    "Highest correct minus highest distractor": lambda found: margin_text(found, found.highest_margin),
    "Prediction minus runner-up": lambda found: two(found.runner_up),
    "Mean probability of each correct option, from the highest to the lowest": ranked_text,
    "Mean probability of the highest distractor": distractor_text,
    "Mean probability at each position, from the first to the last": lambda found: position_text(
        found, lambda found: three(found.by_position or ())
    ),
    "Answers with the prediction at each position, from the first to the last": lambda found: position_text(
        found, lambda found: ", ".join(map(str, found.predicted_at or ()))
    ),
}
HEADERS = [*LEADING_HEADERS, *COLUMNS, LAST_HEADER]


@dataclass(frozen=True)
class Selected:
    """The examples of one row of the table of a model, with the results folder that they are read from."""

    spec: RowSpec
    folder: str
    rows: list[Row]


@cache
def raw_types(path: Path) -> dict[str, str]:
    """Return the `type` of the raw row of each example of a processed test file, by the id of the example."""
    return {example.id: example.raw["type"] for example in read_jsonl(path, Example)}


def raw_type_of(row: Row) -> str:
    """Return the `type` of the raw row of the example, from the processed test file of its dataset."""
    dataset = row.id.split("/")[0]
    return raw_types(PROCESSED_DIRS[dataset] / f"{row.test_file}.jsonl")[row.id]


def selected(spec: RowSpec, model: str, root: Path = REPO_ROOT) -> Selected:
    """Return the examples that a row uses for a model, with their probabilities rounded."""
    folder = model_folder(spec.folder, model, root)
    rows = [rounded(row) for row in read_jsonl(root / folder / "rows.jsonl", Row) if keeps(spec, row)]
    if spec.raw_type:
        rows = [row for row in rows if raw_type_of(row) == spec.raw_type]
    return Selected(spec, folder, rows)


def unanswered(chosen: Selected) -> tuple[int, int]:
    """Return the number of lists of a row that the model rejected, and the number that it refused to answer."""
    rejected = sum(uses(chosen.spec, name) for row in chosen.rows for name in row.rejected)
    refused = sum(uses(chosen.spec, name) for row in chosen.rows for name in row.refused)
    return rejected, refused


def answers_of(chosen: Selected) -> dict[tuple[str, str, str], tuple[Row, ListAnswer]]:
    """Return the answers of a row with their examples, by results folder, id of the example and name of the list."""
    return {
        (chosen.folder, row.id, name): (row, answer)
        for row in chosen.rows
        for name, answer in row.answers.items()
        if uses(chosen.spec, name)
    }


def cells(chosen: Selected) -> list[str]:
    """Return the cells of one row of the table of a model."""
    answers = list(answers_of(chosen).values())
    counts = [f"{count:,}" for count in unanswered(chosen)]
    source = f"`{chosen.folder}`, {chosen.spec.lists_text}"
    if not answers:
        return [chosen.spec.label, "0", "0", *counts, *[NO_ANSWER] * len(COLUMNS), source]
    found = distribution(answers)
    examples = len({id(row) for row, _ in answers})
    figures = [cell(found) for cell in COLUMNS.values()]
    return [chosen.spec.label, str(examples), f"{len(answers):,}", *counts, *figures, source]


def summary(model: str, table: list[Selected]) -> str:
    """Return the sentence above the table of a model: its answers, and how often the prediction is not alone on top.

    An answer that several rows use is counted once. A rejected or refused list is counted once per row.
    """
    used = {key: answer for chosen in table for key, (_, answer) in answers_of(chosen).items()}
    below = tied = 0
    for answer in used.values():
        highest, own = max(answer.probabilities.values()), answer.probabilities[answer.choice]
        below += own < highest
        tied += own == highest and sum(value == highest for value in answer.probabilities.values()) > 1
    rejected, refused = (sum(counts) for counts in zip(*(unanswered(chosen) for chosen in table), strict=True))
    return (
        f"Model `{model}`. The table has {len(used):,} answers. The model rejected {rejected:,} lists and refused "
        f"{refused:,}, counted once per row that uses them. In {below} answers the prediction has a lower "
        f"probability than another option, and in {tied} it shares the highest probability with another option."
    )


def markdown(spec: TableSpec, root: Path = REPO_ROOT) -> str:
    """Return the document of a definition: the terms, one table per model, and the notes."""
    lines = [f"# {spec.title}", "", spec.intro, "", "## Terms", ""]
    lines += [f"- **{term}**: {text}" for term, text in spec.terms]
    for model in spec.models:
        table = [selected(row, model, root) for row in spec.rows if model in (row.models or spec.models)]
        lines += ["", f"## {MODEL_TITLES[model]}", "", summary(model, table), ""]
        lines += ["| " + " | ".join(HEADERS) + " |", "|" + "---|" * len(HEADERS)]
        lines += ["| " + " | ".join(cells(chosen)) + " |" for chosen in table]
    lines += ["", "## Notes", ""] + [f"- {text}" for text in spec.notes]
    return "\n".join(lines) + "\n"
