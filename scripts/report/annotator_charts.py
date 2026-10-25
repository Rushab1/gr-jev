"""Draw the two ChaosNLI charts of the probabilities against the shares of the 100 annotators.

The runs are ANNOTATOR_RUNS in constants.py, and the code is in src/grjev/annotator_charts.py.
"""

import argparse
from pathlib import Path

from grjev.annotator_charts import gap_chart, reliability_chart
from grjev.annotators import all_answers


def main() -> None:
    """Draw the charts asked for by --gap and --reliability."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gap", type=Path, help="draw the chart of the model's gap against the annotators' gap")
    parser.add_argument("--reliability", type=Path, help="draw the chart of the probabilities against the shares")
    parser.add_argument("--paper", action="store_true", help="use the size and the font of the paper")
    arguments = parser.parse_args()
    answers = all_answers()
    for path, draw in ((arguments.gap, gap_chart), (arguments.reliability, reliability_chart)):
        if path:
            draw(answers, path, arguments.paper)
            print(f"wrote {path}")


if __name__ == "__main__":
    main()
