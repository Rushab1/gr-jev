"""The charts of a report, drawn as SVG: one colour per model, the same in every chart."""

import html
from collections.abc import Sequence

from grjev.constants import MODEL_COLORS, MODEL_TITLES

INK, MUTED, GRID, PAGE = "#37352f", "#787774", "#e3e2de", "#ffffff"
FONT = "-apple-system, Helvetica Neue, Arial, sans-serif"
WIDE, HALF = 1040, 510
# A chart with rows keeps this width for the names of its rows, and this one after the plot for a value.
NAMES_WIDTH, VALUE_WIDTH = 200, 66
LEGEND_HEIGHT = 30
BAR, BAR_GAP, GROUP_GAP = 9, 2, 13
ROW, CORNER, MARKER = 15, 3, 4
# The height of a bar of 100% in the chart by position.
POSITION_BARS = 44

# The name of a row of a chart -> the model -> its value.
type Values[T] = dict[str, dict[str, T]]


def label(x: float, y: float, content: str, anchor: str = "start", fill: str = INK, size: int = 10) -> str:
    """Return a line of text. Text is in an ink colour, never in the colour of a model."""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{size}" fill="{fill}">'
        f"{html.escape(content)}</text>"
    )


def legend(models: Sequence[str], marks: Sequence[str] = ()) -> tuple[str, float]:
    """Return the legend of a chart and its height: a swatch and the name of each model, then what the marks mean."""
    parts, x = [], 0.0
    for model in models:
        parts.append(f'<rect x="{x:.1f}" y="6" width="10" height="10" rx="2" fill="{MODEL_COLORS[model]}"/>')
        parts.append(label(x + 15, 15, MODEL_TITLES[model]))
        x += 28 + 5.6 * len(MODEL_TITLES[model])
    parts += [label(0, 31, "; ".join(marks), fill=MUTED)] if marks else []
    return "".join(parts), LEGEND_HEIGHT + (14 if marks else 0)


def svg(width: int, height: float, about: str, body: str) -> str:
    """Return a chart that scales to the width of its place, with a description for a reader who cannot see it."""
    return (
        f'<svg viewBox="0 0 {width} {height:.0f}" width="100%" role="img" font-family="{FONT}">'
        f"<title>{html.escape(about)}</title>{body}</svg>"
    )


def position_bars(model: str, shares: list[float], left: float, base: float, width: float, numbered: bool) -> str:
    """Return the bars of one model in one run: its share of the predictions at each position, from 0% to 100%."""
    step = width / len(shares)
    even = base - POSITION_BARS / len(shares)
    parts = [f'<line x1="{left:.1f}" x2="{left + width - 4:.1f}" y1="{base:.1f}" y2="{base:.1f}" stroke="{GRID}"/>']
    highest = max(range(len(shares)), key=lambda place: shares[place])
    for place, value in enumerate(shares):
        x, top = left + place * step, base - POSITION_BARS * value
        reach = max(base - top, 0.01)
        corner = min(CORNER, reach)
        end = x + step - 4
        path = (
            f"M{x:.1f},{base:.1f} V{top + corner:.1f} Q{x:.1f},{top:.1f} {x + corner:.1f},{top:.1f} "
            f"H{end - corner:.1f} Q{end:.1f},{top:.1f} {end:.1f},{top + corner:.1f} V{base:.1f} Z"
        )
        hover = f"<title>{MODEL_TITLES[model]}, position {place + 1}: {value:.0%}</title>"
        parts.append(f'<path d="{path}" fill="{MODEL_COLORS[model]}">{hover}</path>')
        if place == highest:
            parts.append(label(x + (step - 4) / 2, top - 4, f"{value:.0%}", "middle", size=9))
        if numbered:
            parts.append(label(x + (step - 4) / 2, base + 12, str(place + 1), "middle", MUTED, 9))
    parts.append(
        f'<line x1="{left:.1f}" x2="{left + width - 4:.1f}" y1="{even:.1f}" y2="{even:.1f}" stroke="{INK}" '
        'stroke-dasharray="3 3" stroke-width="0.8"/>'
    )
    return "".join(parts)


def positions_chart(about: str, panels: Values[list[float]]) -> str:
    """Return the chart of the share of the predictions at each position: a row per model and a column per run.

    A bar is the share of the predictions of a model at one position, from 0% to 100%. The dashed line is the share
    of a position when every position gets the same number of predictions. The highest bar of a row is labelled.
    """
    models = list(next(iter(panels.values())))
    width = (WIDE - NAMES_WIDTH) / len(panels)
    row = POSITION_BARS + 28
    body = label(0, 12, "dashed line: every position gets the same share; numbers under the bars: position", fill=MUTED)
    for column, (name, shares) in enumerate(panels.items()):
        left = NAMES_WIDTH + column * width
        body += label(left, 34, name, size=11)
        for number, model in enumerate(models):
            base = 46 + (number + 1) * row - 14
            if model in shares:
                body += position_bars(model, shares[model], left, base, width - 26, number == len(models) - 1)
    for number, model in enumerate(models):
        middle = 46 + number * row + row / 2
        body += f'<rect x="0" y="{middle - 5:.1f}" width="10" height="10" rx="2" fill="{MODEL_COLORS[model]}"/>'
        body += label(15, middle + 4, MODEL_TITLES[model])
    return svg(WIDE, 46 + len(models) * row + 6, about, body)


def rounded_bar(start: float, end: float, y: float, colour: str, hover: str) -> str:
    """Return a bar from the baseline at start to end, with round corners at its end only."""
    side = 1 if end >= start else -1
    reach = max(abs(end - start), 0.01)
    corner = min(CORNER, reach)
    tip = end - side * corner
    path = (
        f"M{start:.1f},{y:.1f} H{tip:.1f} Q{end:.1f},{y:.1f} {end:.1f},{y + corner:.1f} V{y + BAR - corner:.1f} "
        f"Q{end:.1f},{y + BAR:.1f} {tip:.1f},{y + BAR:.1f} H{start:.1f} Z"
    )
    return f'<path d="{path}" fill="{colour}"><title>{html.escape(hover)}</title></path>'


def bars_chart(about: str, groups: Values[tuple[float, str]], low: float, high: float) -> str:
    """Return a chart with one group of bars per run and one bar per model, from 0, with its value at its end.

    A value is given with the text that is written next to its bar.
    """
    models = list(next(iter(groups.values())))
    left, right = NAMES_WIDTH, HALF - VALUE_WIDTH
    group_height = len(models) * (BAR + BAR_GAP) - BAR_GAP

    def across(value: float) -> float:
        return left + (right - left) * (value - low) / (high - low)

    body, top = legend(models)
    y = top + 4.0
    for name, values in groups.items():
        body += label(left - 10, y + group_height / 2 + 3, name, "end")
        for model, (value, text) in values.items():
            hover = f"{name}, {MODEL_TITLES[model]}: {text}"
            body += rounded_bar(across(0), across(value), y, MODEL_COLORS[model], hover)
            end = across(max(value, 0)) + 5
            body += label(end, y + BAR - 1, text, size=9)
            y += BAR + BAR_GAP
        y += GROUP_GAP - BAR_GAP
    body += f'<line x1="{across(0):.1f}" x2="{across(0):.1f}" y1="{top}" y2="{y - 6:.1f}" stroke="{MUTED}"/>'
    return svg(HALF, y, about, body)


def spans_chart(about: str, groups: Values[tuple[float, float]], marks: tuple[str, str]) -> str:
    """Return a chart with one row per run and model: a line from a first value to a second one, from 0 to 1.

    The first value has a hollow marker and the second a filled one. `marks` names the two.
    """
    models = list(next(iter(groups.values())))
    left, right = NAMES_WIDTH, HALF - 40

    def across(value: float) -> float:
        return left + (right - left) * value

    body, top = legend(models, [f"hollow marker: {marks[0]}", f"filled marker: {marks[1]}"])
    y = top + 10.0
    for name, values in groups.items():
        body += label(left - 10, y + ROW * (len(values) - 1) / 2 + 3, name, "end")
        for model, (first, second) in values.items():
            colour, start, end = MODEL_COLORS[model], across(first), across(second)
            hover = f"<title>{html.escape(name)}, {MODEL_TITLES[model]}: {first:.2f} and {second:.2f}</title>"
            body += (
                f'<line x1="{start:.1f}" x2="{end:.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{colour}" stroke-width="2"/>'
            )
            body += (
                f'<circle cx="{start:.1f}" cy="{y:.1f}" r="{MARKER}" fill="{PAGE}" stroke="{colour}" '
                f'stroke-width="2">{hover}</circle>'
            )
            body += f'<circle cx="{end:.1f}" cy="{y:.1f}" r="{MARKER + 1}" fill="{colour}">{hover}</circle>'
            lower, upper = sorted([(start, first), (end, second)])
            body += label(lower[0] - 8, y + 3, f"{lower[1]:.2f}", "end", size=9)
            body += label(upper[0] + 9, y + 3, f"{upper[1]:.2f}", size=9)
            y += ROW
        y += GROUP_GAP
    return svg(HALF, y - GROUP_GAP + 6, about, body)
