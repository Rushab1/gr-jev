"""Tests for grjev.report."""

from pathlib import Path

from grjev.constants import D1_MODEL, JEV_MODEL, LUNA_MODEL, TABLES_DIR, TOOLS_FILE_NAME
from grjev.examples import Example, Option, write_jsonl
from grjev.report import (
    ENTROPY_HEADER,
    MEASURED_HEADER,
    POSITION_HEADERS,
    chart_svg,
    finding_html,
    lists_table,
    page,
    run_html,
    second_correct_table,
    yes_no_table,
)
from grjev.results import write_run
from grjev.runs import ListAnswer, Row, RunConfig
from grjev.tables import FindingSpec, RowSpec, TableSpec, read_spec, selected

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


def test_the_page_puts_the_runs_under_their_groups_after_the_terms_and_the_notes(tmp_path: Path) -> None:
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
    assert [text.count(tag) for tag in ("<h1>", "<h2>", "<section>", "<table>")] == [2, 4, 3, 3]
    order = ["<h2>Terms</h2>", "<h2>Notes</h2>", "<li>A note.</li>", "<h1>Tables by run</h1>"]
    order += ["<h2>1. Lists</h2>", "<h3>Pair</h3>", "<h2>2. Yes or no</h2>"]
    assert [text.index(part) for part in order] == sorted(text.index(part) for part in order)


def processed(tmp_path: Path) -> dict[str, Path]:
    """Write the processed files of the dataset of the runs: the two examples and their three options."""
    options = [Option(name=name, description=f"Does thing {name}, at length.") for name in ("a", "b", "c")]
    first = Example(id="set/file/0", query="Do   a thing <now>.", options=options, labels=["a", "b"], raw={})
    second = Example(id="set/file/1", query="Do another thing.", options=options, labels=["a"], raw={})
    folder = tmp_path / "processed"
    write_jsonl(folder / "file.jsonl", [first, second])
    write_jsonl(folder / TOOLS_FILE_NAME, options)
    return {"set": folder}


def finding(kind: str = "correct_span") -> FindingSpec:
    return FindingSpec.model_validate(
        {
            "title": "1. Allocation",
            "strength": "strong.",
            "conclusion": "One correct option takes most.",
            "evidence": ["0.70 and 0.10."],
            "limits": ["One run."],
            "chart": {"kind": kind, "title": "Lowest and highest", "runs": [("Set", "Set, full list")]},
            "example": {
                "run": "Set",
                "id": "set/file/0",
                "lists": [("full", "The full list"), ("without_1", "Without a")],
                "about": "The first example.",
            },
        }
    )


def test_a_finding_has_its_conclusion_its_chart_and_one_example_with_the_probabilities_of_each_model(
    tmp_path: Path,
) -> None:
    own = spec(lists=("full",), instruction="Choose every tool.")
    runs = {"Set": chosen(results(tmp_path), own)}
    block = finding_html(finding(), {"Set": own}, runs, tmp_path, processed(tmp_path))
    assert "<h2>1. Allocation</h2>" in block and "<b>Strength for the paper:</b> strong." in block
    assert block.count("<svg") == 1 and "<li>0.70 and 0.10.</li>" in block and "<li>One run.</li>" in block
    # The query is shown on one line, and the options in the order sent with their text.
    assert "<b>Query.</b> Do a thing &lt;now&gt;." in block and "<b>Instruction.</b> Choose every tool." in block
    assert '<b>a</b> <span class="tag">correct</span> Does thing a, at length.' in block
    assert "<b>c</b> Does thing c, at length." in block
    # Jev predicts a in the full list and b without a. Liquid d1 refused the list without a.
    assert "<td><b>0.70</b></td><td><b>0.70</b></td>" in block
    assert "<td><b>0.60</b></td><td>refused</td>" in block and "<td>0.40</td><td>refused</td>" in block


def test_each_kind_of_chart_is_drawn_from_the_runs_that_it_names(tmp_path: Path) -> None:
    own = spec(lists=("full",), positions=True)
    runs = {"Set": chosen(results(tmp_path), own)}
    texts = {
        "positions": ("100%", "Set, full list"),
        "correct_span": ("0.10", "0.70", "lowest correct option"),
        "second_correct": ("0.10", "0.60", "after the removal"),
        "confidence": ("0.70",),
        "calibration": ("1.00", "0.70", "mean confidence"),
    }
    for kind, expected in texts.items():
        chart = chart_svg(finding(kind).chart, runs)
        assert chart.startswith("<svg") and all(text in chart for text in expected), kind


def test_the_page_puts_the_conclusions_and_the_findings_before_the_terms_and_the_tables(tmp_path: Path) -> None:
    definition = TableSpec(
        title="Runs",
        intro="One run.",
        terms=[("Option", "one entry of a list.")],
        notes=["A note."],
        models=(JEV_MODEL, D1_MODEL),
        rows=[spec(lists=("full",))],
        conclusions=["Order decides.", "One option takes most."],
        findings=[finding()],
    )
    text = page(definition, results(tmp_path), processed(tmp_path))
    order = ["<h2>Conclusions</h2>", "<li>Order decides.</li>", "<h2>1. Allocation</h2>", "<h2>Terms</h2>"]
    order += ["<h2>Notes</h2>", '<div class="tables">', "<h3>Set</h3>"]
    assert [text.index(part) for part in order] == sorted(text.index(part) for part in order)
    assert "size: A4 portrait" in text and "size: A4 landscape" in text
    assert "<h2>Conclusions</h2>" not in page(
        definition.model_copy(update={"conclusions": [], "findings": []}), tmp_path
    )


def test_the_definition_of_the_runs_on_every_example_names_48_tables_for_three_models() -> None:
    definition = read_spec(TABLES_DIR / "paper_runs.json")
    assert definition.models == (JEV_MODEL, D1_MODEL, LUNA_MODEL) and len(definition.rows) == 48
    assert len({row.label for row in definition.rows}) == 48 and len({row.group for row in definition.rows}) == 6
    assert all(row.instruction for row in definition.rows if row.figures != "second_correct")
    assert all(row.about and "/2026-10-11_" in row.folder for row in definition.rows)
    labels = {row.label for row in definition.rows}
    assert len(definition.findings) == 6 and len(definition.conclusions) == 8
    assert all(run in labels for found in definition.findings for run, _ in found.chart.runs)
    assert all(found.example.run in labels and found.evidence and found.limits for found in definition.findings)
