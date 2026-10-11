"""Tests for grjev.report."""

from pathlib import Path

from grjev.constants import D1_MODEL, JEV_MODEL, LUNA_MODEL, TABLES_DIR
from grjev.report import (
    ENTROPY_HEADER,
    MEASURED_HEADER,
    POSITION_HEADERS,
    lists_table,
    page,
    run_html,
    second_correct_table,
    yes_no_table,
)
from grjev.results import write_run
from grjev.runs import ListAnswer, Row, RunConfig
from grjev.tables import ChartSpec, RowSpec, TableSpec, read_spec, selected

JEV_FOLDER = "results/set_removal/2026-10-01_01"
D1_FOLDER = "results/set_removal_d1/2026-10-02_01"


def answer(probabilities: dict[str, float], correct: bool = False) -> ListAnswer:
    choice = max(probabilities, key=lambda name: probabilities[name])
    return ListAnswer(
        candidates=list(probabilities), choice=choice, probabilities=probabilities, confidence=1.0, correct=correct
    )


def write_folder(root: Path, folder: str, model: str, rows: list[Row]) -> None:
    config = RunConfig(experiment="removal", dataset="set", test_files=("file",), model=model)
    (root / folder).mkdir(parents=True)
    write_run(root / folder, config, {}, rows)


def results(tmp_path: Path) -> Path:
    """Write a Jev run of two examples, and its repeat on Liquid d1 with one list refused."""
    full = answer({"a": 0.7, "c": 0.2, "b": 0.1})
    lists = {
        "full": full,
        "without_1": answer({"b": 0.6, "c": 0.4}, correct=True),
        "pair": answer({"a": 0.5, "b": 0.5}),
    }
    first = Row(id="set/file/0", test_file="file", labels=["a", "b"], answers=lists, input_tokens=1)
    yes = Row(id="set/file/1", test_file="file", labels=["a"], answers={}, input_tokens=1, yes={"a": 0.8, "c": 0.5})
    write_folder(tmp_path, JEV_FOLDER, JEV_MODEL, [first, yes])
    refused = first.model_copy(update={"answers": {"full": full}, "refused": ["without_1", "pair"]})
    write_folder(tmp_path, D1_FOLDER, D1_MODEL, [refused, yes.model_copy(update={"yes": {}, "refused": ["a", "c"]})])
    return tmp_path


def spec(**changes: object) -> RowSpec:
    return RowSpec.model_validate({"label": "Set", "folder": JEV_FOLDER, "lists_text": "every list"} | changes)


def chosen(root: Path, own: RowSpec) -> dict:
    return {model: selected(own, model, root) for model in (JEV_MODEL, D1_MODEL)}


def test_the_table_of_a_run_has_one_row_per_model_and_only_the_figures_that_its_lists_have(tmp_path: Path) -> None:
    own = spec(lists=("full",))
    header, jev, d1 = lists_table(own, chosen(results(tmp_path), own))
    assert header[:3] == ["Model", "Lists answered", "Lists refused"] and "Exact match" in header
    assert f"{ENTROPY_HEADER} (maximum 1.58)" in header
    # The list has 3 options in one order: no column by position, and every list has a distractor.
    assert not set(POSITION_HEADERS) & set(header) and MEASURED_HEADER not in header
    found = dict(zip(header, jev, strict=True))
    assert (found["Model"], found["Lists answered"], found["Lists refused"]) == ("Jev", "1", "0")
    assert (found["Prediction minus runner-up"], found["Highest correct minus lowest correct"]) == ("0.50", "+0.60")
    assert found["Highest correct minus highest distractor"] == "+0.50"
    assert found["Lowest correct minus highest distractor"] == "-0.10"
    assert d1[:3] == ["Liquid d1", "1", "0"] and d1[3:] == jev[3:]


def test_a_refused_list_is_counted_and_a_model_with_no_answer_has_no_figure(tmp_path: Path) -> None:
    own = spec(lists=("without_1",), positions=True)
    header, jev, d1 = lists_table(own, chosen(results(tmp_path), own))
    assert set(POSITION_HEADERS) <= set(header) and "Exact match" not in header
    assert dict(zip(header, jev, strict=True))[POSITION_HEADERS[1]] == "1, 0"
    assert d1[:3] == ["Liquid d1", "0", "1"] and set(d1[3:]) == {"none"}


def test_the_lists_that_hold_only_correct_options_are_counted_apart_from_the_differences(tmp_path: Path) -> None:
    own = spec(lists=("full", "pair"))
    header, jev, _ = lists_table(own, chosen(results(tmp_path), own))
    found = dict(zip(header, jev, strict=True))
    assert (found["Lists answered"], found[MEASURED_HEADER]) == ("2", "1")
    assert found["Highest correct minus highest distractor"] == "+0.50"


def test_the_yes_no_table_and_the_table_of_the_second_correct_option_have_one_row_per_model(tmp_path: Path) -> None:
    root = results(tmp_path)
    yes_no = yes_no_table(spec(), chosen(root, spec()))
    assert yes_no[1] == ["Jev", "2", "0", "0.80", "1 of 1", "0.50", "1 of 1"]
    assert yes_no[2] == ["Liquid d1", "0", "4", "none", "0 of 0", "none", "0 of 0"]
    second = second_correct_table(spec(), chosen(root, spec()))
    # The top correct option of the full list is a, the first label, so the list without it is `without_1`.
    assert second[1] == ["Jev", "1", "0.10", "0.60"] and second[2] == ["Liquid d1", "0", "none", "none"]


def test_the_block_of_a_run_names_its_lists_its_instruction_and_its_folder(tmp_path: Path) -> None:
    own = spec(lists=("full",), about="The list of the example.", instruction="Choose <one> tool.")
    block = run_html(own, chosen(results(tmp_path), own))
    assert "<h3>Set</h3>" in block and 'Instruction: "Choose &lt;one&gt; tool."' in block
    assert "The list of the example. 1 examples, 1 lists. Options in a list: 3. Correct options in a list: 2." in block
    assert f"<code>{JEV_FOLDER}</code>, every list" in block and block.count("<tr>") == 3


def test_the_page_puts_the_runs_under_their_groups_between_the_terms_and_the_notes(tmp_path: Path) -> None:
    definition = TableSpec(
        title="Runs",
        intro="Two runs.",
        terms=[("Option", "one entry of a list.")],
        notes=["A note."],
        models=(JEV_MODEL, D1_MODEL),
        rows=[
            spec(group="1. Lists", lists=("full",)),
            spec(group="1. Lists", label="Pair", lists=("pair",)),
            spec(group="2. Yes or no", label="Asked", figures="yes_no"),
        ],
    )
    text = page(definition, results(tmp_path))
    assert [text.count(tag) for tag in ("<h1>", "<h2>", "<section>", "<table>")] == [1, 4, 3, 3]
    assert text.index("<h2>Terms</h2>") < text.index("<h2>1. Lists</h2>") < text.index("<h2>2. Yes or no</h2>")
    assert text.index("<h2>2. Yes or no</h2>") < text.index("<h2>Notes</h2>") < text.index("<li>A note.</li>")


def test_the_page_draws_the_charts_of_its_definition_before_the_terms(tmp_path: Path) -> None:
    runs = [("Set", "Set, full list")]
    definition = TableSpec(
        title="Runs",
        intro="One run.",
        terms=[],
        notes=[],
        models=(JEV_MODEL, D1_MODEL),
        rows=[spec(lists=("full",), positions=True)],
        charts=[
            ChartSpec(kind=kind, title=f"Chart of {kind}", about="What it shows.", runs=runs)
            for kind in ("positions", "correct_span", "second_correct", "confidence", "overconfidence")
        ],
    )
    text = page(definition, results(tmp_path))
    assert text.count("<figure") == 5 and text.count("<svg") == 5 and text.count('<figure class="wide">') == 1
    assert (
        text.index("<h2>Summary charts</h2>") < text.index("<h3>Chart of positions</h3>") < text.index("<h2>Terms</h2>")
    )
    # The lowest and the highest correct option of the full list, and its second correct option after the removal.
    assert all(f">{value}</text>" in text for value in ("0.10", "0.70", "0.60", "Set, full list"))
    assert "<h2>Summary charts</h2>" not in page(definition.model_copy(update={"charts": []}), tmp_path)


def test_the_definition_of_the_runs_on_every_example_names_43_tables_for_three_models() -> None:
    definition = read_spec(TABLES_DIR / "paper_runs.json")
    assert definition.models == (JEV_MODEL, D1_MODEL, LUNA_MODEL) and len(definition.rows) == 43
    assert len({row.label for row in definition.rows}) == 43 and len({row.group for row in definition.rows}) == 5
    assert all(row.instruction for row in definition.rows if row.figures != "second_correct")
    assert all(row.about and "/2026-10-11_" in row.folder for row in definition.rows)
    labels = {row.label for row in definition.rows}
    assert len(definition.charts) == 5 and all(run in labels for chart in definition.charts for run, _ in chart.runs)
