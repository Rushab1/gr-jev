"""Check the Claude bridge with one small call per model. Every run makes new calls."""

from grjev.constants import CLAUDE_CACHE_DIR, CLAUDE_MODELS
from grjev.frontier import ask_claude, request_bytes
from grjev.store import next_run

SYSTEM = "You select tools. Reply with the tool name only."
PROMPT = """Query: What will the weather be in Paris tomorrow?
Tools:
1. get_weather
2. search_flights
3. send_email
4. convert_currency
Answer with the name of the one tool to use and nothing else."""


def main() -> None:
    """Ask each model the same tool-selection question and print its answer, token counts and seconds."""
    for model in CLAUDE_MODELS:
        # A run number that is not saved yet, so the answer comes from the CLI and not from a saved file.
        run = next_run(CLAUDE_CACHE_DIR / model, request_bytes(model, SYSTEM, PROMPT))
        print(model, ask_claude(model, SYSTEM, PROMPT, run).model_dump())


if __name__ == "__main__":
    main()
