# gr-jev

Research code for a study of Jev, TypeSafe AI's decision model, as a tool and action selector. Background, prior work and datasets are in `docs/starter.md`. The plan is in `docs/plan.md`.

This file is the code standard for everyone who works here: Rushab, Gyanesh, and AI workers such as Claude Code and Codex.

## Layout

```
scripts/        runnable commands: download a dataset, run an experiment
src/grjev/      importable code: loaders, the Jev client, metrics
tests/          tests for src/grjev/
data/<dataset>/raw/        files exactly as downloaded, never edited
data/<dataset>/processed/  files built by our code
data/cache/                saved model responses, shared by all datasets
results/        experiment outputs
notebooks/      Colab notebooks, which only call scripts
docs/           project notes
```

`data/` holds data only. Scripts parse arguments and call functions in `src/grjev/`. Notebooks contain no logic.

## Setup

```
uv sync
source .venv/bin/activate
python scripts/download_data.py metatool stabletoolbench bfcl
python scripts/process_data.py metatool stabletoolbench bfcl
python scripts/dataset_stats.py metatool stabletoolbench bfcl
```

Python 3.13. `uv sync` creates `.venv` and installs the versions recorded in `uv.lock`, with the `grjev` package in editable mode. Packages are listed in `pyproject.toml`: the ones the code needs under `dependencies`, and `ruff`, `mypy` and `pytest` in the `dev` group. After changing them, run `uv lock` and commit `uv.lock`.

`scripts/download_data.py` writes each dataset to `data/<dataset>/raw/` and checks each file against its SHA-256 hash in `constants.py`. `scripts/process_data.py` converts a dataset to the common format in `data/<dataset>/processed/`. `scripts/dataset_stats.py` writes `docs/stats/<dataset>.js`, which the charts on the dashboard load. Commit that file when it changes.

Copy `.env.example` to `.env` and put the Jev key in it. `python scripts/check_jev.py` makes one call to confirm the key works.

The frontier models are Claude Sonnet 5 and Claude Opus 5, called through the `claude` CLI signed in on the machine, at the version pinned in `constants.py`, with thinking and tools switched off. `python scripts/check_frontier.py` makes one call per model.

`python scripts/run_experiment.py position --dry-run` prints the number of Jev calls of an experiment and sends nothing. Without `--dry-run` it asks Jev and writes `results/<dataset>_<experiment>/<date>_<incr>/`. The experiments are `position` and `length`, and `--examples-per-file` runs a seeded sample. A run that would take the saved Jev calls past `JEV_CALL_LIMIT` in `constants.py` does not start. Only Rushab raises that limit.

An experiment runs on any dataset in the common format. A new dataset needs a converter in `src/grjev/` and its entries in `EXPERIMENT_TEST_FILES`, `NONE_TEST_FILES`, `TWO_TOOL_TEST_FILES` and `LIST_LENGTHS` in `constants.py`.

Run `ruff check .`, `ruff format --check .`, `mypy` and `pytest` before every commit, and `pytest -m integration` after a change to the Claude bridge. The pre-commit config and the CI workflow are not added yet.

## Code style

Readability comes first. This is research code: production-like, not production-ready.

- Write small helper functions that each do one thing. As a guide, keep a function under about 40 statements and 6 arguments.
- Prefer plain functions and modules over classes. Use classes only to hold data or state.
- Write few lines. Do not add abstractions, options or error handling for cases that cannot happen.
- Format with `ruff`. Lines may be up to 120 characters, and should use that width before wrapping.
- Put type hints on every function signature. `mypy` runs in normal mode.
- Give each public function a one-line docstring. Add a comment only where the reason is not clear from the code.
- Keep every constant in `src/grjev/constants.py` with an `UPPER_CASE` name. No literal paths, model names, seeds or thresholds elsewhere.
- Use `pydantic` models for data that enters or leaves the code: experiment configs, Jev requests and responses, and rows parsed from dataset files. Use frozen dataclasses for records that stay inside the code.
- Use `pathlib` for paths and `argparse` for script arguments.
- Use `logging` in `src/grjev/`. A script may print its final summary.
- Fail loudly. No bare `except` and no silent fallbacks.
- Leave no dead or commented-out code.

## Tests

Use `pytest`. Test the code that can change a number in the paper: parsers, dataset builders, shuffling and position logic, metrics, and the response cache. Thin scripts need no tests.

A plain `pytest` run uses no network. Tests marked `integration` call the live Claude Code CLI with the machine's sign-in, and `pytest -m integration` runs them. Run them after a change to `src/grjev/frontier.py`, to its constants or to the pinned CLI version. A test of the CLI calls the CLI. It does not replace the CLI with a fake. No test calls the Jev API.

## Reproducibility

- Pin every download to a commit or revision and check it against a SHA-256 hash stored in `constants.py`.
- Never edit files in a `raw/` folder. Build everything in `processed/` with code.
- Processed data has one row per example with the same fields for every dataset: `id`, `query`, `options`, `labels`, and `raw`, the row of the raw file unchanged. When a dataset keeps the answer in a second file, `raw` holds both rows merged. A multi-turn example has one row per turn, and each row holds the whole raw row. `labels` is null when the answer is not one of the options. A converter loses no data, and a test on the downloaded files checks that every raw row and every character survives.
- Every function that makes a random choice takes a seed or a generator as an argument. Do not call `random.seed` globally.
- Save every response from Jev and from the frontier models under a hash of the exact request and a run number, and store the request and the model version with it. A rerun reads the saved files and calls nothing. A deliberate repeat of a request gets a new run number, so repeats are separate calls that can be compared. The hash covers only what is sent to the model, never the version of our code. For a Claude call it also covers the CLI version, the CLI arguments, the variables we set and the working folder. The CLI receives no other variable of our environment except the five listed in `constants.py`.
- Pin the Jev model version. The current one is `jev-1.13.0`.

## Results

Each run writes to `results/<name>/<date>_<incr>/`, for example `results/metatool_position/2026-10-04_01/`. The folder holds `config.json`, `meta.json` with the git commit and model version, and `rows.jsonl` with one row per example.

## Secrets and terms

- The Jev key is read from the environment variable `TYPESAFE_API_KEY`. Do not commit keys or `.env` files.
- Do not train any model on Jev output. TypeSafe's customer agreement prohibits it.

## Git

- Never commit to `main`. Work on a branch named `<worker>/<topic>`, such as `rushab/metatool-download`, `gyanesh/toolbench-loader`, `claude/jev-client` or `codex/metrics`.
- Merge through a pull request with CI passing.
- A branch written by an AI worker needs approval from Rushab or Gyanesh before it is merged. A person may merge their own branch once CI passes.
- AI workers do not merge pull requests and do not push to `main`.
- Write commit subjects in the imperative, such as "Add MetaTool download script". Add a body only when the reason needs explaining. Commits by an AI worker carry a `Co-Authored-By` line.
- Keep commits small. Do not commit data, results or model files.

## Writing

Documents, paper text and dashboard text are plain and neutral. State the claim and stop.

- No em dashes.
- Do not say the same thing twice.
- No sales or authority phrasing, such as "worth it", "it is important to note" or "anyone who wants X will want to know Y".
- No hype and no evaluative adjectives.
- Say plainly when a figure has not been verified.

Every sentence states a claim about a named thing that can be checked against a source. Leave out these five patterns:

- Filler reason: a clause after "because", "so", "since" or "which means" that adds no fact. Bad: "The same test requests exist in three places, because two other groups repackaged the original." End the sentence at the claim. If the reason is a fact, give it its own sentence with names and numbers.
- Unnamed thing: a noun that stands in for a name. Bad: "two other groups", "the original", "another dataset", "the authors". Write "StableToolBench (Guo et al., 2024)", "ToolBench", "the MetaTool authors".
- Amount or comparison without a number and a unit. Bad: "larger", "most", "usually", "several", "a different style". Write "16,464 APIs" or "199 tools", and say what is counted.
- Word the field does not use. Bad: "repackaged", "request", "right tool", "wrong tool", "search format". Use the terms in the papers: query, tool list, correct tool, label, distractor, tool retrieval. One row of a dataset is an example, not an item. A name from our code is not a term for readers: describe the task as a query and a list of tools with a correct tool, never as "options" and a "correct option".
- Shortened label: a tag, caption or table header that drops the subject or the verb. Bad: "Always position 1: 10%", which reads as "the correct tool is always at position 1". Write the claim in full: "Answering position 1 every time scores 10%".

When a count is spread unevenly over tools, files or queries, list the extremes: the items with the highest counts, the lowest count and the number of items that have it, and the cause when the files or the code show one. Example: FinanceTool is in 1,168 of the 4,287 MetaTool tool lists, and 3 tools are in 5.

## Interface text

This covers `docs/dashboard.html` and any other page with an interface. The page content explains the subject. Leave out text that describes the page:

- Lead-in: a line that announces the block under it. "One example from each test file." "The table below lists the files."
- Reading instruction: text that says how to read or use something. "Each bar counts the examples at that position." "Click a tab to switch." An axis label or legend that repeats the paragraph above the chart.
- Echo caption: a caption that repeats what the block shows. "The query needs two tools." under a list with two tools marked. "995 examples" under a bar labelled 995.
- Label or heading on a part that explains itself. "Query" over a query, "Tools" over a tool list, "Overview" over the opening paragraphs, "Decided" inside a Decisions tab.
- Description of a control: a subtitle, helper text, tooltip or option description on a tab, button or menu. A control has a label of one or two words.
- Note about the page. "Some descriptions are shortened." "This page shows the datasets we use." Show it in the content instead, such as an ellipsis on a shortened quote.

Keep text that states a fact the block cannot show: a tool that is absent from a list, the source and date of a number, the label on a commit hash.

`docs/dashboard.html` records Rushab's understanding of the datasets and the decisions. Each dataset tab opens with a plain explanation of the dataset, followed by sections named by topic, with two examples from each test file. It is light mode only. Check every number and quote on it against the raw files.

## Effort

Do not spend 90% of the time on 5% of the detail. If a detail seems to need that much work, confirm with Rushab first, in one short question.
