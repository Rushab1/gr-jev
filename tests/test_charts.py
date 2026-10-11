"""Tests for grjev.charts."""

from grjev.charts import bars_chart, positions_chart, spans_chart
from grjev.constants import D1_MODEL, JEV_MODEL, MODEL_COLORS


def test_the_chart_by_position_has_a_bar_per_model_run_and_position_and_labels_the_highest_of_a_row() -> None:
    panels = {
        "MetaTool": {JEV_MODEL: [0.1, 0.2, 0.7], D1_MODEL: [1.0, 0.0, 0.0]},
        "MMLU": {JEV_MODEL: [0.3, 0.3, 0.4], D1_MODEL: [0.9, 0.05, 0.05]},
    }
    chart = positions_chart("Share of the predictions at each position.", panels)
    assert chart.startswith("<svg") and "<title>Share of the predictions at each position.</title>" in chart
    assert chart.count("<path") == 12
    assert all(f">{text}</text>" in chart for text in ("70%", "100%", "40%", "90%", "MetaTool", "MMLU", "Liquid d1"))
    assert ">20%</text>" not in chart and "<title>Jev, position 3: 70%</title>" in chart
    assert chart.count(f'fill="{MODEL_COLORS[JEV_MODEL]}"') == 6 + 1


def test_a_chart_of_bars_has_a_bar_per_run_and_model_with_its_text_and_a_line_at_0() -> None:
    groups = {
        "One correct tool": {JEV_MODEL: (0.08, "+0.08"), D1_MODEL: (-0.2, "-0.20")},
        "Two correct tools": {JEV_MODEL: (0.0, "0.00")},
    }
    chart = bars_chart("Mean confidence minus accuracy.", groups, -0.3, 0.3)
    assert chart.count("<path") == 3 and chart.count("<line") == 1
    assert all(f">{text}</text>" in chart for text in ("One correct tool", "Two correct tools", "+0.08", "-0.20"))
    assert "<title>One correct tool, Liquid d1: -0.20</title>" in chart


def test_a_chart_of_spans_has_a_hollow_and_a_filled_marker_per_run_and_model_with_both_values() -> None:
    groups = {"HotpotQA": {JEV_MODEL: (0.17, 0.77), D1_MODEL: (0.19, 0.74)}}
    chart = spans_chart(
        "Lowest and highest correct option.", groups, ("lowest correct option", "highest correct option")
    )
    assert chart.count("<circle") == 4 and chart.count('fill="#ffffff"') == 2
    assert all(f">{text}</text>" in chart for text in ("0.17", "0.77", "0.19", "0.74", "HotpotQA"))
    assert "hollow marker: lowest correct option; filled marker: highest correct option" in chart
