"""Tests for grjev.report."""

from pathlib import Path

from grjev.constants import ALLOCATION_RUNS, D1_MODEL, JEV_MODEL, LUNA_MODEL, TABLES_DIR, TOOLS_FILE_NAME
from grjev.examples import Example, Option, write_jsonl
from grjev.report import (
    ENTROPY_HEADER,
    MEASURED_HEADER,
    PAPER_COLUMNS,
    PAPER_LATEX_HEADERS,
    POSITION_HEADERS,
    chart_svg,
    finding_html,
    lists_table,
    page,
    paper_latex,
    paper_table,
    run_html,
    second_correct_table,
    spans,
    yes_no_table,
)
from grjev.results import write_run
from grjev.runs import ListAnswer, Row, RunConfig
from grjev.tables import FindingSpec, PaperTableSpec, RowSpec, TableSpec, read_spec, selected

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


def test_a_list_that_the_model_rejected_is_not_counted_as_refused(tmp_path: Path) -> None:
    first = Row(
        id="set/file/0", test_file="file", labels=["a"], answers={"full": answer({"a": 0.7, "b": 0.3})}, input_tokens=1
    )
    write_folder(tmp_path, JEV_FOLDER, JEV_MODEL, [first])
    write_folder(tmp_path, D1_FOLDER, D1_MODEL, [first.model_copy(update={"answers": {}, "rejected": ["full"]})])
    own = spec(lists=("full",))
    assert lists_table(own, chosen(tmp_path, own))[2][:3] == ["Liquid d1", "0", "0"]
    assert yes_no_table(own, chosen(tmp_path, own))[2][:3] == ["Liquid d1", "0", "0"]


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
    # The options other than a hold 0.3 of the full list, and b holds 0.1 of it.
    assert second[1] == ["Jev", "1", "0.10", "0.60", "1", "0.33", "0.60"]
    assert second[2] == ["Liquid d1", "0", "none", "none", "0", "none", "none"]


def test_the_table_of_a_finding_has_one_row_per_model_and_the_columns_of_each_run_under_its_name(
    tmp_path: Path,
) -> None:
    own = spec(lists=("full",), positions=True)
    removal = spec(label="Removal", figures="second_correct")
    root = results(tmp_path)
    runs = {"Set": chosen(root, own), "Removal": chosen(root, removal)}
    columns = ["Predictions at the first position", "Highest correct option", "Lowest correct option", "Lists refused"]
    moved = ["After the removal", "Full list, renormalised"]
    table = PaperTableSpec.model_validate(
        {
            "caption": "Two runs.",
            "parts": [
                {"run": "Set", "name": "The full list", "columns": columns},
                {"run": "Removal", "name": "Without a", "columns": moved},
            ],
        }
    )
    block = paper_table(table, runs)
    assert '<p class="caption">Two runs.</p>' in block and block.count("<tr>") == 4
    assert '<th class="edge" colspan="4">The full list</th><th class="edge" colspan="2">Without a</th>' in block
    jev = '<td class="edge">100%</td><td>0.70</td><td>0.10</td><td>0%</td><td class="edge">0.60</td><td>0.33</td>'
    assert f"<tr><th>Jev</th>{jev}</tr>" in block
    # Liquid d1 refused the list without a, and the run of the removal counts its 2 refused lists of 3.
    assert '<td>0%</td><td class="edge">none</td><td>none</td></tr>' in block


def test_the_block_of_a_run_names_its_lists_its_instruction_and_its_folder(tmp_path: Path) -> None:
    own = spec(lists=("full",), about="The list of the example.", instruction="Choose <one> tool.")
    block = run_html(own, chosen(results(tmp_path), own))
    assert "<h3>Set</h3>" in block and 'Instruction: "Choose &lt;one&gt; tool."' in block
    assert "The list of the example. 1 examples and 1 lists. Each list has 3 options." in block
    assert "The number of correct options in a list is 2." in block
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
    assert "Table for the paper" not in block
    table = {"caption": "One run.", "parts": [{"run": "Set", "name": "Set", "columns": ["Mean confidence"]}]}
    with_table = finding().model_copy(update={"tables": [PaperTableSpec.model_validate(table)]})
    assert "<h3>Table for the paper</h3>" in finding_html(with_table, {"Set": own}, runs, tmp_path, processed(tmp_path))
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


def test_the_definition_of_the_runs_on_every_example_names_53_tables_for_three_models() -> None:
    definition = read_spec(TABLES_DIR / "paper_runs.json")
    assert definition.models == (JEV_MODEL, D1_MODEL, LUNA_MODEL) and len(definition.rows) == 53
    assert len({row.label for row in definition.rows}) == 53 and len({row.group for row in definition.rows}) == 6
    assert all(row.instruction for row in definition.rows if row.figures != "second_correct")
    # The MetaTool yes/no run was added on 2026-10-14, the copies with random IDs as names on 2026-10-19, the MMLU
    # copies with spaces, rebuilt from the saved responses of 2026-10-11, on 2026-10-20, the MetaTool placements on
    # 2026-10-22, and the HotpotQA cyclic permutations on 2026-10-24.
    dated = (
        "/2026-10-11_",
        "yes_no",
        "_copied/2026-10-19_",
        "_copied_spaced/2026-10-20_",
        "_mixed/2026-10-22_",
        "_own/2026-10-24_",
    )
    assert all(row.about and any(part in row.folder for part in dated) for row in definition.rows)
    labels = {row.label for row in definition.rows}
    assert len(definition.findings) == 6 and len(definition.conclusions) == 8
    assert all(run in labels for found in definition.findings for run, _ in found.chart.runs)
    assert all(found.example.run in labels and found.evidence and found.limits for found in definition.findings)
    parts = [part for found in definition.findings for table in found.tables for part in table.parts]
    assert all(found.tables for found in definition.findings) and all(part.run in labels for part in parts)
    assert all(header in PAPER_COLUMNS for part in parts for header in part.columns)
    assert all(run in labels for found in definition.findings for table in found.yes_bins for run, _ in table.runs)


def test_the_latex_table_of_a_finding_groups_its_parts_and_escapes_the_percent_sign(tmp_path: Path) -> None:
    own = spec(lists=("full",), positions=True)
    runs = {"Set": chosen(results(tmp_path), own)}
    parts = [
        {"run": "Set", "name": "Set, full list", "short": "Set", "group": "One group", "columns": ["Lists refused"]},
        {"run": "Set", "name": "Again", "group": "One group", "columns": ["Highest correct option", "Mean confidence"]},
    ]
    lines = paper_latex(PaperTableSpec.model_validate({"caption": "Two parts.", "parts": parts}), runs).splitlines()
    assert lines[:2] == [r"\begin{tabular}{lrrr}", r"\toprule"]
    assert lines[2:4] == [r" & \multicolumn{3}{c}{One group} \\", r"\cmidrule(lr){2-4}"]
    assert lines[4] == r" & \multicolumn{1}{c}{Set} & \multicolumn{2}{c}{Again} \\"
    assert lines[5:8] == [r"\cmidrule(lr){2-2} \cmidrule(lr){3-4}", r"Model & Refused & High & Conf. \\", r"\midrule"]
    assert lines[8:] == [
        r"Jev & 0\% & 0.70 & 0.70 \\",
        r"Liquid d1 & 0\% & 0.70 & 0.70 \\",
        r"\bottomrule",
        r"\end{tabular}",
    ]
    assert set(PAPER_COLUMNS) == set(PAPER_LATEX_HEADERS)


def test_the_latex_table_gives_gaps_in_points_the_lists_ranked_correctly_and_the_headers_of_a_part(
    tmp_path: Path,
) -> None:
    # The label of the HotpotQA run of ALLOCATION_RUNS, which counts every list of a row. Only the full list holds a
    # distractor. In it a gets 0.7 and b 0.1, below the distractor c at 0.2, so the list is not ranked correctly and
    # no list is left for the share below 1/n.
    own = spec(label=ALLOCATION_RUNS["HotpotQA"][0], lists=("full",), positions=True)
    runs = {"Set": chosen(results(tmp_path), own)}
    columns = [
        "Highest correct minus lowest correct, in points",
        "Lists with every correct option above every distractor",
        "Of those, lists with a correct option below 1/n",
        "Predictions at the first position",
    ]
    parts = [{"run": "Set", "name": "Set", "columns": columns, "heads": ["Gap", "Ranked", "Below", "Lead"]}]
    lines = paper_latex(PaperTableSpec.model_validate({"caption": "One part.", "parts": parts}), runs).splitlines()
    assert lines[4] == r"Model & Gap & Ranked & Below & Lead \\"
    assert lines[6] == r"Jev & 60 & 0\% & none & 100\% \\"


def test_neighbouring_parts_with_the_same_name_share_a_header_only_within_one_group() -> None:
    assert spans(["A", "A"], [1, 2])[0] == r" & \multicolumn{3}{c}{A} \\"
    assert spans(["A", "A"], [1, 2], ["x", "y"])[0] == r" & \multicolumn{1}{c}{A} & \multicolumn{2}{c}{A} \\"
