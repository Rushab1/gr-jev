"""Tests for grjev.example_tables on examples written by hand."""

from grjev.example_tables import Shown, block, choice_row, escaped, shortened

SHOWN = Shown(
    title="ChaosNLI SNLI, the votes of 100 annotators",
    query="Premise: a & b",
    choices=["entailment", "neutral"],
    labels=["neutral"],
    shares={"entailment": 0.48, "neutral": 0.46},
    probabilities={"jev-1.13.0": {"entailment": 0.85}, "liquid/d1": {}, "openai/gpt-6-luna-decisions": {}},
)


def test_the_characters_that_latex_reads_as_commands_are_written_out() -> None:
    assert escaped("a & b_c 100%") == "a " + r"\& b\_\allowbreak c 100\%"


def test_runs_of_spaces_become_one_space() -> None:
    assert escaped("a \n b") == "a b"


def test_a_long_text_is_cut_at_a_space_and_followed_by_an_ellipsis() -> None:
    assert shortened("one two three", 20) == "one two three"
    assert shortened("one two three", 8) == r"one two\ldots"


def test_a_correct_choice_is_marked_and_a_choice_with_no_probability_is_zero() -> None:
    assert choice_row(SHOWN, "neutral").startswith(r"neutral$^\star$ & 0.46 & 0.00 &")
    assert choice_row(SHOWN, "entailment").startswith("entailment & 0.48 & 0.85 &")


def test_a_block_gives_the_name_the_query_the_column_names_and_one_row_per_choice() -> None:
    lines = block(SHOWN)
    assert rf"\textbf{{{SHOWN.title}}}" in lines[1]
    assert r"Premise: a \& b" in lines[2]
    assert lines[5].startswith("Choice & Annotators & Jev")
    assert len(lines) == 10 + len(SHOWN.choices)
