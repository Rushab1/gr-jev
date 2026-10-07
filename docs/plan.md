# Jev study: plan

Last updated 2026-10-07. Two sets of runs have been made on Jev: runs on subsets of MetaTool, 749 calls, and runs on subsets of StableToolBench, 911 calls. The MetaTool runs are a subset of the position and length experiments with 350 calls, a second run of the position subset with 250 calls, a run with rewordings of one correct tool with 49 calls, a run with copies of one correct tool with 50 calls, and a run with the correct tool removed with 50 calls. The StableToolBench runs are the wording run and a second run of it with 300 calls each, the list-length run with 59 calls, four runs with rewordings of one relevant API with 50 calls each, a run with copies of one relevant API with 50 calls, and two single requests.

This file holds the plan: the next steps, the first run, the rules for building a tool list, the measures, the later runs, and the points not decided. Background on Jev, the datasets and prior work is in `docs/starter.md`. `docs/dashboard.html` shows the same plan with the datasets. `docs/findings/` holds a code review, a list of proposals, and a response to each.

## Next steps

The runner is built: `scripts/run_experiment.py`, with `src/grjev/placement.py`, `src/grjev/runs.py` and `src/grjev/results.py`. It runs the experiments `position`, `length`, `wording`, `growth`, `reworded`, `rotated`, `copied` and `absent` on a dataset in the common format. `--examples` takes a seeded sample of an exact number of examples over all the test files, and `--run 2` sends the same requests again and saves the answers under run number 2. `python scripts/run_experiment.py position --dry-run` prints the Jev calls of a run and sends nothing.

A subset was run on 2026-10-05, on Rushab's instruction to run a small subset of every experiment before one experiment on every example. Its results are under "Subset of 2026-10-05" and on the Results tab of `docs/dashboard.html`.

The wording run on a subset of StableToolBench was made on 2026-10-06. Its design and results are under "Several correct tools: the wording run". The list-length run on StableToolBench was made the same day, and is under "List length on StableToolBench". A second run of the wording run was made the same day, and is under "A second run of the same requests". The runs with rewordings were made on 2026-10-06 and 2026-10-07, and are under "Rewordings of one relevant API".

Rushab decided on 2026-10-07 to repeat the second run and the runs with rewordings on MetaTool. They were made the same day, and are under "MetaTool: the second run and the rewordings". Runs that list one correct tool five times were made the same day on both datasets, and are under "Copies of one correct tool". A run with the correct tool removed and "None" at five places was made the same day on MetaTool, and is under "The correct tool removed". "Two results so far" brings the results of all these runs together.

1. The runs on every example wait. Rushab decided this on 2026-10-05, after the subset.
2. Rushab raises the limit of Jev calls, `JEV_CALL_LIMIT` in `src/grjev/constants.py`. It is 1,662, and 1,661 calls have been made. The position run on every example needs 4,534 more calls with both two-tool wordings and the length run 3,480 more, which takes the saved calls to 9,675. A run that would pass the limit does not start.
3. When Rushab decides to run on every example: the position run needs 4,534 more calls and the length run 3,480 more. The 4,534 are 4,087 calls with the wording "one" and 447 calls for the multi-tool examples with the wording "both". On every example the position run costs about $0.50 with both wordings, and the length run about $4.80.
4. Build the runner for open-weight decision models and repeat the first run on them.

The three open points of the code review in `docs/findings/review_2026-10-04.md` were applied on 2026-10-05, on Rushab's instruction. `jev.ask` validates a response before it is saved (finding 2). The documents name `--effort low` (finding 4). The two check scripts make a new call on every run (finding 3). Claude Code took that option, and Rushab confirmed it the same day: a health check on a model calls the model. One run of `scripts/check_jev.py` uses 1 Jev call of the limit.

## Two results so far

Rushab, 2026-10-07: the runs give two results. Jev exaggerates its probabilities, as the rewordings and the drop from its highest probability show. The place of an entry in the list affects Jev's probabilities.

Terms of this section:

- An answer is Jev's response to one query, one list and one instruction. The top entry has the highest probability of an answer, and the second entry the second-highest.
- A normal list is the list that the benchmark gives for the query: different tools under their own names and descriptions.
- A rewording is a rewritten name and description of one tool. A copy is the same tool again with the same description, under a name that differs only by extra spaces.
- The place of an entry is where it stands in the list that is sent. Rotated orders are 5 orders of the same 5 entries, each moved by one place, with each entry at each place once.
- An even split gives every entry the same probability: 0.20 with 5 entries.

Every figure is the mean of a seeded sample: 50 queries for the rewordings, the copies and the list-length run, 300 queries for the StableToolBench wording run, and 50 queries of a test file for the MetaTool position subset. No margin of error is given.

### Result 1: Jev gives most of its probability to one entry

| The list holds | StableToolBench | MetaTool |
|---|---|---|
| 5 copies of one tool: mean probability from the highest of an answer to the lowest | 0.34, 0.24, 0.18, 0.14, 0.10 | 0.32, 0.23, 0.19, 0.15, 0.11 |
| 5 rewordings of one tool: the same | 0.43, 0.24, 0.16, 0.10, 0.06 | 0.45, 0.25, 0.16, 0.09, 0.05 |
| A normal list: the highest, second-highest and third-highest probability | 0.84, 0.12, 0.03 | 0.85, 0.14, 0.01 for the two-tool queries |
| A normal list: highest probability minus second-highest | 0.55 to 0.64 over the 4 instructions | 0.70 to 0.80 over the 4 test files |
| Queries with 2 or more correct tools: the top entry is a correct tool | 276 or 277 of 294 queries | 446 of 450 answers |
| The same queries: every correct tool is found | 203 to 218 of 294 | 314 of 450 with "Choose one of them.", 378 with "Choose both." |
| The same request sent twice: the selected entry is the same | 1,158 of 1,182 answers | 1,526 of 1,550 answers |

For a query with several correct tools, the table below gives the correct tool with the highest probability and the one with the lowest. In a list of rewordings or of copies every entry is correct. `python scripts/results_figures.py <folder>` prints the three columns of probabilities for each list.

| Run | Correct entries of the list | Answers | Highest correct, mean probability | Lowest correct, mean probability | Highest minus lowest | All correct entries together | An even split over the correct entries |
|---|---|---|---|---|---|---|---|
| MetaTool multi-tool, "Choose one of them." | 2 different tools | 450 | 0.85 | 0.12 | 0.73 | 0.97 | 0.50 |
| MetaTool multi-tool, "Choose both." | 2 different tools | 450 | 0.84 | 0.13 | 0.71 | 0.97 | 0.50 |
| StableToolBench wording run, `one` | 2 different APIs | 205 | 0.81 | 0.13 | 0.67 | 0.94 | 0.50 |
| StableToolBench wording run, `all` | 2 different APIs | 205 | 0.80 | 0.14 | 0.66 | 0.94 | 0.50 |
| StableToolBench wording run, `equal` | 2 different APIs | 205 | 0.77 | 0.16 | 0.61 | 0.93 | 0.50 |
| StableToolBench wording run, `every` | 2 different APIs | 205 | 0.81 | 0.13 | 0.68 | 0.93 | 0.50 |
| StableToolBench wording run, `all` | 3 different APIs | 63 | 0.64 | 0.06 | 0.58 | 0.86 | 0.33 |
| StableToolBench wording run, `all` | 4 to 6 different APIs | 26 | 0.58 | 0.04 | 0.54 | 0.93 | 0.17 to 0.25 |
| StableToolBench, rotated orders | 5 rewordings of one API | 250 | 0.43 | 0.06 | 0.37 | 1.00 | 0.20 |
| MetaTool, rotated orders | 5 rewordings of one tool | 250 | 0.45 | 0.05 | 0.40 | 1.00 | 0.20 |
| StableToolBench, rotated orders | 5 copies of one API | 250 | 0.34 | 0.10 | 0.24 | 1.00 | 0.20 |
| MetaTool, rotated orders | 5 copies of one tool | 250 | 0.32 | 0.11 | 0.20 | 1.00 | 0.20 |

- With 2 correct tools the two hold 0.93 to 0.97 of the probability together, and the lower one has 0.12 to 0.16.
- The instruction changes the difference by at most 0.07: it is 0.68 with `every` and 0.61 with `equal`, which asks for equal probabilities.
- The difference is 0.61 to 0.73 for 2 different tools, 0.37 to 0.40 for 5 rewordings of one tool, and 0.20 to 0.24 for 5 copies of one tool.

Other runs show the same difference:

| Run | Answers | Highest correct, mean probability | Lowest correct, mean probability | Highest minus lowest |
|---|---|---|---|---|
| StableToolBench list-length run, `all`, the list of the wording run with 5 to 11 APIs | 47 | 0.78 | 0.10 | 0.69 |
| The same with 20 APIs | 47 | 0.76 | 0.11 | 0.65 |
| The same with 50 APIs | 47 | 0.75 | 0.11 | 0.64 |
| The same with 100 APIs | 47 | 0.74 | 0.12 | 0.62 |
| The same with 199 APIs | 47 | 0.70 | 0.12 | 0.58 |
| MetaTool multi-tool, released order | 50 | 0.86 | 0.11 | 0.74 |
| MetaTool multi-tool, the 2 correct tools next to each other, 5 orders | 250 | 0.85 | 0.12 | 0.73 |
| MetaTool multi-tool, the 2 correct tools apart, 3 orders | 150 | 0.85 | 0.12 | 0.73 |
| MetaTool multi-tool, second run, "Choose one of them." | 450 | 0.85 | 0.12 | 0.72 |
| MetaTool multi-tool, second run, "Choose both." | 450 | 0.84 | 0.13 | 0.71 |
| StableToolBench wording run, second run, `all`, 2 or more relevant APIs | 294 | 0.74 | 0.11 | 0.63 |

### Result 2: the place of an entry changes Jev's probabilities

| Run | StableToolBench | MetaTool |
|---|---|---|
| 5 copies: answers that select the entry at the first, second, third, fourth and fifth place, of 250 | 12, 8, 21, 47, 162 | 77, 0, 4, 67, 102 |
| 5 copies: mean probability at the five places | 0.14, 0.13, 0.19, 0.23, 0.31 | 0.22, 0.12, 0.17, 0.24, 0.26 |
| 5 copies: answers that select each of the 5 copies, of 250 | 42 to 60 | 46 to 57 |
| 5 rewordings: answers that select the entry at the five places, of 250 | 30, 44, 47, 51, 78 | 51, 46, 36, 56, 61 |
| 5 rewordings: queries whose selected entry differs between the 5 orders | 37 of 50 | 28 of 50 |
| A normal list with one correct tool: correct answers with it first and with it last, of 50 | Not run | 39 and 38 on `similar_tools`, 41 and 41 on `scenario` |
| The same request sent twice: the largest change of one probability | 0.10 | 0.10 |

- A copy is selected about as often as every other copy, and the place is not: the 5 copies of a query sit at each place once, and the count by copy is 42 to 60 where the count by place is 8 to 162. Jev does not follow the extra spaces of a name.
- In the MetaTool position subset the probability of the correct tool differs by 0.08 on average between its 5 places on `similar_tools` and by 0.05 on `scenario`. Jev's highest probability is 0.72 and 0.78 above its second-highest there, and Jev selects the same tool at all 5 places for 44 and 48 of the 50 queries. The figures script does not print the 0.08 and the 0.05.
- TypeSafe's documentation says that `jev-1.13` "leans toward the option that comes first". In the copied runs the last place is selected most often.

### How the two results fit together

Claude Code's reading, 2026-10-07: the place decides Jev's selection when the entries are close, and not when one entry is far ahead.

| The list holds | Highest probability, mean | Jev's selection follows |
|---|---|---|
| 5 copies of one tool | 0.32 to 0.34 | The place: the last place is selected in 162 and in 102 of 250 answers |
| 5 rewordings of one tool | 0.43 to 0.45 | The rewording and the place: the same rewording is selected in all 5 orders for 13 and for 22 of 50 queries |
| Different tools with one correct tool | 0.84 to 0.88 on MetaTool | The tool: 39 and 38 correct answers with the correct tool first and last |

Rushab, 2026-10-07: the normal lists show no effect of the place because their tools are not similar enough. The run under "The correct tool removed" tests this with a list of tools that are similar to the correct tool, and it finds "None" selected 34 to 37 times of 50 at each of the 5 places.

### Towards the paper

- Rushab, 2026-10-07, after two single requests with 5 copies of one API: "There is our paper." His proposal for the claim: decision models exaggerate probabilities.
- Claude Code's view of the claim: the copies show the exaggeration with a known answer, 0.34 against 0.20 for an even split, and they show that the place decides the selection. For different tools, Jev's question asks for one choice, and a high probability for one tool is a possible reading of the question. A claim that the runs support: Jev's probabilities follow how the list is written, and they do not state how relevant each tool is.
- Missing for a paper, in Claude Code's view: a second model, since no open-weight decision model has been run; a consequence for a user of Jev; and runs on every query, of which the copied run costs about $0.25 on both datasets.
- `docs/findings/review_prompt_2026-10-07.md` holds a prompt that asks a reviewer with no context to check the two results.

## Subset of 2026-10-05

350 Jev calls, 3,877,435 input tokens, $0.16. Every figure is from a seeded sample of 50 examples of a test file, or of 50 queries, and is given here without a margin of error. `python scripts/results_figures.py` prints the figures from a results folder, each CSR with a margin of error computed from the saved answers. The code is in `src/grjev/metrics.py`.

The results folders are `results/metatool_position/2026-10-05_04` and `2026-10-05_05`, and `results/metatool_length/2026-10-05_02`. They were written on 2026-10-05 from the saved responses, with 0 new Jev calls, at commit `fc0b930`, which holds the runner. The folders `2026-10-05_02` and `2026-10-05_03` of the position runs and `2026-10-05_01` of the length run hold the same rows and were written before the runner was committed. `results/metatool_position/2026-10-05_01` is a trial with 1 example per test file. Results folders are not in git.

| Run | Command | Examples | Tool lists | Jev calls |
|---|---|---|---|---|
| Position | `python scripts/run_experiment.py position --examples-per-file 50` | 200 | 1,100 | 200 |
| Position, multi-tool with the wording "both" | `python scripts/run_experiment.py position --test-files multi_tool --examples-per-file 50 --two-tool-wording both` | 50 | 450 | 50 |
| Length | `python scripts/run_experiment.py length --examples-per-file 25` | 50 | 1,500 | 100 |

Position, 50 examples per test file:

| Test file | Released order | First | 25% | 50% | 75% | Last |
|---|---|---|---|---|---|---|
| Similar tools | 76% | 78% | 74% | 78% | 76% | 76% |
| Scenario | 82% | 82% | 84% | 82% | 80% | 82% |
| Reliability | 86% | | | | | |

- No position effect is visible. CSR with the correct tool first minus CSR with it last is +2.0 points on similar tools and 0.0 points on scenario.
- Jev selects the same candidate in all 5 placements for 88% of the similar-tools examples and 96% of the scenario examples.
- "None" is selected in 27 of 300 answers on similar tools (9.0%) and in 24 of 300 on scenario (8.0%), where it is wrong, and in 43 of 50 on reliability (86%), where it is correct. The similar-tools and reliability samples hold the same 50 queries.
- Confidently wrong. Of the answers with a top probability of 0.9 or more, 14 of 176 are wrong on similar tools (8.0%), 16 of 201 on scenario (8.0%) and 2 of 34 on reliability (5.9%). They are 20%, 30% and 29% of the wrong answers of each file.

Multi-tool, the same 50 examples with two wordings of the instruction, 450 tool lists each. Both wordings begin "Two tools in the list are appropriate to solve the user's query."

| Outcome of an answer | "Choose one of them." | "Choose both." |
|---|---|---|
| Both correct tools are the top two | 314 (69.8%) | 378 (84.0%) |
| Only top tool is correct | 132 | 66 |
| Top tool is wrong | 4 | 6 |
| Total | 450 | 450 |

- The top tool is the one with Jev's highest probability. In 66 of the 132 answers with "Choose one of them." and in 12 of the 66 with "Choose both.", Jev names no second tool: several tools share the second-highest probability. In 57 of those 66, every tool but the top one has 0.00. In the other answers of the row, the second tool is a wrong tool.
- The two wordings differ in the second tool. In the released order, both correct tools are the top two in 74% of the examples with "Choose one of them." and in 86% with "Choose both."
- With the wording "both", CSR is 83.6% with the two correct tools adjacent and 84.0% with them separated.
- Rushab decided on 2026-10-05 to keep both wordings and to report the difference between them as a finding. Each multi-tool example is sent with both.

Length, 50 queries, random distractors, the 5 placements pooled:

| Tools in the list | 5 | 10 | 20 | 50 | 100 | 199 |
|---|---|---|---|---|---|---|
| CSR | 85.6% | 85.6% | 81.2% | 80.0% | 76.4% | 72.8% |

- CSR at 5 tools minus CSR at 199 tools is 12.8 points for the same queries.
- By placement, with all lengths pooled, CSR is 79.0% first, 81.0% at 25%, 80.0% at 50%, 80.7% at 75% and 80.7% last.
- "None" is selected in 12.4% of the answers at 5 tools and 10.0% at 199 tools. At 5 tools CSR is 85.6%, so the wrong answers at 5 tools are mostly "None".
- At 199 tools 98.1% of the returned probabilities are 0.00.

Measured cost. A tool list of the position run took 457 input tokens, which puts the whole position run at about $0.43. A tool list of the multi-tool run with the wording "both" took 402 input tokens, which adds about $0.08 for the 4,473 tool lists of the 497 multi-tool examples. A query of the length run took 63,876 input tokens, which puts the whole length run at about $4.80.

## Several correct tools: the wording run

Decided by Rushab on 2026-10-06. Question: is Jev biased towards a single selection when a query needs several tools? On MetaTool's multi-tool file Jev's highest probability is 0.71 above its second-highest on average with "Choose one of them." and 0.70 with "Choose both."

The run was made on 2026-10-06 on StableToolBench, where 738 of the 765 queries have 2 or more relevant APIs. An API is one function of a tool, and the relevant APIs of a query are the correct entries of its list.

- Examples. A seeded sample of 50 examples from each of the six test files, 300 examples, as in the MetaTool subset. 6 of the 300 queries have 1 relevant API, 205 have 2, 63 have 3, 18 have 4, 6 have 5 and 2 have 6.
- Tool list. The released list of the example. A list under 5 APIs gets random other APIs of the 2,490 added until it has 5, and every list is put in a seeded random order. 141 of the 300 lists are padded, with 299 APIs added. No "None" candidate is offered. An API with a blank description is sent without a description: 149 of the 1,952 candidates.
- Position. The relevant APIs are not placed at fixed positions. Rushab, 2026-10-05: the MetaTool subset showed no position effect.
- Wordings. Four instructions go to Jev as four questions of one request per example. The first three state the number of relevant APIs and go to the 294 queries with 2 or more. The fourth states no number and goes to all 300.

| Name | Instruction |
|---|---|
| `one` | "Three tools in the list are appropriate to solve the user's query. Choose one of them." |
| `all` | "Three tools in the list are appropriate to solve the user's query. Choose all of them." |
| `equal` | "Three tools in the list are appropriate to solve the user's query. Choose all of them with equal probability." |
| `every` | "Choose every tool in the list that is needed to solve the user's query." |

The number word follows the query, from Two to Six. The texts say "tools", as on MetaTool.

- Score. For a query with k relevant APIs, an answer is correct when Jev's k highest probabilities are the k relevant APIs.
- Entropy. H = −Σ pᵢ log₂ pᵢ over the probabilities pᵢ of one answer, in bits. It is 0 when one API has 1.00, 1.00 when two APIs have 0.50 each, and 1.58 when three have one third each.
- Size and cost. 300 requests, 1,182 questions, 487,714 input tokens, $0.02. The results folder is `results/stabletoolbench_wording/2026-10-06_01`, written at commit `2e5e4ad`. `python scripts/results_figures.py` prints the figures of the three tables below. No margin of error is given.

All six test files:

| Wording | Queries | Correct answers | Entropy, mean | Highest probability minus second-highest, mean |
|---|---|---|---|---|
| `one` | 294 | 203 (69.0%) | 0.75 | 0.62 |
| `all` | 294 | 218 (74.1%) | 0.84 | 0.59 |
| `equal` | 294 | 212 (72.1%) | 0.94 | 0.55 |
| `every` | 300 | 215 (71.7%) | 0.74 | 0.64 |

Correct answers by number of relevant APIs:

| Relevant APIs | Queries | `one` | `all` | `equal` | `every` |
|---|---|---|---|---|---|
| 1 | 6 | not sent | not sent | not sent | 6 (100%) |
| 2 | 205 | 156 (76.1%) | 166 (81.0%) | 164 (80.0%) | 161 (78.5%) |
| 3 | 63 | 33 (52.4%) | 37 (58.7%) | 35 (55.6%) | 33 (52.4%) |
| 4 | 18 | 10 | 11 | 9 | 11 |
| 5 | 6 | 4 | 4 | 4 | 4 |
| 6 | 2 | 0 | 0 | 0 | 0 |

Mean entropy by number of relevant APIs:

| Relevant APIs | `every` | `equal` | An even split over the relevant APIs |
|---|---|---|---|
| 1 | 0.00 | not sent | 0.00 |
| 2 | 0.63 | 0.75 | 1.00 |
| 3 | 0.98 | 1.30 | 1.58 |
| 4 | 1.19 | 1.59 | 2.00 |
| 5 | 1.05 | 1.34 | 2.32 |
| 6 | 1.45 | 1.82 | 2.58 |

- With every wording Jev's highest probability is 0.55 to 0.64 above its second-highest on average. The wording `equal` asks for equal probabilities and gives a mean entropy of 0.75 for 2 relevant APIs, against 1.00 for an even split.
- `all` scores 5.1 points above `one`. On MetaTool's multi-tool file "Choose both." scores 14.2 points above "Choose one of them."
- The score falls with the number of relevant APIs: with `all` it is 81.0% for 2 and 58.7% for 3.
- The 6 queries with 1 relevant API are all correct, with an entropy of 0.00. Their released list holds 1 API, and the other 4 APIs of their list are random.
- For the 294 queries with 2 or more relevant APIs, Jev's highest probability is on a relevant API in 277 answers with `one`, 276 with `all`, 277 with `equal` and 277 with `every`. All the relevant APIs are found in 203, 218, 212 and 209 of the 294. Rushab, 2026-10-06: Jev selects one relevant API and gives the others a low probability, in queries of which 44% name an API or its tool.

Not decided: how the number of relevant APIs is read from an answer when the instruction does not state it. A first look at the saved answers of the wording `every` gave the three figures below. The figures script does not print them.

- The largest drop between two neighbouring probabilities comes right after the top API in 250 of the 300 answers. The APIs above the drop are exactly the relevant APIs in 28 of 300.
- Selecting every API with a probability of 0.03 or more gives exactly the relevant APIs in 155 of 300. The cut of 0.03 was chosen on these same answers.
- With the number of relevant APIs given to the scoring rule, the highest probabilities are the relevant APIs in 215 of 300.

### A second run of the same requests

Rushab asked on 2026-10-06 whether Jev's top API changes between two runs of one request while its highest probability stays far above its second-highest. The 300 requests of the wording run were sent a second time on 2026-10-06: 300 calls, 487,714 input tokens, $0.02. The results folder is `results/stabletoolbench_wording/2026-10-06_02`, written at commit `ac8fd1d` with `--run 2`. `python scripts/compare_runs.py results/stabletoolbench_wording/2026-10-06_01 results/stabletoolbench_wording/2026-10-06_02` prints the first four columns of figures.

| Wording | Answers | Same selected API in both runs | Answers with every probability the same | Largest change of one probability | Correct answers, first run | Correct answers, second run | Highest probability minus second-highest, mean, first run | The same, second run |
|---|---|---|---|---|---|---|---|---|
| `one` | 294 | 291 | 78 | 0.09 | 203 | 203 | 0.62 | 0.62 |
| `all` | 294 | 285 | 64 | 0.10 | 218 | 218 | 0.59 | 0.59 |
| `equal` | 294 | 289 | 53 | 0.10 | 212 | 214 | 0.55 | 0.55 |
| `every` | 300 | 293 | 65 | 0.08 | 215 | 216 | 0.64 | 0.64 |

- The selected API differs in 24 of the 1,182 answers. In each of the 24, the first run gave the API that the second run selects at most 0.10 less than the API it selected.
- In 20 of the 24 both selected APIs are relevant APIs. The figures script does not print this count.
- TypeSafe's page "TypeSafe in action" says that "TypeSafe returns stable noul probabilities" while "LLM answers vary run to run". Rushab sent a screenshot of the page on 2026-10-06.

## List length on StableToolBench

Decided by Rushab on 2026-10-06, for 50 queries: the fall of CSR with the list length is a main finding of the MetaTool subset, and it is tested on StableToolBench.

- Examples. A seeded sample of 50 queries over the six test files: 9 from each of the first two and 8 from each of the other four. 3 have 1 relevant API, 35 have 2, 8 have 3, 2 have 4, 1 has 5 and 1 has 6. 48 of the 50 are also in the wording run.
- Lists. The list that the wording run sends for the example, with 5 to 11 APIs for these 50 queries, and that list grown to 20, 50, 100 and 199 APIs with random other APIs of the 2,490. Each longer list contains the shorter ones, and each list is in a seeded random order of its own.
- Wordings. `all` for the 47 queries with 2 or more relevant APIs, and `every` for all 50.
- Size and cost. 59 requests, since 9 queries need two requests for their 10 questions. 485 questions, 1,667,337 input tokens, $0.07. The results folder is `results/stabletoolbench_growth/2026-10-06_02`, written at commit `2343b01`. The folder `2026-10-06_01` holds 48 of the 50 queries: 8 per test file were sent first, and 2 queries were added to reach the 50 that Rushab asked for. The code names the experiment `growth`. `python scripts/results_figures.py` prints the figures of the table. No margin of error is given.

| APIs in the list | Correct with `all`, 47 queries | Correct with `every`, 50 queries | Entropy with `every`, mean | Highest probability minus second-highest with `every`, mean | Probabilities at 0.00 with `every` |
|---|---|---|---|---|---|
| 5 to 11, the list of the wording run | 31 (66.0%) | 33 (66.0%) | 0.63 | 0.72 | 58.5% |
| 20 | 31 (66.0%) | 34 (68.0%) | 0.66 | 0.70 | 85.4% |
| 50 | 29 (61.7%) | 33 (66.0%) | 0.71 | 0.70 | 93.9% |
| 100 | 28 (59.6%) | 30 (60.0%) | 0.74 | 0.68 | 96.8% |
| 199 | 30 (63.8%) | 32 (64.0%) | 0.83 | 0.62 | 98.3% |

- From the list of the wording run to 199 APIs the score changes by 2.1 points with `all` and by 2.0 points with `every`. That is 1 query. On MetaTool, CSR falls from 85.6% with 5 tools to 72.8% with 199.
- The 35 queries with 2 relevant APIs score 77.1% with the list of the wording run and 77.1% with 199 APIs, with both wordings.
- The mean entropy rises with the list length, from 0.63 to 0.83 with `every`.

A first look at the saved answers gave the figures below. The figures script does not print them.

- StableToolBench, wording `every`. The added APIs get 0.05 of Jev's probability in the list of 199 APIs, and an added API is Jev's top API in 2 of the 200 answers to the four grown lists.
- MetaTool length run, 250 answers at each list length. The 9 tools closest to the correct tool, which form its similar-tools list, enter the list as it grows: a list of 5 tools holds 0.22 of them on average, a list of 20 holds 0.86, a list of 100 holds 4.56, and the list of 199 holds all 9.

| Tools in the list | Wrong answers of "None" | Wrong answers that select one of the 9 closest tools | Wrong answers that select another tool |
|---|---|---|---|
| 5 | 31 | 0 | 5 |
| 10 | 26 | 0 | 10 |
| 20 | 37 | 0 | 10 |
| 50 | 25 | 5 | 20 |
| 100 | 31 | 12 | 16 |
| 199 | 25 | 17 | 26 |

- MetaTool, lists of 50 tools. CSR is 100% for the lists with none of the 9 closest tools (15 of 15), 86% with 1 or 2 of them (125 of 145) and 67% with 3 to 5 (60 of 90).
- The 48 queries in both StableToolBench runs had 94 questions sent twice, with the same list and instruction. Jev selects the same API in 93 of the 94, and no probability differs by more than 0.06.

### How many tools are similar to a given tool

Rushab asked on 2026-10-06 how many tools or APIs are similar to a given one in each benchmark. This is a first look, and the code and the model are not in the repo. The name and description of each of the 199 MetaTool tools and of the 2,490 StableToolBench APIs were embedded with `Qwen/Qwen3-Embedding-0.6B`, revision `97b0c61`. Rushab asked for a recent and highly cited model: its paper, arXiv 2506.05176 of June 2025, has 1,549 citations on Semantic Scholar on 2026-10-06. Two entries count as similar when the cosine similarity of their embeddings reaches a bar. The first bar, 0.752, is where a MetaTool tool has 9 similar tools on average, which is the size of MetaTool's own lists of closest tools. The second bar, 0.835, is where it has 1.

| | MetaTool | StableToolBench |
|---|---|---|
| Entries | 199 tools | 2,490 APIs in 819 tools and 47 categories |
| Similar entries per entry at the first bar, mean | 9.0 of 198 (4.5%) | 29.9 of 2,489 (1.2%), of which 4.4 are APIs of the same tool |
| Similar entries per entry at the second bar, mean | 1.0 of 198 (0.5%) | 10.3 of 2,489 (0.4%), of which 4.1 are APIs of the same tool |
| Wrong entries similar to a correct one at the first bar, in the shortest list that was sent, mean | 0.14, in a list of 5 tools | 2.32, in the list of the wording run |
| The same in the list of 199, mean | 7.80 | 5.78, of which 3.46 were added by growing the list |

- A StableToolBench API has 4.6 other APIs in its own tool on average, and 96% of the pairs of APIs of one tool are similar at the first bar.
- As the list grows to 199, a MetaTool list gains 7.66 wrong tools that are similar to the correct one, and a StableToolBench list gains 3.46. The StableToolBench list has 2.32 from the start.
- The measure agrees in part with MetaTool's own lists, which come from OpenAI's `text-embedding-ada-002`: of the 9 closest tools of a tool, 3.8 are among its 9 nearest by this measure.
- The count depends on the embedding model. With `sentence-transformers/all-MiniLM-L6-v2`, the first model tried, the list of 199 held 19.8 similar wrong APIs on StableToolBench and 9.9 similar wrong tools on MetaTool.

A rule with no model call was scored on the same lists: it selects the entries whose embedding is closest to the embedding of the query, as many as the query has correct entries.

| Tools in the list | MetaTool: Jev correct, 50 queries | MetaTool: embedding rule correct | StableToolBench: Jev correct, 50 queries | StableToolBench: embedding rule correct |
|---|---|---|---|---|
| 5 on MetaTool, 5 to 11 on StableToolBench | 43 | 49 | 33 | 28 |
| 10 | 42 | 47 | not sent | not sent |
| 20 | 39 | 44 | 34 | 27 |
| 50 | 41 | 41 | 33 | 26 |
| 100 | 38 | 38 | 30 | 26 |
| 199 | 34 | 36 | 32 | 24 |

- The MetaTool columns use the lists with the correct tool first. Jev's lists on MetaTool hold a "None" candidate, and the rule cannot answer "None". The StableToolBench columns use the wording `every`.
- On MetaTool the rule scores as many queries as Jev or more at every list length, and both fall as the list grows. On StableToolBench Jev scores 5 to 8 queries more than the rule, and the rule falls from 28 to 24 of 50 while Jev stays between 30 and 34.

## Rewordings of one relevant API

Decided by Rushab on 2026-10-06. Question: when every entry of a list is equally correct, does Jev still give most of its probability to one entry? In the runs above the correct entries of a query are different APIs.

- Examples. The 50 queries of the list-length run.
- Reworded API. One relevant API of each query is chosen with the seed. The 50 queries give 45 different APIs: "Advertising / URL Link Shortener / Get a list of domains" is chosen for 4 queries, 2 APIs for 2 queries each, and 42 APIs for 1 query.
- List. The 5 rewordings of the chosen API and no other entry. Rushab, 2026-10-06: "exactly 5 options are passed to jev".
- Instruction. "Pick all the tools in the list that are relevant to the task at hand." It states no number.
- Rewordings. Each of the 45 APIs has 5 rewordings of its name and description, 225 in all, in `src/grjev/rewordings/stabletoolbench.json`. Claude Opus 5.5 wrote them in a Claude Code session on 2026-10-06, on Rushab's instruction. A rewording keeps the category and the tool of the name and rewords the API name and the description. 5 of the 45 APIs have a blank description, and so do their rewordings. Rushab found a first set of rewordings "too similar" to each other, and the file holds a second set.
- Order of the rewordings in the file. The first rewording has the shortest description of the 5 for 37 of the 40 APIs with a description, and the second starts with "Use" for 35. The mean length of a description is 61 characters for the first rewording and 90 to 106 for the other four.
- Similarity. Rushab set a bar of 0.80 for the cosine similarity between a rewording and the API it rewords, on embeddings of the name and description from `Qwen/Qwen3-Embedding-0.6B`. The lowest of the 225 is 0.932, and the mean is 0.985. With the category and the tool left out of the text, the lowest is 0.812 and the mean 0.958. The embedding code is not in the repo.

"Travel / Flight Fare Search / Flight Search V2", with the description "A faster, more agile Endpoint that's used to search flights.", has these 5 rewordings:

| Name | Description |
|---|---|
| Travel / Flight Fare Search / Find Flights (v2) | Looks up flights. Built to be quicker and more agile. |
| Travel / Flight Fare Search / Flight Lookup 2 | Quick, nimble flight search. |
| Travel / Flight Fare Search / Search Available Flights, Version 2 | Use this endpoint to search for flights when you want a faster and more agile option. |
| Travel / Flight Fare Search / V2 Flight Finder | Searches flights with greater speed and agility. |
| Travel / Flight Fare Search / Flights Query v2 | An agile, high-speed endpoint for querying flights. |

Three runs were made, each with one request per query. The code names the first two `reworded` and the third `rotated`.

| Run | Order of the 5 rewordings | Questions | Input tokens | Results folder | Commit |
|---|---|---|---|---|---|
| Written order, 2026-10-06 | The order of the file | 50 | 26,945 | `results/stabletoolbench_reworded/2026-10-06_02` | `a5d5eaa` |
| Shuffled order, 2026-10-07 | A seeded random order for each query | 50 | 26,945 | `results/stabletoolbench_reworded/2026-10-07_01` | `e0b630d` |
| Rotated orders, 2026-10-07 | The order of the file moved by 0, 1, 2, 3 and 4 places, as 5 questions of one request | 250 | 71,929 | `results/stabletoolbench_rotated/2026-10-07_01` | `42dbd0d` |

Each run cost under $0.01. `python scripts/results_figures.py <folder>` prints the figures of the two tables below, and `python scripts/compare_runs.py` compares two folders. No margin of error is given.

A first run on 2026-10-06 kept the other APIs of the query's list and put the 5 rewordings in the place of the chosen API, which gave lists of 9 to 15 entries. Rushab rejected that design the same day. Its 50 calls count towards the limit, its folder is `results/stabletoolbench_reworded/2026-10-06_01`, and its figures are not used.

| Rewording, by Jev's probability within an answer | Written order, mean of 50 answers | Shuffled order, mean of 50 answers | Rotated orders, mean of 250 answers |
|---|---|---|---|
| Highest | 0.437 | 0.444 | 0.434 |
| Second-highest | 0.235 | 0.238 | 0.241 |
| Third | 0.155 | 0.150 | 0.159 |
| Fourth | 0.105 | 0.102 | 0.102 |
| Lowest | 0.068 | 0.067 | 0.064 |
| Entropy, mean | 1.97 | 1.96 | 1.96 |
| Highest minus second-highest, mean | 0.20 | 0.21 | 0.19 |

- An even split gives each rewording 0.20 and an entropy of 2.32 bits.
- Rushab, 2026-10-07: the probability falls from the highest rewording to the lowest, and the fall is not at the second place. The highest is 0.33 above the fourth and 0.37 above the lowest in the written order.

The rotated run puts each rewording at each place of the list in one of the 5 orders of a query:

| | First | Second | Third | Fourth | Fifth |
|---|---|---|---|---|---|
| Mean probability of the entry at this place of the list | 0.179 | 0.186 | 0.188 | 0.204 | 0.241 |
| Answers that select the entry at this place, of 250 | 30 | 44 | 47 | 51 | 78 |
| Mean probability of this rewording, by its place in the file | 0.214 | 0.261 | 0.171 | 0.211 | 0.142 |
| Answers that select this rewording, of 250 | 60 | 82 | 28 | 60 | 20 |

- The entry at the last place is selected in 78 of the 250 answers and the entry at the first place in 30. TypeSafe's documentation says that `jev-1.13` "leans toward the option that comes first" (`docs.typesafe.ai/model-jaggedness/jev-1.13`, read on 2026-10-04).
- Jev selects the same rewording in all 5 orders for 13 of the 50 queries, in 4 orders for 19, in 3 for 12 and in 2 for 6.
- The written order was sent twice: in the written-order run, and as the first question of the rotated run. Jev selects the same rewording in 47 of the 50 queries, and no probability differs by more than 0.08.
- Between the written order and the shuffled order Jev selects the same rewording in 33 of the 50 queries, and the largest change of one probability is 0.58.

A first look at the saved answers gave the figures below. The figures script does not print them.

- In the list of the list-length run, with different APIs and the wording `every`, the 5 highest probabilities of the same 50 queries are 0.840, 0.117, 0.031, 0.009 and 0.003 on average.
- In the rotated run the probability of one rewording differs by more than 0.10 between its highest and its lowest place in 167 of the 250 cases of a query and a rewording, and by more than 0.20 in 71.
- For the query that names "Flight Search V2", Jev selects "Search Available Flights, Version 2" in all 5 orders, with 0.87 at the first place, 0.80 at the second, 0.47 at the third, 0.65 at the fourth and 0.75 at the fifth.

## Queries that name their APIs

Rushab, 2026-10-06, after reading one request of StableToolBench: "the tool is exctly specified in the query. not representative of the real wold at all". Its query: "I need to book a flight from London to Dubai for a business trip. Can you provide me with the flight options available on a specific date using the Flight Search V2 API? Additionally, I would like to search for airports using a specific query using the Airport Search API."

A count on the processed files, with the names and the queries in lower case and without punctuation:

| Dataset | Queries | Queries that contain the name of a relevant API or of its tool | Queries that contain neither |
|---|---|---|---|
| StableToolBench, the six test files | 765 | 336 (43.9%) | 429 |
| The 50 queries of the list-length run | 50 | 23 | 27 |
| MetaTool, the test files `similar_tools`, `scenario` and `multi_tool` | 3,292 | 170 (5.2%), the name of a correct tool | 3,122 |

- 221 of the 765 StableToolBench queries contain the name of a relevant API, 180 the name of the tool of a relevant API, and 49 the name of every relevant API.
- `G2_category` has the highest share, 72 of 124 queries, and `G1_instruction` the lowest, 56 of 163.
- The count takes exact names. "Can you provide me with the channel clips and the channel details?" is counted as naming neither "Get Channel Clips" nor "Get Channel Details".
- Rushab dropped StableToolBench on 2026-10-06 and kept it the same day: Jev gives one relevant API its highest probability and the others a low one in queries that name them.
- The code of this count is not in the repo.

## MetaTool: the second run and the rewordings

Decided by Rushab on 2026-10-07: the second run and the runs with rewordings are repeated on MetaTool.

### A second run of the position subset

The 250 requests of the position subset of 2026-10-05 were sent a second time on 2026-10-07: the 200 requests of the position run, and the 50 requests of the multi-tool examples with "Choose both." They took 683,647 input tokens, $0.03. The results folders are `results/metatool_position/2026-10-07_01` and `results/metatool_position/2026-10-07_02`, written at commit `8fceb0a` with `--run 2`. `python scripts/compare_runs.py` prints the figures of each tool list, and the table sums them over the tool lists of a test file.

| Test file | Tool lists of an example | Answers | Same selected tool in both runs | Answers with every probability the same | Largest change of one probability | Correct answers, first run | Correct answers, second run | Highest probability minus second-highest, mean, in both runs |
|---|---|---|---|---|---|---|---|---|
| `similar_tools` | 6 | 300 | 296 | 128 | 0.09 | 229 | 230 | 0.72 |
| `scenario` | 6 | 300 | 298 | 170 | 0.09 | 246 | 246 | 0.78 |
| `multi_tool`, "Choose one of them." | 9 | 450 | 438 | 155 | 0.10 | 314 | 313 | 0.71 |
| `reliability` | 1 | 50 | 49 | 31 | 0.08 | 43 | 44 | 0.80 |
| `multi_tool`, "Choose both." | 9 | 450 | 445 | 161 | 0.06 | 378 | 378 | 0.70 |

- The selected tool differs in 24 of the 1,550 answers. In each of the 24, the first run gave the tool that the second run selects at most 0.09 less than the tool it selected.
- On StableToolBench the selected API differs in 24 of 1,182 answers.

### Rewordings of one correct tool

- Examples. A seeded sample of 50 queries: 17 from `similar_tools`, 17 from `scenario` and 16 from `multi_tool`. 1 of the 50 queries contains the name of its chosen tool.
- Reworded tool. The correct tool of the query, or for a multi-tool query one of its 2 correct tools, chosen with the seed. The 50 queries give 38 different tools: ProductSearch, WeatherTool and ResearchFinder are chosen for 3 queries each, 6 tools for 2 queries each, and 29 tools for 1 query.
- List and instruction. The 5 rewordings of the chosen tool and no other entry, with "Pick all the tools in the list that are relevant to the task at hand." The "None" candidate of the MetaTool runs is not offered.
- Rewordings. Each of the 38 tools has 5 rewordings of its name and description, 190 in all, in `src/grjev/rewordings/metatool.json`. Claude Opus 5.5 wrote them in a Claude Code session on 2026-10-07. For all 38 tools the first rewording has the shortest description of the 5, the second starts with "Use" and the fourth with "Given". The mean length of a description is 46 characters for the first rewording and 116 to 129 for the other four.
- Similarity. The lowest cosine similarity between a rewording and its tool is 0.907 and the mean 0.979, on `Qwen/Qwen3-Embedding-0.6B` embeddings of the name and description. Rushab's bar is 0.80.
- Run. The rotated orders, as on StableToolBench: 50 queries with 5 questions each, 64,578 input tokens, under $0.01. `metatool/scenario/210` and `metatool/scenario/1230` are the same query with the same tool and give the same request, which leaves 49 requests. The results folder is `results/metatool_rotated/2026-10-07_01`, written at commit `93f6128`. The written order and the shuffled order were not sent as runs of their own, and no second run of these lists was made.

"WebRewind", with the description "Get the picture of a website at a specific date.", has these 5 rewordings:

| Name | Description |
|---|---|
| SiteSnapshot | Website picture for a date. |
| WebTimeMachine | Use this to get a picture of how a website looked on a specific date. |
| RewindWeb | Fetches the picture of a website as of a given date. |
| PageRewinder | Given a website and a date, returns its picture at that date. |
| WebRewinder | A picture of a website at a specific date is retrieved. |

| Rewording, by Jev's probability within an answer | MetaTool, mean of 250 answers | StableToolBench, mean of 250 answers |
|---|---|---|
| Highest | 0.453 | 0.434 |
| Second-highest | 0.248 | 0.241 |
| Third | 0.157 | 0.159 |
| Fourth | 0.092 | 0.102 |
| Lowest | 0.049 | 0.064 |
| Entropy, mean | 1.89 | 1.96 |
| Highest minus second-highest, mean | 0.20 | 0.19 |

| MetaTool, rotated orders | First | Second | Third | Fourth | Fifth |
|---|---|---|---|---|---|
| Mean probability of the entry at this place of the list | 0.214 | 0.184 | 0.177 | 0.208 | 0.218 |
| Answers that select the entry at this place, of 250 | 51 | 46 | 36 | 56 | 61 |
| Mean probability of this rewording, by its place in the file | 0.120 | 0.301 | 0.194 | 0.253 | 0.131 |
| Answers that select this rewording, of 250 | 11 | 96 | 51 | 66 | 26 |

- The entry at the last place is selected in 61 of the 250 answers and the entry at the first place in 51. On StableToolBench the counts are 78 and 30.
- Jev selects the same rewording in all 5 orders for 22 of the 50 queries, in 4 orders for 12, in 3 for 15 and in 2 for 1. On StableToolBench the counts are 13, 19, 12 and 6.
- The second rewording of the file is selected in 96 of the 250 answers and the first in 11. On StableToolBench the counts are 82 and 60.

A first look at the saved answers gave the figure below. The figures script does not print it.

- The probability of one rewording differs by more than 0.10 between its highest and its lowest place in 144 of the 250 cases of a query and a rewording, and by more than 0.20 in 53. On StableToolBench the counts are 167 and 71.

## Copies of one correct tool

Rushab, 2026-10-07: "Let's send ONE query inline here with all options same". Question: how does Jev divide its probability over entries that are the same? Jev's API takes each entry under a name of its own, and the entries of these runs differ in their names only.

### Two single requests

Both requests use the StableToolBench query that names "Flight Search V2", the instruction "Pick all the tools in the list that are relevant to the task at hand.", and the API "Travel / Flight Fare Search / Flight Search V2" five times with its description. In the first the names end in "(1)" to "(5)". Rushab then asked for names without numbers: "add extra spaces randomly". In the second each name has one extra space at a place chosen at random.

| Place in the list | Probability from Jev, names that end in "(1)" to "(5)" | Probability from Jev, names with one extra space |
|---|---|---|
| First | 0.92 | 0.04 |
| Second | 0.04 | 0.07 |
| Third | 0.01 | 0.16 |
| Fourth | 0.01 | 0.34 |
| Fifth | 0.02 | 0.39 |

The two answers are saved under the request hashes that start with `8ae4984f` and `5b3c3e68`. They have no results folder. After the second, Rushab: "There is our paper."

### The copied run

- Examples. The 50 queries of the rotated run of each dataset, with the same chosen tool.
- List. The chosen tool five times, with its description. The names of the 5 copies differ only by extra spaces, at places chosen with the seed. A StableToolBench copy has its extra spaces after one run of spaces of the name: 227 of the 250 copies have 1 extra space and 23 have 2. A MetaTool name has no space, and a copy has 1 to 5 spaces at its end. The "None" candidate is not offered.
- Orders and instruction. The 5 rotations of the list as 5 questions of one request, with "Pick all the tools in the list that are relevant to the task at hand."
- Size and cost. 50 requests for each dataset, 72,174 input tokens on StableToolBench and 65,753 on MetaTool, each under $0.01. The results folders are `results/stabletoolbench_copied/2026-10-07_01` and `results/metatool_copied/2026-10-07_01`, written at commit `22b5c83`. The code names the experiment `copied`. `python scripts/results_figures.py <folder>` prints the figures of the two tables. No margin of error is given.

| Entry, by Jev's probability within an answer | StableToolBench, mean of 250 answers | MetaTool, mean of 250 answers |
|---|---|---|
| Highest | 0.340 | 0.317 |
| Second-highest | 0.239 | 0.233 |
| Third | 0.184 | 0.186 |
| Fourth | 0.136 | 0.149 |
| Lowest | 0.101 | 0.114 |
| Entropy, mean | 2.16 | 2.21 |
| Highest minus second-highest, mean | 0.10 | 0.08 |

| Place in the list | First | Second | Third | Fourth | Fifth |
|---|---|---|---|---|---|
| StableToolBench: mean probability of the entry at this place | 0.140 | 0.132 | 0.193 | 0.230 | 0.306 |
| StableToolBench: answers that select the entry at this place, of 250 | 12 | 8 | 21 | 47 | 162 |
| MetaTool: mean probability of the entry at this place | 0.216 | 0.123 | 0.167 | 0.236 | 0.258 |
| MetaTool: answers that select the entry at this place, of 250 | 77 | 0 | 4 | 67 | 102 |

- An even split gives each entry 0.20 and an entropy of 2.32 bits.
- The entry at the last place is selected in 162 of the 250 answers on StableToolBench and in 102 on MetaTool. The entry at the second place is selected in 8 and in 0.
- Each of the 5 copies is selected in 42 to 60 of the 250 answers on StableToolBench and in 46 to 57 on MetaTool, and its mean probability is 0.19 to 0.21 on both.
- On MetaTool the first place is selected in 50 of the 85 answers of `similar_tools`, in 16 of the 85 of `scenario` and in 11 of the 80 of `multi_tool`. The last place is selected in 30, 36 and 36.
- With 5 rewordings of the tool in place of 5 copies, the highest probability is 0.434 on StableToolBench and 0.453 on MetaTool, and the entry at the last place is selected in 78 and in 61 of 250 answers.

A first look at the saved answers gave the figures below. The figures script does not print them.

- Jev selects the last place in all 5 orders for 9 of the 50 StableToolBench queries and 7 of the 50 MetaTool queries, and the first place in all 5 orders for 1 and for 11.
- The highest probability of an answer is 0.50 or more in 7 of the 250 StableToolBench answers and in 3 of the 250 MetaTool answers.
- The mean probability of a copy is 0.203 with 1 extra space and 0.173 with 2 on StableToolBench, and 0.216, 0.202, 0.212, 0.190 and 0.180 with 1 to 5 spaces at the end on MetaTool.

## The correct tool removed

Decided by Rushab on 2026-10-07: remove the correct tool of a MetaTool query, add the "None" candidate, and move "None" through the 5 places. His reason: the tools of a normal list are not similar enough for the place to show.

- Examples. A seeded sample of 50 queries of the `similar_tools` file.
- List. 4 of the 9 other tools of the query's list, chosen with the seed, and "None". The 9 are the tools most similar to the correct tool, and the correct tool is not in the list. "None" is the correct answer.
- Orders. The 5 rotations of the list as 5 questions of one request. "None" is at the fifth place in the first and at the first place in the last.
- Instruction. The instruction of the MetaTool runs for one tool: "Choose the tool that is applicable to the user's query. If no tool in the list is applicable, choose None."
- Size and cost. 50 requests with 5 questions each, 63,569 input tokens, under $0.01. The results folder is `results/metatool_absent/2026-10-07_01`, written at commit `ac73272`. The code names the experiment `absent`. `python scripts/results_figures.py` prints the answers of "None" for each order. No margin of error is given.

| Place of "None" in the list | Answers of "None", of 50 | Highest probability minus second-highest, mean |
|---|---|---|
| First | 35 | 0.71 |
| Second | 35 | 0.73 |
| Third | 34 | 0.71 |
| Fourth | 37 | 0.74 |
| Fifth | 37 | 0.74 |

- Jev answers "None" in 178 of the 250 answers and selects one of the 4 tools in 72.
- Jev selects the same entry in all 5 orders for 42 of the 50 queries: "None" for 32 and one tool for 10.
- The entries at the five places are selected in 49, 50, 45, 54 and 52 of the 250 answers.
- In MetaTool's own `reliability` file the list holds 10 tools that are unrelated to the query, and Jev answers "None" for 43 of 50 queries with "None" last.

A first look at the saved answers gave the figures below. The figures script does not print them.

- The mean probability of "None" is 0.66, 0.68, 0.65, 0.70 and 0.69 with "None" at the first to the fifth place.
- The probability of "None" differs by 0.09 on average between its 5 places, by more than 0.10 for 15 of the 50 queries and by more than 0.20 for 6.
- 12 of the 50 queries get no answer of "None" in any order.

## How runs are staged

Decided by Rushab on 2026-10-04.

- A run is in the plan only if it proves a claim of the paper.
- The simplest run that can show an effect is run first. Its result is read before the next run is added.
- A repeat run, a control or a second variant is added when a result needs it, such as a difference that is not statistically separable.
- Run-to-run noise changes answers at random and does not favour a position. A difference in CSR between two positions that is larger than its confidence interval needs no repeat run.
- Each proposed run states its claim and its cost.
- Insights come first. Supporting statistics, such as margins of error, are reported in the final paper. No extra run is made for them at this stage. Rushab decided this on 2026-10-05. The code that computes a margin of error from the saved answers stays in `src/grjev/metrics.py`.
- An alternative that is not run is kept as a spare, in one line.
- A small subset of every experiment is run before one experiment on every example. Rushab decided this on 2026-10-05.

## Stages

Question: how do the position of the correct tool, the order of the list and the number of tools change what a decision model selects? Prompt format is a spare factor.

| Stage | Work | Needs |
|---|---|---|
| 1 | MetaTool. Document the fixed positions, build a test set with balanced positions, and run Jev: first the released order and 5 placements of the correct tool, then longer lists with random distractors, up to 199 tools. | Jev API key |
| 2 | Open-weight decision models on the stage 1 runs | Local machine |
| 3 | Two fine-tuned open decision models, one trained on MetaTool's 20,614 queries and one on ToolBench's training set. Each is tested on both benchmarks. | Colab |
| 4 | A smaller set of runs on ToolBench, Mind2Web and AndroidControl | Jev API key |
| 5 | A small student model trained from a stage 3 model. The baseline is a student trained on the labels. Jev is a comparison point. | Colab and local machine |

Nothing is trained on Jev output. TypeSafe's Master Customer Agreement, section 2.3(b), prohibits it.

Measurements: CSR, calibration, confidently wrong answers, latency, and cost. The share of answers that change on an identical repeat is a spare measurement.

## The first run

Every example of the four MetaTool test files with a tool list is sent with its list in the released order. Every example with a correct tool is also sent with the correct tool at 5 positions. A multi-tool example is sent with each of the two wordings of the instruction for two tools. Tool awareness has no tool list and is not in the run.

| Test file | Examples | Tool lists per example | Tool lists | "None" candidate | Jev's answer |
|---|---|---|---|---|---|
| Similar tools | 995 | 6: the released order and 5 placements | 5,970 | Last | The selected candidate |
| Scenario | 1,800 | 6: the released order and 5 placements | 10,800 | Last | The selected candidate |
| Multi-tool | 497 | 18: the released order and 8 placements, with each of the two wordings | 8,946 | Not offered | The two tools with the highest probabilities |
| Reliability | 995 | 1: the released order. The list has no correct tool to place. | 995 | Last, and correct | The selected candidate |
| Total | 4,287 | | 26,711 | | |

- Models. Jev first, then open-weight decision models. Claude is not run.
- Requests. The lists of one example go to Jev as separate questions in one request, with the query as the state. TypeSafe's documentation says every question in a request "is evaluated independently". A multi-tool example takes two requests, one for each wording. That is 4,784 requests.
- Cost. About $0.50 for Jev, from the input tokens measured in the subset of 2026-10-05: about $0.43 for the 22,238 tool lists of the four test files, and about $0.08 for the 4,473 multi-tool lists sent again with the wording `both`.
- Limit. Jev calls are limited to `JEV_CALL_LIMIT`, 1,662 on 2026-10-07, until Rushab raises it.

| Claim the run can show | Read from |
|---|---|
| Jev's selection depends on the position of the correct tool | CSR at each of the 5 positions, per test file |
| MetaTool's fixed positions change the score of a model with a position effect | CSR in the released order minus mean CSR over the 5 positions |
| Jev's score on MetaTool as released | CSR in the released order, the row comparable with published results |
| Jev gives a high probability to wrong selections | The measures of confidently wrong answers, and the tools selected on the reliability file |
| Jev answers "None" for a reason other than its place in the list | The share of "None" answers on similar tools and scenario, next to the share on reliability |
| The distance between two correct tools changes the selection | Multi-tool CSR with the two tools adjacent and separated |

The runner sends these texts to Jev. They are in `src/grjev/constants.py`. Rushab has not confirmed the first two. Both wordings of the instruction for two tools are kept. A change to a text changes every request that holds it.

| Text | Sent with | Wording |
|---|---|---|
| Instruction for one tool | Similar tools, scenario, reliability | "Choose the tool that is applicable to the user's query. If no tool in the list is applicable, choose None." |
| Description of the "None" candidate | Similar tools, scenario, reliability | "No tool in the list is applicable to the user's query." |
| Instruction for two tools, wording `one` | Multi-tool | "Two tools in the list are appropriate to solve the user's query. Choose one of them." |
| Instruction for two tools, wording `both` | Multi-tool | "Two tools in the list are appropriate to solve the user's query. Choose both." |

The state of a request is the query. Each candidate is a tool name with the tool's description. The seed of the orders is `ORDER_SEED` in `src/grjev/constants.py`, and each run writes it to its `config.json`.

## Rules for building a tool list

Decided on 2026-10-04.

- Placement. In every list of 5 or more tools the correct tool is placed at 5 positions: first, 25%, 50%, 75% and last. In a list of N tools the positions are 1 + q × (N − 1) for q = 0, 0.25, 0.5, 0.75 and 1, rounded to the nearest position, with a half rounded down.
- Distractors. They are shuffled once per example with a seed and keep that order in every placement. The lists of one example then differ only in the position of the correct tool.
- Two correct tools. The example gets 8 orders. In 5 the two tools are adjacent and the pair is placed at the 5 positions, starting at 1 + q × (N − 2). In 3 the tools are separated: first and last, first and 50%, 50% and last. A seed decides which tool comes first. The rule follows Baker et al. (arXiv 2412.10079) and is used for MetaTool, ToolBench and BFCL.
- "None". Where it is offered it is the last candidate. The last placement of the correct tool is then position N of N + 1 candidates.
- Two tools from Jev. For a multi-tool example Jev's answer is the two tools with the highest probabilities of one question. The example is correct when they are the two correct tools. When several tools share the second-highest probability, Jev has named no second tool. That counts as a miss, and these cases are counted.

| Tools in the list | Positions of one correct tool | Positions of two adjacent correct tools |
|---|---|---|
| 5 | 1, 2, 3, 4, 5 | 1-2, 2-3, 2-3, 3-4, 4-5 (4 different orders) |
| 10 | 1, 3, 5, 8, 10 | 1-2, 3-4, 5-6, 7-8, 9-10 |
| 15 | 1, 4, 8, 11, 15 | 1-2, 4-5, 7-8, 11-12, 14-15 |
| 20 | 1, 6, 10, 15, 20 | 1-2, 5-6, 10-11, 14-15, 19-20 |
| 50 | 1, 13, 25, 38, 50 | 1-2, 13-14, 25-26, 37-38, 49-50 |
| 100 | 1, 26, 50, 75, 100 | 1-2, 25-26, 50-51, 74-75, 99-100 |
| 199 | 1, 50, 100, 149, 199 | 1-2, 50-51, 99-100, 149-150, 198-199 |

MetaTool's files have lists of 5, 10 and 15 tools.

## The "None" answer

Decided on 2026-10-04. A "None" candidate is offered where the benchmark itself lets the model decline, and nowhere else.

| Test files | Does the benchmark let the model decline? | "None" candidate |
|---|---|---|
| MetaTool similar tools, scenario, reliability | Yes. The released prompt of all three says "If there is a tool in the list that is applicable to this query, please return the name of the tool (you can only choose one tool). If there isn't, please return 'None.'" | Yes |
| MetaTool multi-tool | No. The released prompt says "choose two appropriate tools". | No |
| BFCL | Yes. A model can reply without a function call on any example, and 1,536 examples have no correct function. | Yes |
| StableToolBench | No. Every one of the 765 examples has a relevant API. | No |

Reasons:

- Published results. The CSR figures of the MetaTool paper on the three single-tool files were measured with the answer "None" allowed. Without the candidate, Jev selects among 10 tools, and the published task is a choice among 10 tools and "None". `baibizhe/jev-decision-benchmarks` gives Jev the tool list plus "None" on the single-tool examples.
- False "None" answers. The reliability file measures how often a model answers "None" when no tool is correct. With "None" in the lists that have a correct tool, the runs also measure how often it answers "None" when a correct tool is in the list. A model that answers "None" in 90% of its answers, whatever the list, scores 90% on reliability. On similar tools with "None" offered it scores at most 10%. With "None" left out of similar tools, the 90% has no visible cost.
- One task for both files. Similar tools and reliability use the same 995 queries. With "None" in both, each query is tested with the correct tool present and absent, on the same 11 candidates.
- Use. A caller does not know in advance whether the correct tool is in the list.

Two rules were considered and dropped:

- "None" in every list of every dataset. MetaTool's multi-tool prompt asks for two tools, and StableToolBench has no example without a relevant API. Results on them would not be comparable with published results.
- "None" only in the lists that have no correct tool. The reason first given for dropping it was that the candidate's presence gives away the answer. That reason does not hold: Jev's requests are independent and Jev learns nothing between them. The reason that holds is the second one above.

Decided on 2026-10-04: "None" is always the last candidate, and no run puts it first. Similar tools and reliability use the same 995 queries, with "None" last in both. A model that selects "None" for being last would also select it on similar tools, where it is wrong, and the first run shows that share.

## The released-order run

Decided on 2026-10-04, as part of the first run. Every example is run once with its tool list in the released order, with the candidates of the rule above, and a multi-tool example once with each wording. On MetaTool that is 4,784 tool lists: 995 similar tools, 1,800 scenario, 995 reliability and 994 multi-tool, 497 with each wording.

Published results on MetaTool use the released order: the MetaTool paper, PA-Tool (arXiv 2510.07248) and `baibizhe/jev-decision-benchmarks`. The placement runs reorder the lists, and their results are not comparable with those. The released-order run gives the row that is comparable, and the placement runs are compared against it. The prompt still differs from the MetaTool paper's. Jev receives the query as the state and the tools as candidates. The released prompts of the three single-tool files hold 5 worked examples.

The run adds one measure: CSR in the released order minus mean CSR over the 5 positions. It shows how much a released file with a fixed position overstates a model that leans toward that position.

## Measures

| Measure | What it shows | Source |
|---|---|---|
| CSR at each of the 5 positions of the correct tool | The size of the position effect | Liu et al. (TACL 2024) |
| CSR in the released order | The score comparable with published results | The MetaTool paper |
| CSR in the released order minus mean CSR over the 5 positions | How much a released file with a fixed position overstates a model that leans toward that position | The released-order run |
| Share of selections in each fifth of the list, summarised as half the sum of the gaps between each share and 20% | Which part of the list a model selects from, whether or not the correct tool is there | BiasBusters (arXiv 2510.00307) |
| CSR with adjacent and with separated correct tools | Whether the distance between two correct tools changes the selection | Baker et al. (arXiv 2412.10079) |
| Share of "None" answers, with a correct tool in the list and without | Whether "None" answers follow the list or the candidate's place | The "None" rule |
| Confidently wrong answers | Wrong selections that Jev gives a high probability | arXiv 2609.26550 |

The score is the plain CSR: the percentage of examples with a correct selection, as published results on MetaTool compute it.

MetaTool's uneven counts are reported as a property of MetaTool and are not corrected in the score. `TripTool` is the correct tool in 85 of the 2,795 examples of the similar-tools and scenario files, and `ShoppingAssistant` in 5.

Margins of error are reported in the final paper and not at this stage. `src/grjev/metrics.py` computes one from the saved answers, and the method for the final paper is not decided. The similar-tools file has 199 different tool lists, the scenario file has 9, and the multi-tool file has 15 different correct tools.

## Confidently wrong answers

Decided on 2026-10-04. A confidently wrong answer is a wrong selection to which Jev gives a high probability. A rule that accepts Jev's answer when its probability is high accepts these answers, and no other model checks them. They are measured in every Jev run.

| Measure | Definition |
|---|---|
| Error rate of confident answers | Of the answers whose top probability is at or above a threshold, the share that are wrong |
| Confident share of errors | Of the wrong answers, the share whose top probability is at or above the threshold |
| AUROC of the top probability | How well the top probability separates Jev's wrong answers from its correct ones |

Each is reported by position of the correct tool, by list length and by test file. On the reliability file a confidently wrong answer is a tool selected with a high probability.

The measures are those of arXiv 2609.26550, which uses Jev to judge pairs of model outputs. At a top probability of 0.9 or more it reports a Jev error rate of 2.1% on RewardBench (24 of 1,155 judgments) and 6.5% on JudgeBench (9 of 138). Those errors are 21% and 12% of Jev's errors, against 41% and 25% for GPT-6. On RM-Bench the error rate at 0.9 or more rises from 1.5% on easy pairs to 7.9% on style-adversarial pairs.

The top probability depends on the number of tools. Jev also returns a `confidence`, equal to (top probability − 1/n) / (1 − 1/n) for n tools. Both are saved with every answer. The threshold is not decided.

## After the first run: list length

These runs are designed in detail after the result of the first run is read.

- Distractors. Plain random tools. Rushab, 2026-10-04: if random distractors show the claim, the most similar tools are not run. At 199 tools both give the same list.
- Building a list. For each query the other 198 tools are shuffled once with a seed. A list of L tools is the correct tool and the first L − 1 tools of that order. Each longer list contains the shorter ones, and the list of 199 tools is every tool.
- Lengths. 5, 10, 20, 50, 100 and 199 tools are proposed in `docs/findings/open_items.md`. Not confirmed.
- Placement. The correct tool at the 5 positions in every list.
- Queries. The 1,790 different queries with one correct tool, each once per list. The similar-tools file has 995 different queries and the scenario file 1,060, and 265 are in both. In these runs the list is built by the rule above, and a repeated query would be the same request.
- Size. 1,790 queries, 6 lengths and 5 placements give 53,700 tool lists in 10,740 requests. About $4 for Jev, estimated at 4 characters per token.

One MetaTool query in several test files, "What can this travel companion do for me?", with the correct tool `TripTool`:

| Test file | Tools in the list | Position of `TripTool` |
|---|---|---|
| Similar tools | 10 | 1 |
| Scenario, `TopTool_top5` | 5 | 4 |
| Scenario, `TopTool_top10` | 10 | 4 |
| Scenario, `TopTool_top15` | 15 | 4 |
| Scenario, `Housewife` | 10 | 9 |
| Reliability | 10 | Not in the list |

The first run sends all six, each with its own list.

Facts that bear on these runs:

- With random distractors Jev's CSR may be near 100% at every position. The released similar-tools lists of the first run hold the 9 tools most similar to the correct tool and cover the harder case at 10 tools.
- The MetaTool paper names the "overlapped issue", "a query that can be solved by multiple tools", and says the MetaTool authors merged tools with similar functions. A distractor added from the 199 tools can still answer the query. The share that do has not been measured.
- A list of all 199 tools has 20,476 characters of names and descriptions, about 5,100 tokens at 4 characters per token. The token count is an estimate.

## Spare runs

None of these is run until a result calls for it.

| Spare | What it would show | Added when | Size and estimated cost |
|---|---|---|---|
| The most similar tools as added distractors | Whether a longer list lowers CSR more when the added tools are similar to the correct tool | Random distractors do not show the claim | 44,750 tool lists at 5 lengths, about $2.40 |
| A second run of identical requests | How much of a change between two orders is run-to-run noise | A difference is not statistically separable, or the share of examples whose selection changes between placements is reported | The first run again: 26,711 tool lists, about $0.50 |
| Prompt formats | Whether the selection changes when the same query and tools are written differently, such as a candidate labelled with the tool name or with an id | Rushab, 2026-10-04: "not really required just yet" | About 18,000 tool lists and $0.45 for each added format at 10 tools |
| A second question for a multi-tool example, with the first selected tool removed | The second tool, when several tools share the second-highest probability of one question | Such ties are common in the first run | 4,473 tool lists, about $0.11 |
| CSR averaged over tools | Whether the score comes mostly from the tools with the largest number of examples | Jev scores differently on those tools in the first run | No run |
| Jev's probabilities averaged over the placements | Whether averaging removes a position effect | A position effect is found | No run |

Considered and dropped on 2026-10-04:

- A run with "None" first.
- For multi-tool examples, one choice among the 45 pairs of the 10 tools, the form `baibizhe/jev-decision-benchmarks` uses.
- A reshuffle of the distractors at each placement, and an extra list with only the distractors reshuffled.
- Random distractors drawn only from outside the 20 tools nearest to the correct tool.
- Rotating the list. A list of 199 tools would need 199 orders.
- Claude in the position runs.

## Not decided for the position runs

- The list lengths.
- The probability threshold of a confidently wrong answer.
- Placement with three or more correct tools (176 examples in StableToolBench, 322 in BFCL), in lists under 5 tools (169 and 934 examples), and when the correct tools fill more than half of the list. None of the three occurs in MetaTool.

## Accept or escalate

Direction set on 2026-10-04. The design for tool selection is not confirmed.

Jev selects first. When its top probability is at or above a threshold, the selection is final. Otherwise a frontier LLM, Claude Sonnet 5 or Claude Opus 5, selects on its own. Claude gets one call per example here and no call in the position runs.

The rule is from arXiv 2609.26550 (v3), "JEV-as-a-Judge: Accept When Confident, Escalate When Unsure". That paper picks the threshold on about 100 labelled examples from the grid 0.5, 0.6, 0.7, 0.8, 0.9, 0.95 and 0.99: the lowest threshold whose accuracy stays within 2 points of the stronger model, by a one-sided 95% lower bound. The threshold is fixed before the test examples are run. For a pair of outputs it asks Jev in both orders and averages the probabilities.

| Test set in arXiv 2609.26550 | Share escalated | Accuracy against GPT-6 alone | Share of GPT-6's fee |
|---|---|---|---|
| 1,610 held-out pairs, threshold 0.9 | 31.5% | +0.93 points | 41.4% |
| RewardBench | 25% | +1.27 points | 26.7% |
| JudgeBench | 65% | −0.74 points | 66.8% |

For tool selection the report is CSR against Claude alone, the share of examples escalated, and the tokens used against Claude alone. Not decided: how the threshold is chosen, which Claude model is the fallback, and which test files are used.

## Fine-tuning and transfer

Decided on 2026-10-04.

| Model | MetaTool test files | ToolBench test files |
|---|---|---|
| Jev | No training | No training |
| Open model, not fine-tuned | No training | No training |
| Open model fine-tuned on MetaTool | In-domain | Transfer |
| Open model fine-tuned on ToolBench | Transfer | In-domain |

No model is trained on both sets.

Metrics. The four MetaTool tool-selection files are scored with the Correct Selection Rate (CSR) of the MetaTool paper, the percentage of examples with a correct selection. Tool awareness is scored with accuracy, precision, recall and F1. ToolBench queries have 1 to 6 relevant APIs. The ToolBench score is precision, recall and F1 if the model selects a set, or accuracy if each list is built with one relevant API. This is not decided.

Training data. The MetaTool model trains on `dataset/data/all_clean_data.csv` with the test queries removed. 993 of the 995 similar-tools queries and 1,797 of the 1,800 scenario queries are rows of that file. The ToolBench model trains on ToolBench's training set. ToolBench's six test files hold out queries, tools or RapidAPI categories from that training set.

Limit. MetaTool's tools are ChatGPT plugins from 2023. ToolBench's APIs were collected from RapidAPI in 2023, and StableToolBench reports that 44.4% of its calls to them succeeded. The fine-tuned models and the student are baselines on these two benchmarks. The paper makes no claim from them about current tools. BFCL (ICML 2025, 573 citations on Semantic Scholar on 2026-10-04) was chosen on 2026-10-04 as a test-only set. No model is trained on it.

An audit of the first 28 Jev papers (arXiv 2609.32160) gives a 14-item evaluation checklist. The items that apply here are a baseline that reads label probabilities from an ordinary open model, a model trained on the task, confidence intervals, repeated runs, a pinned model version, and thresholds fixed before evaluation. The audit found that 21 of 27 papers had no label-probability baseline and 12 of 27 reported no confidence intervals or significance tests.

## Jev as a co-pilot

Decided on 2026-10-04. Question: can Jev reduce the token cost of a frontier LLM on difficult tasks? The frontier LLM proposes each function call and Jev checks the choice of function before the call runs. The first measurement is a four-way count on the same examples: both correct, only the LLM wrong, only Jev wrong, both wrong, with whether both select the same wrong function. This is a parallel study to REFLEX (arXiv 2609.26532), in which Jev decides first and a strong LLM is the fallback. The frontier LLMs are Claude Sonnet 5 and Claude Opus 5, called through the Claude Code CLI with thinking and tools switched off and with `--effort low`. Codex is left out, because with tools switched off it still sends the model one tool definition. Not decided: which tasks count as difficult, how token cost is counted, and whether trajectories are run end to end.

## Open items

- Confirm Mind2Web and AndroidControl.
- Decide when the limit of 1,662 Jev calls is raised, and for which runs.
- Decide the claim of the paper. Rushab's proposal of 2026-10-07 is that decision models exaggerate probabilities. Claude Code's proposal is that Jev's probabilities follow how the list is written.
- Find a consequence of the two results for a user of Jev, such as reading several tools from one answer.
- Find why the entry at the last place of a list of 5 copies of one tool is selected in 162 of 250 answers on StableToolBench and in 102 on MetaTool, and the entry at the second place in 8 and in 0. In MetaTool's `similar_tools` file the first place is selected in 50 of 85 answers.
- Run the copied experiment on open-weight decision models.
- Decide whether the order of the rewordings in the two files is changed. The second rewording starts with "Use" for 35 of the 45 StableToolBench APIs and for all 38 MetaTool tools, and it is selected in 82 and in 96 of 250 answers.
- Check whether the queries that name their APIs explain why CSR does not fall with the list length on StableToolBench.
- Find why CSR falls with the list length on MetaTool and not on StableToolBench. A first look counts 7.66 similar wrong tools gained by a MetaTool list as it grows to 199, and 3.46 by a StableToolBench list.
- Decide whether the rule that selects the entries closest to the query by embedding becomes a baseline in the code. On the 50 queries of the MetaTool length run it scores 36 of 50 with 199 tools, and Jev 34 of 50.
- Decide how the number of correct tools is read from one answer of Jev, when the instruction does not state it.
- Confirm the instruction for one tool and the description of the "None" candidate.
- Decide the list lengths of the later runs.
- Decide the threshold for a confidently wrong answer and the accept-or-escalate design.
- Decide how margins of error are computed, for the final paper.
- Decide how a ToolBench example is posed to the model, and its metric.
- Decide which BFCL test files are used, and how a BFCL example is posed to the model.
- Decide last whether fine-tuning stays in the paper.
- Decide which fine-tuned model trains the student.
- Decide whether the MetaTool fine-tuning holds out some tools.
- Choose the open models and check their licences.
- Measure AndroidControl's steps per episode and accessibility-tree size.
- Decide whether to ask TypeSafe for permission to train on Jev output.
- Choose a venue.
