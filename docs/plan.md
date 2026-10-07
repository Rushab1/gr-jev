# Jev study: plan

Last updated 2026-10-06. Two sets of runs have been made on Jev: a subset of the position and length experiments on MetaTool, 350 calls, and two runs on subsets of StableToolBench, the wording run with 300 calls and the list-length run with 59 calls.

This file holds the plan: the next steps, the first run, the rules for building a tool list, the measures, the later runs, and the points not decided. Background on Jev, the datasets and prior work is in `docs/starter.md`. `docs/dashboard.html` shows the same plan with the datasets. `docs/findings/` holds a code review, a list of proposals, and a response to each.

## Next steps

The runner is built: `scripts/run_experiment.py`, with `src/grjev/placement.py`, `src/grjev/runs.py` and `src/grjev/results.py`. It runs the experiments `position`, `length`, `wording` and `growth` on a dataset in the common format, and `--examples` takes a seeded sample of an exact number of examples over all the test files. `python scripts/run_experiment.py position --dry-run` prints the Jev calls of a run and sends nothing.

A subset was run on 2026-10-05, on Rushab's instruction to run a small subset of every experiment before one experiment on every example. Its results are under "Subset of 2026-10-05" and on the Results tab of `docs/dashboard.html`.

The wording run on a subset of StableToolBench was made on 2026-10-06. Its design and results are under "Several correct tools: the wording run". The list-length run on StableToolBench was made the same day, and is under "List length on StableToolBench".

1. The runs on every example wait. Rushab decided this on 2026-10-05, after the subset.
2. Rushab raises the limit of Jev calls, `JEV_CALL_LIMIT` in `src/grjev/constants.py`. It is 710, and 710 calls have been made. The position run on every example needs 4,534 more calls with both two-tool wordings and the length run 3,480 more, which takes the saved calls to 8,724. A run that would pass the limit does not start.
3. When Rushab decides to run on every example: the position run needs 4,534 more calls and the length run 3,480 more. The 4,534 are 4,087 calls with the wording "one" and 447 calls for the multi-tool examples with the wording "both". On every example the position run costs about $0.50 with both wordings, and the length run about $4.80.
4. Build the runner for open-weight decision models and repeat the first run on them.

The three open points of the code review in `docs/findings/review_2026-10-04.md` were applied on 2026-10-05, on Rushab's instruction. `jev.ask` validates a response before it is saved (finding 2). The documents name `--effort low` (finding 4). The two check scripts make a new call on every run (finding 3). Claude Code took that option, and Rushab confirmed it the same day: a health check on a model calls the model. One run of `scripts/check_jev.py` uses 1 Jev call of the limit.

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

Not decided: how the number of relevant APIs is read from an answer when the instruction does not state it. A first look at the saved answers of the wording `every` gave the three figures below. The figures script does not print them.

- The largest drop between two neighbouring probabilities comes right after the top API in 250 of the 300 answers. The APIs above the drop are exactly the relevant APIs in 28 of 300.
- Selecting every API with a probability of 0.03 or more gives exactly the relevant APIs in 155 of 300. The cut of 0.03 was chosen on these same answers.
- With the number of relevant APIs given to the scoring rule, the highest probabilities are the relevant APIs in 215 of 300.

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

Rushab asked on 2026-10-06 how many tools or APIs are similar to a given one in each benchmark. This is a first look. The name and description of each of the 199 MetaTool tools and of the 2,490 StableToolBench APIs were embedded with `sentence-transformers/all-MiniLM-L6-v2`, and two entries count as similar when the cosine similarity of their embeddings is 0.32 or more. At 0.32 a MetaTool tool has 9 similar tools on average, which is the size of MetaTool's own lists of closest tools. The code and the model are not in the repo.

| | MetaTool | StableToolBench |
|---|---|---|
| Entries | 199 tools | 2,490 APIs in 819 tools and 47 categories |
| Similar entries per entry at 0.32, mean | 9.0 of 198 (4.5%) | 120.8 of 2,489 (4.9%) |
| Similar entries per entry at 0.60, mean | 0.1 | 5.5, of which 3.0 are APIs of the same tool |
| Wrong entries in the list of 199 that are similar to a correct one, mean | 9.9 | 19.8, of which 17.0 were added by growing the list |

- The measure agrees in part with MetaTool's own lists, which come from OpenAI's `text-embedding-ada-002`: of the 9 closest tools of a tool, 3.8 are among its 9 nearest by this measure.
- A StableToolBench API has 4.6 other APIs in its own tool on average, and 97% of the pairs of APIs of one tool are similar at 0.32.
- The grown StableToolBench lists hold more similar wrong entries than the MetaTool lists, and Jev's score does not fall on StableToolBench. The similarity of the added entries does not explain the difference between the two benchmarks.

A rule with no model call was scored on the same lists: it selects the entries whose embedding is closest to the embedding of the query, as many as the query has correct entries.

| Tools in the list | MetaTool: Jev correct, 50 queries | MetaTool: embedding rule correct | StableToolBench: Jev correct, 50 queries | StableToolBench: embedding rule correct |
|---|---|---|---|---|
| 5 on MetaTool, 5 to 11 on StableToolBench | 43 | 48 | 33 | 25 |
| 10 | 42 | 45 | not sent | not sent |
| 20 | 39 | 43 | 34 | 22 |
| 50 | 41 | 39 | 33 | 21 |
| 100 | 38 | 37 | 30 | 21 |
| 199 | 34 | 35 | 32 | 19 |

- The MetaTool columns use the lists with the correct tool first. Jev's lists on MetaTool hold a "None" candidate, and the rule cannot answer "None". The StableToolBench columns use the wording `every`.
- On MetaTool the rule scores within 5 queries of Jev at every list length, and both fall as the list grows. On StableToolBench the rule falls from 25 to 19 of 50 and Jev stays between 30 and 34.

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
- Limit. Jev calls are limited to `JEV_CALL_LIMIT`, 710 on 2026-10-06, until Rushab raises it.

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
- Decide when the limit of 710 Jev calls is raised, and for which runs.
- Find why CSR falls with the list length on MetaTool and not on StableToolBench. The similarity of the added tools does not explain it.
- Decide whether the rule that selects the entries closest to the query by embedding becomes a baseline in the code. On the 50 queries of the MetaTool length run it scores 35 of 50 with 199 tools, and Jev 34 of 50.
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
