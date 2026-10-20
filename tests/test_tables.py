"""Tests for grjev.tables."""

from pathlib import Path

import pytest

from grjev.constants import (
    D1_MODEL,
    GATEWAY_MODELS,
    JEV_MODEL,
    LUNA_MODEL,
    POSITIONS_SHOWN_BELOW,
    PROCESSED_DIRS,
    TABLES_DIR,
)
from grjev.examples import Example
from grjev.results import write_run
from grjev.runs import ListAnswer, Row, RunConfig
from grjev.tables import (
    ALL_CORRECT,
    COLUMNS,
    HEADERS,
    NO_ANSWER,
    NO_CORRECT,
    NO_DISTRACTOR,
    ONE_CORRECT,
    RowSpec,
    TableSpec,
    cells,
    keeps,
    markdown,
    model_folder,
    read_spec,
    selected,
    signed,
    spanned,
    summary,
    uses,
)

JEV_FOLDER = "results/set_copied/2026-10-01_01"


def answer(probabilities: dict[str, float], correct: bool = False, choice: str | None = None) -> ListAnswer:
    selected_name = choice or max(probabilities, key=lambda name: probabilities[name])
    return ListAnswer(
        candidates=list(probabilities),
        choice=selected_name,
        probabilities=probabilities,
        confidence=1.0,
        correct=correct,
    )


def row(
    number: int,
    labels: list[str],
    answers: dict[str, ListAnswer],
    rejected: tuple[str, ...] = (),
    refused: tuple[str, ...] = (),
) -> Row:
    return Row(
        id=f"set/file/{number}",
        test_file="file",
        labels=labels,
        answers=answers,
        input_tokens=10,
        rejected=list(rejected),
        refused=list(refused),
    )


def write_folder(root: Path, folder: str, model: str, rows: list[Row], **changes: object) -> None:
    """Write a results folder with the config of a run of the model."""
    config = RunConfig.model_validate(
        {"experiment": "copied", "dataset": "set", "test_files": ("file",), "model": model} | changes
    )
    (root / folder).mkdir(parents=True)
    write_run(root / folder, config, {}, rows)


def results(tmp_path: Path) -> Path:
    """Write a Jev run with two examples, and its repeat on Liquid d1 in which every list is refused."""
    several = row(
        0, ["a", "b"], {"full": answer({"a": 0.7, "c": 0.2, "b": 0.1}), "other": answer({"a": 1.0, "b": 0.0})}
    )
    one = row(1, ["a"], {"full": answer({"b": 0.5, "a": 0.5}, choice="a")})
    write_folder(tmp_path, JEV_FOLDER, JEV_MODEL, [several, one])
    refused = [row(0, ["a", "b"], {}, refused=("full", "other")), row(1, ["a"], {}, rejected=("full",))]
    write_folder(tmp_path, "results/set_copied_d1/2026-10-02_01", D1_MODEL, refused)
    return tmp_path


def spec(**changes: object) -> RowSpec:
    return RowSpec.model_validate({"label": "Set", "folder": JEV_FOLDER, "lists_text": "list `full`"} | changes)


def test_the_folder_of_a_gateway_model_is_the_latest_one_that_repeats_the_config_of_the_jev_run(tmp_path: Path) -> None:
    write_folder(tmp_path, JEV_FOLDER, JEV_MODEL, [])
    # A config written before the field `examples` existed matches one that holds its default.
    config = tmp_path / JEV_FOLDER / "config.json"
    config.write_text(config.read_text().replace('"examples": null,', ""))
    assert '"examples"' not in config.read_text()
    for day, changes in (("01", {}), ("02", {}), ("03", {"examples_per_file": 50})):
        write_folder(tmp_path, f"results/set_copied_d1/2026-10-02_{day}", D1_MODEL, [], **changes)
    assert model_folder(JEV_FOLDER, JEV_MODEL, tmp_path) == JEV_FOLDER
    assert model_folder(JEV_FOLDER, D1_MODEL, tmp_path) == "results/set_copied_d1/2026-10-02_02"
    # A folder of the model with the name of the Jev folder is chosen over a later one.
    write_folder(tmp_path, "results/set_copied_d1/2026-10-01_01", D1_MODEL, [])
    assert model_folder(JEV_FOLDER, D1_MODEL, tmp_path) == "results/set_copied_d1/2026-10-01_01"
    write_folder(tmp_path, "results/set_copied_gpt-6-luna-decisions/2026-10-02_01", LUNA_MODEL, [], seed=7)
    with pytest.raises(FileNotFoundError, match="repeats results/set_copied/2026-10-01_01"):
        model_folder(JEV_FOLDER, LUNA_MODEL, tmp_path)


def test_a_row_uses_the_named_lists_or_a_prefix_and_the_examples_of_a_test_file_and_a_number_of_labels() -> None:
    assert uses(spec(lists=("full",)), "full") and not uses(spec(lists=("full",)), "full_may")
    assert uses(spec(list_prefix="5_"), "5_first") and not uses(spec(list_prefix="5_"), "50_first")
    assert uses(spec(), "anything")
    two_labels = row(0, ["a", "b"], {})
    assert keeps(spec(), two_labels) and keeps(spec(test_file="file", labels=(2, 99)), two_labels)
    assert not keeps(spec(labels=(1, 1)), two_labels) and not keeps(spec(test_file="other"), two_labels)


def test_the_cells_of_a_row_hold_its_counts_its_figures_and_its_source(tmp_path: Path) -> None:
    chosen = selected(spec(lists=("full",), labels=(2, 99)), JEV_MODEL, results(tmp_path))
    found = dict(zip(HEADERS, cells(chosen), strict=True))
    assert (found["Run"], found["Examples"], found["Answers"]) == ("Set", "1", "1")
    assert (found["Options in a list"], found["Correct options in a list"]) == ("3", "2")
    assert (found["Accuracy"], found["Exact match"], found["Mean confidence"]) == ("1.00", "0.00", "0.70")
    assert found["Highest correct minus lowest correct"] == "+0.60"
    assert found["Lowest correct minus highest distractor"] == "-0.10"
    assert found["Highest correct minus highest distractor"] == "+0.50"
    assert found["Mean probability of each correct option, from the highest to the lowest"] == "0.700, 0.100"
    assert found["Mean probability at each position, from the first to the last"] == "0.700, 0.200, 0.100"
    assert found["Answers with the prediction at each position, from the first to the last"] == "1, 0, 0"
    assert found["Results folder and lists"] == f"`{JEV_FOLDER}`, list `full`"


def test_a_cell_names_what_the_lists_lack_and_the_answers_that_a_figure_leaves_out(tmp_path: Path) -> None:
    root = results(tmp_path)
    every = dict(zip(HEADERS, cells(selected(spec(labels=(2, 99)), JEV_MODEL, root)), strict=True))
    # The list `other` holds only correct options and is left out of the differences with a distractor.
    assert every["Highest correct minus highest distractor"] == "+0.50 (1 answers)"
    assert every["Mean probability at each position, from the first to the last"] == "not listed, 2 to 3 options"
    only = dict(zip(HEADERS, cells(selected(spec(lists=("other",)), JEV_MODEL, root)), strict=True))
    assert (only["Accuracy"], only["ECE"], only["Exact match"]) == (ALL_CORRECT,) * 3
    assert only["Lowest correct minus highest distractor"] == only["Mean probability of the highest distractor"]
    assert only["Mean probability of the highest distractor"] == NO_DISTRACTOR
    one = dict(zip(HEADERS, cells(selected(spec(lists=("full",), labels=(1, 1)), JEV_MODEL, root)), strict=True))
    assert one["Exact match"] == one["Highest correct minus lowest correct"] == ONE_CORRECT
    assert (one["Accuracy"], one["Lowest correct minus highest distractor"]) == ("1.00", "0.00")


def test_a_row_whose_lists_have_no_answer_says_so_and_counts_the_rejected_and_refused_lists(tmp_path: Path) -> None:
    chosen = selected(spec(lists=("full",)), D1_MODEL, results(tmp_path))
    assert cells(chosen) == [
        "Set",
        "0",
        "0",
        "1",
        "1",
        *[NO_ANSWER] * len(COLUMNS),
        "`results/set_copied_d1/2026-10-02_01`, list `full`",
    ]


def test_lists_without_a_correct_option_and_long_lists_are_named_in_their_cells(tmp_path: Path) -> None:
    long = {f"tool_{number}": 1 / POSITIONS_SHOWN_BELOW for number in range(POSITIONS_SHOWN_BELOW)}
    write_folder(tmp_path, JEV_FOLDER, JEV_MODEL, [row(0, [], {"full": answer(long)})])
    found = dict(zip(HEADERS, cells(selected(spec(), JEV_MODEL, tmp_path)), strict=True))
    assert (found["Accuracy"], found["Exact match"]) == ("0.00", NO_CORRECT)
    assert (
        found["Highest correct minus lowest correct"] == found["Lowest correct minus highest distractor"] == NO_CORRECT
    )
    assert found["Mean probability of the highest distractor"] == "0.100"
    assert found["Mean probability at each position, from the first to the last"] == "not listed, 10 options"


def test_the_summary_counts_an_answer_once_and_the_predictions_that_are_not_alone_on_top(tmp_path: Path) -> None:
    root = results(tmp_path)
    table = [selected(spec(), JEV_MODEL, root), selected(spec(lists=("full",)), JEV_MODEL, root)]
    text = summary(JEV_MODEL, table)
    assert "The table has 3 answers. The model rejected 0 lists and refused 0" in text
    assert "In 0 answers the prediction has a lower probability than another option, and in 1 it shares" in text
    refused = [selected(spec(), D1_MODEL, root), selected(spec(lists=("full",)), D1_MODEL, root)]
    assert "The table has 0 answers. The model rejected 2 lists and refused 3" in summary(D1_MODEL, refused)


def test_the_document_has_the_terms_one_table_per_model_and_the_notes(tmp_path: Path) -> None:
    definition = TableSpec(
        title="Runs",
        intro="Two runs.",
        terms=[("Option", "one entry of a list.")],
        notes=["A note."],
        models=(JEV_MODEL, D1_MODEL),
        rows=[spec(lists=("full",)), spec(label="Jev only", models=(JEV_MODEL,))],
    )
    lines = markdown(definition, results(tmp_path)).split("\n")
    assert lines[:6] == ["# Runs", "", "Two runs.", "", "## Terms", ""]
    assert lines[6] == "- **Option**: one entry of a list." and lines[-4:] == ["## Notes", "", "- A note.", ""]
    assert [line for line in lines if line.startswith("## ")] == ["## Terms", "## Jev", "## Liquid d1", "## Notes"]
    tables = [line for line in lines if line.startswith("| ")]
    assert [line.split(" | ")[0] for line in tables] == ["| Run", "| Set", "| Jev only", "| Run", "| Set"]
    assert all(line.count(" | ") == len(HEADERS) - 1 for line in tables)


def test_a_difference_keeps_its_sign_except_at_zero_and_a_range_of_one_count_is_that_count() -> None:
    assert [signed(value) for value in (0.126, -0.5, 0.001, -0.001)] == ["+0.13", "-0.50", "0.00", "0.00"]
    assert (spanned((5, 5)), spanned((6, 16))) == ("5", "6 to 16")


def test_the_definition_of_the_table_of_every_run_names_38_runs_of_jev_and_37_of_each_gateway_model() -> None:
    definition = read_spec(TABLES_DIR / "all_runs.json")
    assert definition.models == (JEV_MODEL, *GATEWAY_MODELS)
    assert len(definition.rows) == 38
    assert sum(row.models is None for row in definition.rows) == 37
    assert all(row.folder.startswith("results/") for row in definition.rows)


def test_a_row_with_a_raw_type_keeps_the_examples_whose_raw_row_has_that_type(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = results(tmp_path)
    processed = tmp_path / "processed"
    processed.mkdir()
    examples = [
        Example(id=f"set/file/{number}", query="q", options=[], labels=[], raw={"type": kind})
        for number, kind in ((0, "bridge"), (1, "comparison"))
    ]
    (processed / "file.jsonl").write_text("".join(example.model_dump_json() + "\n" for example in examples))
    monkeypatch.setitem(PROCESSED_DIRS, "set", processed)
    assert [found.id for found in selected(spec(raw_type="bridge"), JEV_MODEL, root).rows] == ["set/file/0"]
    assert [found.id for found in selected(spec(raw_type="comparison"), JEV_MODEL, root).rows] == ["set/file/1"]
