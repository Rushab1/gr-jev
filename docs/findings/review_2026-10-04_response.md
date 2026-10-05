# Response to the code review of 2026-10-04

Written by Claude Code on 2026-10-04, in the session that wrote the reviewed code. Each finding of `review_2026-10-04.md` was checked against the working tree. No code and no document was changed for a finding.

| # | Finding | Verdict |
|---|---|---|
| 1 | `read_jsonl` cannot read a row that holds U+2028, U+2029 or U+0085 | Accepted. Rushab's decision of no fix stands. |
| 2 | `jev.ask` saves a response before it validates it | Accepted |
| 3 | The two check scripts call the model only on their first run | Accepted. The fix needs a decision. |
| 4 | No document records that Claude runs with `--effort low` | Accepted |
| 5 | MetaTool has no rule for an answer of no tool or of two tools | Accepted. The decision recorded in the review has been replaced. |

All five findings are correct. None is defended.

## 1. `read_jsonl` and the three characters

Checked:

- An `Example` with each of the three characters in its query was written with `write_jsonl` and read with `read_jsonl`. All three reads raised a `ValidationError`.
- The 33 processed `.jsonl` files hold none of the three characters.
- The raw `.json`, `.jsonl`, `.csv` and `.txt` files of MetaTool, StableToolBench and BFCL hold none of them.

The failure is loud. A row cut at one of these characters leaves two pieces that are not valid JSON, and `read_jsonl` raises. It cannot return a wrong row.

`bfcl.read_rows` reads BFCL's raw files with `split("\n")` and is not affected.

Text taken from web pages can hold these characters. The case can arise when Mind2Web or AndroidControl is added.

Fix if the decision changes: `read_jsonl` splits on `"\n"` and skips the empty last piece. One line.

## 2. `jev.ask` saves before it validates

Checked by reading the code:

- `ask` passes `load_or_compute` a function that returns the record with the body from `post`.
- `load_or_compute` writes that record to the file.
- `ask` calls `JevResponse.model_validate` after `load_or_compute` returns.
- `ask_claude` calls `parse_response` inside the function it passes, so a CLI output that does not parse is never saved.

A saved body of the wrong shape blocks its request. Every rerun reads the file and raises, and the API is not called again until the file is deleted.

Fix, not applied: validate the body inside the function passed to `load_or_compute`, as `ask_claude` does.

Test, not written: replace `post` with a function that returns a body of the wrong shape, and check that `ask` raises and that no file is saved. `AGENTS.md` forbids a fake only for the Claude CLI, and this test calls no API.

## 3. The check scripts read saved responses

Checked by reading the code:

- Both scripts call with the default run number 1, and `load_or_compute` reads the saved file when it exists.
- `api_key()` is called only inside `post`. A run that reads the saved file never looks at the key.
- The scripts' docstrings state the behaviour: "The first run makes one API call; later runs read the saved file." and "Later runs read the saved responses."
- `AGENTS.md` says `check_jev.py` "makes one call to confirm the key works" and `check_frontier.py` "makes one call per model".

The saved read was chosen when the limit of 100 Jev calls was set. It leaves both scripts unable to check anything after their first run.

Fix, not applied. Two options:

| Option | Effect | Cost |
|---|---|---|
| The review's proposal: every run makes a new call, saved under the next unused run number | The scripts check the key, the sign-in and the CLI version on every run | 1 Jev call per run of `check_jev.py`, counted against the limit of 100 calls (1 used). 2 Claude calls per run of `check_frontier.py`. |
| Keep the scripts and change `AGENTS.md` | The text matches the behaviour. The scripts still check nothing after the first run. | None |

I recommend the review's proposal. The decision is Rushab's.

## 4. `--effort low` is not documented

Checked:

- `CLAUDE_ARGS` in `src/grjev/constants.py` holds `"--effort", "low"`.
- A search for "effort" in `AGENTS.md`, `docs/starter.md`, `docs/plan.md` and `docs/dashboard.html` finds only the heading "Effort" of `AGENTS.md`, which is about working time.
- The message of commit `003cd06` names thinking and tools and not the effort setting.

The CLI arguments are part of the hashed request. Every saved Claude response is tied to the setting.

Fix, not applied: name the setting in `AGENTS.md`, `docs/starter.md` and the dashboard, as Rushab decided. `docs/plan.md` was created after the review and holds the same sentence about the frontier LLMs in its co-pilot section, so it is a fourth place.

## 5. No rule for an answer of no tool or of two tools

The finding was correct when written: the Metrics table had one row for the four tool-selection files, and a Jev `choice` question returns one tool.

The decision recorded in the review, "every list gets a None option", was replaced by Rushab on 2026-10-04. The rule is in `docs/plan.md`, section 'The "None" answer':

- "None" is offered on MetaTool's similar-tools, scenario and reliability files and on BFCL.
- "None" is not offered on MetaTool's multi-tool file or on StableToolBench.

The Metrics table on the dashboard now has one row each for reliability and multi-tool.

Where "None" sits and how Jev returns two tools are items 1 and 2 of `open_items.md`. The response to them is in `open_items_response.md`.
