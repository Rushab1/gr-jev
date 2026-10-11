"""The figure of the paper: the correct options of a list on the scale of the probability, as a TikZ picture.

Each run gives one row per model. The row has the mean probability of the lowest and of the highest correct option
and of the highest distractor. Under it, an arrow goes from the mean probability of the second correct option in the
full list to its mean probability in the list without the highest correct option. A line marks the threshold of
TypeSafe's example code.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from grjev.constants import MODEL_COLORS, MODEL_TITLES, SECOND_TEAM_PROBABILITY
from grjev.distribution import second_after_removal
from grjev.report import figures_of, latex
from grjev.tables import FigureSpec, Selected

# Centimetres of the picture: the length of the scale from 0 to 1, the height of a row and of the name of a run,
# and the distance of the arrow under the line of its row.
SCALE, ROW, HEADING, ARROW = 8.6, 0.44, 0.5, 0.15
SCALE_TICKS = (0.0, 0.25, 0.5, 0.75, 1.0)
LEGEND = (
    r"\draw[black, line width=0.9pt, fill=white] (0,0) circle[radius=1.7pt]; "
    r"\node[anchor=west] at (0.1,0) {lowest correct option};",
    r"\fill[black] (0,0) circle[radius=2pt]; \node[anchor=west] at (0.1,0) {highest correct option};",
    r"\draw[black, line width=0.9pt] (0,-0.09) -- (0,0.09); \node[anchor=west] at (0.1,0) {highest distractor};",
    r"\draw[black!55, densely dashed, -{Stealth[length=4pt]}] (-0.25,0) -- (0.05,0); "
    r"\node[anchor=west] at (0.1,0) {second correct option, before and after the highest one is removed};",
)


@dataclass(frozen=True)
class Marks:
    """The mean probabilities that one row of the figure draws, for one model on one run."""

    lowest: float
    highest: float
    distractor: float
    before: float
    after: float


def marks_of(lists: dict[str, Selected], removal: dict[str, Selected]) -> dict[str, Marks]:
    """Return the marks of each model from the run with the full lists and the run with the removal."""
    found = {}
    for model, figures in figures_of(lists).items():
        moved = second_after_removal(removal[model].rows)
        lowest, highest, distractor = figures.lowest_correct, figures.highest_correct, figures.highest_distractor
        if moved is None or lowest is None or highest is None or distractor is None:
            raise ValueError(f"{model} has no correct option, no distractor or no removal in a run of the figure")
        found[model] = Marks(lowest, highest, distractor, moved.before, moved.after)
    return found


def row_tikz(model: str, marks: Marks, height: float) -> list[str]:
    """Return the TikZ commands of the row of one model at a height in centimetres."""
    color, low = f"model{list(MODEL_COLORS).index(model)}", height - ARROW
    at = [
        f"{value * SCALE:.3f}" for value in (marks.lowest, marks.highest, marks.distractor, marks.before, marks.after)
    ]
    return [
        rf"\node[anchor=east] at (-0.15,{height:.2f}) {{{latex(MODEL_TITLES[model])}}};",
        rf"\draw[{color}, line width=1pt] ({at[0]},{height:.2f}) -- ({at[1]},{height:.2f});",
        rf"\draw[black, line width=0.9pt] ({at[2]},{height - 0.09:.2f}) -- ({at[2]},{height + 0.09:.2f});",
        rf"\draw[{color}, line width=0.9pt, fill=white] ({at[0]},{height:.2f}) circle[radius=1.7pt];",
        rf"\fill[{color}] ({at[1]},{height:.2f}) circle[radius=2pt];",
        rf"\draw[black!55, densely dashed, -{{Stealth[length=4pt]}}] ({at[3]},{low:.2f}) -- ({at[4]},{low:.2f});",
    ]


def figure_tikz(groups: Sequence[tuple[str, dict[str, Marks]]]) -> str:
    """Return the TikZ picture of the figure: one group of rows per run, a scale from 0 to 1 and a legend."""
    colors = [
        rf"\definecolor{{model{place}}}{{HTML}}{{{code[1:].upper()}}}"
        for place, code in enumerate(MODEL_COLORS.values())
    ]
    lines, height = [*colors, r"\begin{tikzpicture}[font=\footnotesize]"], 0.0
    for name, models in groups:
        height -= HEADING
        lines.append(rf"\node[anchor=east, font=\footnotesize\bfseries] at (-0.15,{height:.2f}) {{{latex(name)}}};")
        for model, marks in models.items():
            height -= ROW
            lines += row_tikz(model, marks, height)
    floor, edge = height - ROW, SECOND_TEAM_PROBABILITY * SCALE
    lines.append(rf"\draw[black!40] (0,{floor:.2f}) -- ({SCALE},{floor:.2f});")
    for tick in SCALE_TICKS:
        lines.append(rf"\draw[black!40] ({tick * SCALE:.3f},{floor:.2f}) -- ++(0,-0.08) node[below] {{{tick:.2f}}};")
    lines.append(
        rf"\draw[black, dashed] ({edge:.3f},{floor:.2f}) -- ({edge:.3f},0.05) "
        rf"node[above] {{threshold {SECOND_TEAM_PROBABILITY}}};"
    )
    for place, entry in enumerate(LEGEND):
        lines.append(rf"\begin{{scope}}[shift={{(0.1,{floor - 0.75 - 0.36 * place:.2f})}}] {entry} \end{{scope}}")
    return "\n".join([*lines, r"\end{tikzpicture}"]) + "\n"


def figure(spec: FigureSpec, runs: dict[str, dict[str, Selected]]) -> str:
    """Return the TikZ picture of the figure of a definition from the runs that it names."""
    return figure_tikz([(row.name, marks_of(runs[row.run], runs[row.removal])) for row in spec.rows])
