"""Tests for grjev.figure."""

import pytest

from grjev.constants import D1_MODEL, JEV_MODEL
from grjev.figure import SCALE, Marks, figure_tikz, marks_of
from grjev.runs import ListAnswer, Row
from grjev.tables import RowSpec, Selected


def answer(probabilities: dict[str, float]) -> ListAnswer:
    choice = max(probabilities, key=lambda name: probabilities[name])
    return ListAnswer(
        candidates=list(probabilities), choice=choice, probabilities=probabilities, confidence=1.0, correct=False
    )


def chosen(lists: tuple[str, ...] | None, removed: bool = True) -> dict[str, Selected]:
    """Return one example with two correct options, a and b, for Jev: its full list and the list without a."""
    answers = {"full": answer({"a": 0.7, "c": 0.2, "b": 0.1})}
    if removed:
        answers["without_1"] = answer({"b": 0.6, "c": 0.4})
    row = Row(id="set/file/0", test_file="file", labels=["a", "b"], answers=answers, input_tokens=1)
    spec = RowSpec(label="Set", folder="results/set/2026-10-01_01", lists_text="every list", lists=lists)
    return {JEV_MODEL: Selected(spec, spec.folder, [row])}


def test_the_marks_of_a_model_come_from_the_full_list_and_from_the_list_without_the_top_correct_option() -> None:
    assert marks_of(chosen(("full",)), chosen(None)) == {JEV_MODEL: Marks(0.1, 0.7, 0.2, 0.1, 0.6)}
    with pytest.raises(ValueError, match="no removal"):
        marks_of(chosen(("full",)), chosen(None, removed=False))


def test_the_picture_has_one_row_per_model_with_its_marks_on_the_scale_and_the_threshold() -> None:
    marks = {JEV_MODEL: Marks(0.1, 0.7, 0.2, 0.1, 0.6), D1_MODEL: Marks(0.2, 0.5, 0.1, 0.2, 0.4)}
    lines = figure_tikz([("Set, 2 correct options", marks)]).splitlines()
    assert lines[0] == r"\definecolor{model0}{HTML}{2A78D6}" and lines[-1] == r"\end{tikzpicture}"
    assert r"\node[anchor=east, font=\footnotesize\bfseries] at (-0.15,-0.50) {Set, 2 correct options};" in lines
    # The first row is 0.44 cm under the name of the run, and the scale from 0 to 1 is SCALE cm long.
    assert rf"\draw[model0, line width=1pt] ({0.1 * SCALE:.3f},-0.94) -- ({0.7 * SCALE:.3f},-0.94);" in lines
    assert rf"\draw[black, line width=0.9pt] ({0.2 * SCALE:.3f},-1.03) -- ({0.2 * SCALE:.3f},-0.85);" in lines
    arrow = rf"({0.2 * SCALE:.3f},-1.53) -- ({0.4 * SCALE:.3f},-1.53);"
    assert any(line.startswith(r"\draw[black!55, densely dashed") and line.endswith(arrow) for line in lines)
    assert r"\node[anchor=east] at (-0.15,-1.38) {Liquid d1};" in lines
    assert any(f"({0.25 * SCALE:.3f},0.05) node[above] {{threshold 0.25}}" in line for line in lines)
