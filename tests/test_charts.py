"""Tests for grjev.charts."""

from grjev.charts import SCALE_END, SCALE_START, TICKS, across, bars_chart, positions_chart, spans_chart
from grjev.constants import D1_MODEL, JEV_MODEL, MODEL_COLORS


def test_every_chart_with_rows_draws_a_value_at_the_same_place_on_one_scale_from_0_to_1() -> None:
    assert (across(0), across(1), across(0.5)) == (SCALE_START, SCALE_END, (SCALE_START + SCALE_END) / 2)
    bars = bars_chart("Confidence.", {"Run": {JEV_MODEL: (0.5, "0.50")}})
    spans = spans_chart("Spread.", {"Run": {JEV_MODEL: (0.1, 0.5)}}, ("lowest", "highest"))
    for chart in (bars, spans):
        assert all(f'x1="{across(tick):.1f}" x2="{across(tick):.1f}"' in chart for tick in TICKS)
        assert all(f">{tick:.2f}</text>" in chart for tick in TICKS)
    assert f"H{across(0.5) - 3:.1f}" in bars and f'cx="{across(0.5):.1f}"' in spans


def test_the_chart_by_position_has_a_bar_per_model_run_and_position_and_labels_the_highest_of_a_row() -> None:
    panels = {
        "MetaTool": {JEV_MODEL: [0.1, 0.2, 0.7], D1_MODEL: [1.0, 0.0, 0.0]},
        "MMLU": {JEV_MODEL: [0.3, 0.3, 0.4], D1_MODEL: [0.9, 0.05, 0.05]},
    }
    chart = positions_chart("Share of the predictions at each position.", panels)
    assert chart.startswith("<svg") and "<title>Share of the predictions at each position.</title>" in chart
    assert chart.count("<path") == 12
    assert all(f">{text}</text>" in chart for text in ("70%", "40%", "90%", "MetaTool", "MMLU", "Liquid d1"))
    # Each row has its scale from 0% to 100%, and the highest bar of Liquid d1 on MetaTool is labelled 100% too.
    assert chart.count(">0%</text>") == 2 and chart.count(">100%</text>") == 3
    assert "<title>Jev, position 3: 70%</title>" in chart
    assert chart.count(f'fill="{MODEL_COLORS[JEV_MODEL]}"') == 6 + 1


def test_a_chart_of_bars_has_a_bar_per_run_and_model_with_its_text() -> None:
    groups = {
        "Random tools": {JEV_MODEL: (0.78, "0.78"), D1_MODEL: (0.74, "0.74, refused 58%")},
        "Random choices": {JEV_MODEL: (0.55, "0.55")},
    }
    chart = bars_chart("Mean confidence.", groups)
    assert chart.count("<path") == 3
    assert all(f">{text}</text>" in chart for text in ("Random tools", "Random choices", "0.74, refused 58%"))
    assert "<title>Random tools, Liquid d1: 0.74, refused 58%</title>" in chart


def test_a_chart_of_spans_has_a_hollow_and_a_filled_marker_per_run_and_model_with_both_values() -> None:
    groups = {"HotpotQA": {JEV_MODEL: (0.17, 0.77), D1_MODEL: (0.19, 0.74)}}
    marks = ("lowest correct option", "highest correct option")
    chart = spans_chart("Lowest and highest correct option.", groups, marks)
    assert chart.count("<circle") == 4 and chart.count('fill="#ffffff"') == 2
    assert all(f">{text}</text>" in chart for text in ("0.17", "0.77", "0.19", "0.74", "HotpotQA"))
    assert "hollow marker: lowest correct option; filled marker: highest correct option" in chart
