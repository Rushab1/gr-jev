"""The charts of a report, drawn as SVG: one colour per model, the same in every chart.

Every chart has the same width. The charts with rows share one scale from 0 to 1 at the same place, so a value is
at the same distance from the left in each of them.
"""

import html
from collections.abc import Sequence

from grjev.constants import MODEL_COLORS, MODEL_TITLES

INK, MUTED, GRID, PAGE = "#37352f", "#787774", "#e3e2de", "#ffffff"
FONT = "-apple-system, Helvetica Neue, Arial, sans-serif"
WIDTH = 340
# Where 0 and 1 of the scale of a chart with rows are drawn. The text of a value follows its mark.
SCALE_START, SCALE_END = 24.0, 274.0
TICKS = (0.0, 0.25, 0.5, 0.75, 1.0)
LEGEND_HEIGHT = 22
BAR, BAR_GAP, GROUP_GAP = 8, 2, 9
ROW, CORNER, MARKER = 13, 3, 3.5
NAME_HEIGHT = 13
# The chart by position: the width kept for the scale, and the height of a bar of 100%.
POSITION_SCALE, POSITION_BARS = 30, 38

# The name of a row of a chart -> the model -> its value.
type Values[T] = dict[str, dict[str, T]]


def label(x: float, y: float, content: str, anchor: str = "start", fill: str = INK, size: float = 9) -> str:
    """Return a line of text. Text is in an ink colour, never in the colour of a model."""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{size}" fill="{fill}">'
        f"{html.escape(content)}</text>"
    )


def legend(models: Sequence[str], marks: Sequence[str] = ()) -> tuple[str, float]:
    """Return the legend of a chart and its height: a swatch and the name of each model, then what the marks mean."""
    parts, x = [], SCALE_START
    for model in models:
        parts.append(f'<rect x="{x:.1f}" y="3" width="9" height="9" rx="2" fill="{MODEL_COLORS[model]}"/>')
        parts.append(label(x + 13, 11, MODEL_TITLES[model]))
        x += 24 + 4.9 * len(MODEL_TITLES[model])
    parts += [label(SCALE_START, 25, "; ".join(marks), fill=MUTED, size=8.5)] if marks else []
    return "".join(parts), LEGEND_HEIGHT + (13 if marks else 0)


def svg(height: float, about: str, body: str) -> str:
    """Return a chart that scales to the width of its place, with a description for a reader who cannot see it."""
    return (
        f'<svg viewBox="0 0 {WIDTH} {height:.0f}" width="100%" role="img" font-family="{FONT}">'
        f"<title>{html.escape(about)}</title>{body}</svg>"
    )


def across(value: float) -> float:
    """Return where a value from 0 to 1 is drawn on the scale of a chart with rows."""
    return SCALE_START + (SCALE_END - SCALE_START) * value


def scale(top: float, bottom: float) -> str:
    """Return the scale of a chart with rows: a line at each tick from top to bottom, and its value under it."""
    parts = []
    for tick in TICKS:
        x = across(tick)
        colour = MUTED if tick == 0 else GRID
        parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top:.1f}" y2="{bottom:.1f}" stroke="{colour}"/>')
        parts.append(label(x, bottom + 11, f"{tick:.2f}", "middle", MUTED, 8))
    return "".join(parts)


def rounded_bar(start: float, end: float, y: float, colour: str, hover: str) -> str:
    """Return a bar from the baseline at start to end, with round corners at its end only."""
    corner = min(CORNER, max(end - start, 0.01))
    tip = end - corner
    path = (
        f"M{start:.1f},{y:.1f} H{tip:.1f} Q{end:.1f},{y:.1f} {end:.1f},{y + corner:.1f} V{y + BAR - corner:.1f} "
        f"Q{end:.1f},{y + BAR:.1f} {tip:.1f},{y + BAR:.1f} H{start:.1f} Z"
    )
    return f'<path d="{path}" fill="{colour}"><title>{html.escape(hover)}</title></path>'


def bars_chart(about: str, groups: Values[tuple[float, str]]) -> str:
    """Return a chart with one group of bars per run and one bar per model, from 0 to 1, with its text at its end.

    A value from 0 to 1 is given with the text that is written after its bar.
    """
    models = list(next(iter(groups.values())))
    body, top = legend(models)
    rows, y = "", top + 2.0
    for name, values in groups.items():
        rows += label(SCALE_START + 3, y + NAME_HEIGHT - 4, name, fill=INK)
        y += NAME_HEIGHT
        for model, (value, text) in values.items():
            rows += rounded_bar(
                across(0), across(value), y, MODEL_COLORS[model], f"{name}, {MODEL_TITLES[model]}: {text}"
            )
            rows += label(across(value) + 4, y + BAR - 1, text, size=8)
            y += BAR + BAR_GAP
        y += GROUP_GAP - BAR_GAP
    return svg(y + 14, about, body + scale(top, y - 4) + rows)


def spans_chart(about: str, groups: Values[tuple[float, float]], marks: tuple[str, str]) -> str:
    """Return a chart with one row per run and model: a line from a first value to a second one, from 0 to 1.

    The first value has a hollow marker and the second a filled one. `marks` names the two.
    """
    models = list(next(iter(groups.values())))
    body, top = legend(models, [f"hollow marker: {marks[0]}", f"filled marker: {marks[1]}"])
    rows, y = "", top + 2.0
    for name, values in groups.items():
        rows += label(SCALE_START + 3, y + NAME_HEIGHT - 4, name)
        y += NAME_HEIGHT + 4
        for model, (first, second) in values.items():
            colour, start, end = MODEL_COLORS[model], across(first), across(second)
            hover = f"<title>{html.escape(name)}, {MODEL_TITLES[model]}: {first:.2f} and {second:.2f}</title>"
            rows += (
                f'<line x1="{start:.1f}" x2="{end:.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{colour}" stroke-width="2"/>'
            )
            rows += (
                f'<circle cx="{start:.1f}" cy="{y:.1f}" r="{MARKER}" fill="{PAGE}" stroke="{colour}" '
                f'stroke-width="2">{hover}</circle>'
            )
            rows += f'<circle cx="{end:.1f}" cy="{y:.1f}" r="{MARKER + 1}" fill="{colour}">{hover}</circle>'
            lower, upper = sorted([(start, first), (end, second)])
            rows += label(lower[0] - 7, y + 3, f"{lower[1]:.2f}", "end", size=8)
            rows += label(upper[0] + 8, y + 3, f"{upper[1]:.2f}", size=8)
            y += ROW
        y += GROUP_GAP - 4
    return svg(y + 12, about, body + scale(top, y - 6) + rows)


def position_bars(model: str, shares: list[float], left: float, base: float, width: float, numbered: bool) -> str:
    """Return the bars of one model in one run: its share of the predictions at each position, from 0% to 100%."""
    step = width / len(shares)
    even = base - POSITION_BARS / len(shares)
    full = base - POSITION_BARS
    parts = [
        f'<line x1="{left:.1f}" x2="{left + width - 3:.1f}" y1="{height:.1f}" y2="{height:.1f}" stroke="{GRID}"/>'
        for height in (base, full)
    ]
    highest = max(range(len(shares)), key=lambda place: shares[place])
    for place, value in enumerate(shares):
        x, top = left + place * step, base - POSITION_BARS * value
        corner = min(CORNER, max(base - top, 0.01))
        end = x + step - 3
        path = (
            f"M{x:.1f},{base:.1f} V{top + corner:.1f} Q{x:.1f},{top:.1f} {x + corner:.1f},{top:.1f} "
            f"H{end - corner:.1f} Q{end:.1f},{top:.1f} {end:.1f},{top + corner:.1f} V{base:.1f} Z"
        )
        hover = f"<title>{MODEL_TITLES[model]}, position {place + 1}: {value:.0%}</title>"
        parts.append(f'<path d="{path}" fill="{MODEL_COLORS[model]}">{hover}</path>')
        if place == highest:
            parts.append(label(x + (step - 3) / 2, top - 3, f"{value:.0%}", "middle", size=8))
        if numbered:
            parts.append(label(x + (step - 3) / 2, base + 10, str(place + 1), "middle", MUTED, 8))
    parts.append(
        f'<line x1="{left:.1f}" x2="{left + width - 3:.1f}" y1="{even:.1f}" y2="{even:.1f}" stroke="{INK}" '
        'stroke-dasharray="3 3" stroke-width="0.7"/>'
    )
    return "".join(parts)


def positions_chart(about: str, panels: Values[list[float]]) -> str:
    """Return the chart of the share of the predictions at each position: a row per model and a column per run.

    A bar is the share of the predictions of a model at one position. Every row has the same scale from 0% to 100%.
    The dashed line is the share of a position when every position gets the same number of predictions. The
    highest bar of a model in a run is labelled.
    """
    models = list(next(iter(panels.values())))
    width = (WIDTH - POSITION_SCALE) / len(panels)
    row = NAME_HEIGHT + POSITION_BARS + 22
    body = "".join(label(POSITION_SCALE + column * width, 10, name, size=9.5) for column, name in enumerate(panels))
    for number, model in enumerate(models):
        top = 16 + number * row
        base = top + NAME_HEIGHT + 10 + POSITION_BARS
        body += f'<rect x="0" y="{top + 1:.1f}" width="9" height="9" rx="2" fill="{MODEL_COLORS[model]}"/>'
        body += label(13, top + 9, MODEL_TITLES[model])
        body += label(POSITION_SCALE - 5, base + 3, "0%", "end", MUTED, 8)
        body += label(POSITION_SCALE - 5, base - POSITION_BARS + 3, "100%", "end", MUTED, 8)
        for column, shares in enumerate(panels.values()):
            if model in shares:
                left = POSITION_SCALE + column * width
                body += position_bars(model, shares[model], left, base, width - 8, number == len(models) - 1)
    return svg(16 + len(models) * row, about, body)
