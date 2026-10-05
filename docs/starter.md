# Jev study: starter notes

Last updated 2026-10-05. A subset of two experiments has been run on Jev. Its results are in `docs/plan.md`.

## Draft abstract

Typed decision models return a probability for each option in a list supplied by the caller and generate no text. Jev, released by TypeSafe AI in September 2026, is used in agents to pick tools and interface elements. This paper measures how the option list affects that pick. We vary the position of the correct option and the number of options, and we report how often Jev gives a high probability to a wrong selection. The tasks are tool selection (MetaTool, ToolBench, and BFCL as a test-only set), web browsing (Mind2Web) and mobile device control (AndroidControl). We compare Jev with open-weight decision models and with two fine-tuned open models, one trained on MetaTool and one on ToolBench, and we test each fine-tuned model on the other benchmark. We compare Jev's errors with those of two frontier LLMs, Claude Sonnet 5 and Claude Opus 5, on the same examples. We report three properties of MetaTool's test files. The correct tool is at position 1 in all 995 examples of the similar-tools file, and the two correct tools are at positions 7 and 8 in all 497 examples of the multi-tool file. A rule that ignores the query scores 100% on both. The four files with tool lists hold 2,287 different queries in 4,287 examples. In 1,432 of the 3,292 examples with a correct tool (43.5%), the correct tool is one of 15 tools. We release a version with balanced positions. We also train a small student model from a fine-tuned model and report its accuracy and latency on a laptop. Results are not yet available.

## Status

- Goal set on 2026-10-02: two workshop papers by the end of October 2026.
- Current plan: one paper. After stage 3 we decide whether stage 5 becomes a second paper.
- Datasets: MetaTool and ToolBench come first. BFCL is a test-only set. Mind2Web and AndroidControl are proposed and not confirmed. WebArena and OSWorld are backups for them.
- GPU work runs on Google Colab.
- The Jev key is read from `TYPESAFE_API_KEY`.
- The code standard is in `AGENTS.md`. `docs/plan.md` holds the plan. `docs/dashboard.html` records the datasets, the experiments and the decisions.
- Built: downloads of MetaTool, StableToolBench and BFCL pinned to a commit, the Jev client, the Claude bridge, saved responses with run numbers, the common example format, the converters for MetaTool, StableToolBench and BFCL, and dataset statistics drawn as charts on the dashboard.
- Built: the experiment runner, `scripts/run_experiment.py`, with the experiments `position` and `length`.
- Built: `scripts/results_figures.py`, which prints the figures of a run from its results folder, with 95% bootstrap intervals.
- Not built: the runner for open-weight models.
- Next: the first run on MetaTool, described in `docs/plan.md`. It needs a higher limit on Jev calls.
- `docs/findings/` holds a code review and a list of proposals from 2026-10-04, with a response to each. Findings 2, 3 and 4 of the review were applied on 2026-10-05.
- Calls made: 351 Jev calls, one to check the key and 350 for the subset of 2026-10-05, and short Claude calls to check the bridge.
- Venue not chosen.

## Jev

| Property | Value |
|---|---|
| Maker | TypeSafe AI |
| Release | Limited early access since 2026-09-15 |
| Version | `jev-1.13.0`. `jev-latest` is an alias that moves with new releases. |
| Input | A `state` (text or JSON) and one or more typed questions. Text only. |
| Output | Probabilities. No generated text. |
| Question types | `choice` with up to 255 options, `score` with 2 to 10 ordered levels, `noul` for yes or no |
| Request limits | 64k tokens per request. 32k for the state plus the longest question. 80 requests per second. |
| Price | $0.042 per million input tokens. Output is free. |
| Probability precision | Two decimals |
| Determinism | No seed or temperature setting. Identical requests can return different answers. TypeSafe's parallel-questions cookbook reports run-to-run noise on 2 of 8 yes-or-no questions over 5 repeats. Its consistency cookbook reports Jev's label changing on 2 of 8 choice questions over 15 repeats, with a new id field in the state on each call. |
| Several questions | "Every question in a request sees the same state, is evaluated independently" (TypeSafe documentation, Primitives page) |
| Confidence | For a choice among n options, (top probability − 1/n) / (1 − 1/n). The saved check call returned probabilities 0.89, 0.11 and 0.00 and confidence 0.83. |
| Access | TypeSafe API with a waitlist. Vercel AI Gateway lists `typesafe-ai/jev` at the same price. |

The vendor's page on known weaknesses says: "In some cases, we observed that the order of a Choice's options can affect the answer, and `jev-1.13` leans toward the option that comes first." The same page lists arithmetic, counting, date comparison, multi-step questions and long states with unrelated content as weak areas.

Vercel AI Gateway also lists `liquid/d1`, a second hosted decision model with the same API format, at $0.04 per million input tokens.

### Terms of use

The Master Customer Agreement, last updated 2026-09-23, section 2.3(b), says the customer will not "use the Services or any Output (defined below) to perform model distillation, train a model to imitate the output of the Services, or develop (or to facilitate the development of) a similar or competing product or service". The agreement contains no research exception. A search of its text found no clause about publishing benchmark results.

## Plan

The plan is in `docs/plan.md`: the stages, the design of each experiment, the measures and the open items.

## MetaTool: fixed positions of the correct tool

Source: `HowieHwong/MetaTool`, commit `35e81bb7576826e980c80fed8f8c0a2b4a1e6fbb`, folder `dataset/tmp_dataset`.

| Test file | File | Examples | Tools per list | Position of the correct tool | Score of a fixed-position rule |
|---|---|---|---|---|---|
| Similar tools | `Task2-Subtask1.json` | 995 | 10 | 1 in all 995 examples | 100% |
| Scenario | `Task2-Subtask2.json` | 1,800 | 5, 10 or 15 | Spread evenly over positions | 10% for position 1 |
| Reliability | `Task2-Subtask3.json` | 995 | 10 | Correct tool removed by design | Not applicable |
| Multi-tool | `Task2-Subtask4.json` | 497 | 10 | 7 and 8 in all 497 examples | 100% |

The cause is in `src/prompt/prompt_construction.py`. The similar-tools candidates are the 10 nearest neighbours of the correct tool's own embedding, kept in similarity order, so the correct tool comes first. For the multi-tool list, `select_10_tools_with_exclusion` calls `random.seed(48)` for every example and samples the 8 distractors. The two correct tools are appended last, and `random.shuffle` moves them to positions 7 and 8 every time.

The scenario subtask uses 9 distinct candidate lists. Each tool keeps the same position in its list for every query.

`baibizhe/jev-decision-benchmarks` noted the fixed positions in a Chinese-language report dated 2026-09-19 and stated that it ran no order-randomisation test. Its Jev scores on the original order were 77.79% on similar tools, 87.04% on reliability, and 81.29% and 88.33% on the two multi-tool conditions. arXiv 2608.13959 (Lee, 2026-08-14) reports the similar-tools position: "the candidate list is ordered rather than shuffled, with the gold tool first in all 995 Subtask1 rows". It cites a note by the same author, "The answer is always first", as in preparation, and says the note moves the correct tool through all ten positions on four models. No copy of the note was found on arXiv or GitHub on 2026-10-04. The paper does not mention the multi-tool file. The 12 issues and pull requests of `HowieHwong/MetaTool` have no title about tool order.

## MetaTool: repeated queries and uneven tool counts

Measured on the four test files with tool lists. Tool awareness has no tool list.

| Measurement | Value |
|---|---|
| Different queries | 2,287 in 4,287 examples |
| Scenario file | 1,060 different queries in 1,800 examples. A tool in more than one of the 9 lists has the same 20 queries in each. 265 of the 1,060 are similar-tools queries. |
| Reliability file | The 995 queries of the similar-tools file, with other tool lists |
| Examples with a correct tool | 3,292. The reliability file has none. |
| Examples whose correct tool is one of the 15 tools of the scenario list `TopTool_top15` | 1,432 of 3,292 (43.5%) |
| Examples in which a tool is a correct tool | 89 to 168 for each of those 15 tools. 5 to 65 for each of the other 184, and 5 for 146 of them. |
| Lists that hold a tool | 5 to 1,168 of 4,287, median 120. FinanceTool is in 1,168 (27.2%). CranePumpsManuals, dev and reflect_notes are in 5. |
| Tools in the reliability lists | 89 of 199 |
| Tools used as distractors in the multi-tool lists | 67 of 199 |

The cause is in `src/prompt/prompt_construction.py`. `get_query_by_tool` calls `np.random.seed(48)` before every sample of a tool's queries. `select_10_tools_with_exclusion` calls `random.seed(48)` before every sample of tools for a reliability or multi-tool list. Both correct tools of every multi-tool query are among the 15 tools of `TopTool_top15`.

Other measurements:

- Each prompt in the similar-tools, scenario and reliability files ends with 5 example queries and their tools, different in every row. In 488 of the 995 similar-tools prompts and 920 of the 1,800 scenario prompts, one example has the correct tool as its answer.
- A rule that selects the tool whose name and description share the most words with the query scores 47.9% on the similar-tools file and 43.2% on the scenario file. Stop words are ignored and ties are split evenly.
- In the multi-tool file the descriptions of the correct tools have a mean of 21.1 words, and those of the distractors 13.8.

## ToolBench and BFCL: lists without a distractor, and rules that use no model

Measured on StableToolBench's six test files (765 examples), BFCL's 13 single-turn files (3,641 examples) and BFCL's 4 multi-turn files (3,336 turns, each counted as one example). BFCL's agentic files, `web_search` (100 examples) and `memory` (155 examples on three memory backends), are answered in text and store no function as the label. The rules are scored on the examples whose list has a correct entry and a distractor, and a rule scores when the entry it selects is correct.

| Measurement | StableToolBench | BFCL, single-turn | BFCL, multi-turn |
|---|---|---|---|
| Examples where every entry in the list is correct | 196 of 765 | 1,207 of 3,641 | 0 of 3,336 |
| Examples with no correct entry | 0 | 1,124 | 412 |
| Examples whose label is not a function | 0 | 16, in `live_relevance` | 0 |
| Examples with a correct entry and a distractor | 569 | 1,294, of which 1,053 are in `live_multiple` and 200 in `multiple` | 2,924, 731 in each file |
| Random choice | 38.9% to 49.5% by file | 38.4% on `multiple`, 30.2% on `live_multiple` | 5.7% to 5.8% by file |
| Answering one position every time, best position | 45.7% to 61.7% by file | 36.5% on `multiple`, 36.0% on `live_multiple` | 12.9% to 14.0% by file |
| Word-overlap rule | 75.8% to 88.9% by file | 94.2% on `multiple`, 70.1% on `live_multiple` | 34.6% to 45.4% by file |

- StableToolBench: the API at position 1 is relevant in 484 of the 765 lists (63%), the API at position 5 in 139 of 404 (34%), and the API at position 10 in 22 of 96 (23%).
- StableToolBench: the 61 examples of `G3_instruction` use 7 tools and 44 APIs. The other five files use 88 to 330 tools each.
- StableToolBench: 224 of the 2,490 APIs have a blank description.
- BFCL: 339 of the 1,998 function names have more than one description, up to 30 for `get_current_weather`.
- BFCL: in 653 of the 1,053 examples of `live_multiple`, the correct function has a name of the form `Service_N_Intent`, such as `Movies_3_FindMovies`.
- BFCL multi-turn: a turn's list holds 15 to 39 functions, and its ground truth calls 0 to 7 different functions. 203 turns of `multi_turn_miss_func` and 203 of `multi_turn_miss_param` have no call.
- BFCL multi-turn: in `multi_turn_miss_func_49` the ground truth of the second turn calls `tail`, which the row withholds until the fourth turn.
- BFCL parameter values: the 2,501 single-turn examples with a ground truth have 10,193 accepted parameter values. 63.3% are in the query, 8.3% are true or false, 5.9% are listed in the function's schema, 11.2% may be left out, 2.6% are in the description of the function or of the parameter or are the parameter's default, and 8.8% are none of these. In 1,848 of the 2,501 examples (73.9%) no value has to be rewritten. Of the 892 values that do, 269 are dates or times in a fixed format, 230 are numbers that are not in the query as digits, and 157 are place names with a part added.

## Prior work

A search of arXiv on 2026-10-03 found 76 papers posted since 2026-09-19 that mention Jev or System One models in the title or abstract. Appendix A lists them. None is peer reviewed. The tables below give the results closest to this study.

### Option order, option count and repeat runs

| Source | Finding |
|---|---|
| TypeSafe documentation | `jev-1.13` "leans toward the option that comes first" |
| arXiv 2609.37647 | 37 datasets, 346,009 requests. Rotating the options left accuracy unchanged. |
| `anessbelbati/jev-rerank-bench` | With 30 passages, reversing the order changed Jev's top pick on 400 of 1,617 queries (24.7%). |
| `kachar/jev-tool-search` | With 199 tool options, 241 of 241 answer pairs agreed across orders when both top probabilities were at least 0.6. Every order flip occurred below that level. |
| `123Satyajeet123/jev-wide` | With 200 candidates, 95.8% of returned probabilities were 0.00. An identical repeat changed 7.3% of the top 10. Moving candidates between chunks changed 59% of the top 10. |
| `zaesho/S1Rank` | 52% of probabilities changed across byte-identical requests. |
| `hosamsh/jev-mind2web` | 35 of 698 picks changed between two identical runs. |
| arXiv 2609.38827 | On ordinal scales with 2 to 14 levels, Jev used a smaller share of the scale as levels were added. |
| arXiv 2609.26758 | Renaming two options from 0/1 to no/yes changed the hosted model's AUC from .8146 to .5806. |
| arXiv 2610.00346 | Swapping yes and no flipped 50.5 answers per hundred for Jev. |
| arXiv 2610.00831 | For open models on two 20-option tasks, averaging over rotations of the list cut the order-flip rate from 0.33 to 0.14 and from 0.33 to 0.18. |

### Position and order: methods in prior work

Checked on 2026-10-04.

| Work | List | How the order is varied | Measure |
|---|---|---|---|
| Liu et al., "Lost in the Middle" (TACL 2024) | 10, 20 or 30 documents | The correct document is placed at chosen positions, such as 1, 5, 10, 15 and 20 of 20 | Accuracy at each position |
| RAG-MCP (arXiv 2505.03275) | 1 to 11,100 tools | The correct tool is placed from the top to the bottom of the list | Selection success by position and list length |
| BiasBusters (arXiv 2510.00307) | 5 tools | 5 cyclic rotations, each tool first once | Half the sum of the gaps between each position's share of selections and 1/5 |
| Baker et al. (arXiv 2412.10079) | 20 documents, 2 to 4 of them evidence | 5 adjacent placements and 3 or 4 separated placements | Score at each placement. Higher when the evidence documents are adjacent. |
| Levy et al., FLenQA (arXiv 2402.14848) | 2 key paragraphs in padding text | Adjacent at first, middle and last, and one setting with random gaps | Accuracy in each setting. Higher when the paragraphs are adjacent. |
| Tian et al., LongPiBench (ACL Findings 2025, arXiv 2410.14641) | About 10 relevant pieces in 32K to 256K tokens | The position of the pieces and the distance between them | Recall. It falls 20 to 30% as the distance grows. |

These six test LLMs. arXiv 2407.03007, a study of the stability of tool learning, was returned by the search and not read. None of the works in this table or the table above measures a decision model's position effect on a tool-selection benchmark at several list lengths.

### How later papers report on MetaTool

A check on 2026-10-04 used Semantic Scholar's list of 240 papers that cite MetaTool, read the full text of 35, and confirmed 22 that evaluate on MetaTool data. 183 of the 240 have no citation sentence that names MetaTool, and 6 of those were read.

| Use of MetaTool | Papers | Reported |
|---|---|---|
| The 199 tools as a tool-retrieval corpus | 11 | nDCG@k and Recall@k with k of 1, 5 or 10, on splits made by each paper. Examples: Re-Invoke (EMNLP Findings 2024), ToolRet (ACL 2025). |
| LLMs on the released tool-selection files | 5 | "Accuracy" per file, on the full files or a subsample. PA-Tool (ACL 2026, arXiv 2510.07248) runs the four files, 4,287 examples, with the released few-shot prompt. |
| The tools as a library for an attack on tool selection | 2 | Attack success rate. ToolHijacker (NDSS 2026), ToolFlood (arXiv 2603.13950). |
| Other uses | 4 | Tool awareness with "decision accuracy" (MeCo, ACL 2025), tool planning, and single scores |

No paper whose setup could be verified reports separate zero-shot and five-shot columns. No paper found shuffles MetaTool's tool lists and reports the change. No paper found runs Jev or an open-weight decision model on MetaTool. `baibizhe/jev-decision-benchmarks` runs Jev on the released order.

The MetaTool paper reports CSR per file, zero-shot and five-shot. For multi-tool with the prompt "choose zero, one or two tools" it reports 2/2 CSR, 1/1 CSR and 1/2 CSR, and with the prompt "choose two tools" one CSR.

### Tool selection and agents

| Source | Finding |
|---|---|
| `baibizhe/jev-decision-benchmarks` | Jev on MetaTool, When2Call and BFCL v4. MetaTool scores are in the section above. |
| `kachar/jev-tool-search` | LiveMCPBench, 525 tools, 94 tasks. Share of tasks with a correct tool ranked first: BM25 32%, Voyage embeddings 46%, two-stage Jev search 56%, Voyage rerank-2.5 60%. |
| arXiv 2609.26532 | Jev as a decision layer with an LLM fallback reached 95% success on 100 tasks with 72.7% fewer strong-model calls. The advantage was limited on BFCL and tau-style evaluations. |
| arXiv 2610.01834 | Jev failed when the correct action depended on something not stated in the input, such as a required earlier step. |
| arXiv 2609.30243 | Added context redirected 312 of 508 initially correct decisions (61.4%). |
| arXiv 2609.31142 | One unverified opinion appended to the state flipped 12.1% of decisions. |

### Browsing and computer use

| Source | Finding |
|---|---|
| `browser-use/jev-ultrafast` | Web agent built on Jev. 21,864 GitHub stars on 2026-10-03. |
| arXiv 2609.30186 | Jev-Mobile reached 79% task success on AndroidWorld, against 84% for a step-wise vision-language model, at 73.4% lower API cost. |
| `hosamsh/jev-mind2web` | Draft on one Mind2Web training shard, 706 steps, 50 candidates. Next-element accuracy: Jev 52.1%, GPT-5.4 without reasoning 54.1%, GPT-5.4 with medium reasoning 57.8%. Given a description of the step, Jev picked the correct element 79.2% of the time from a median of 404 candidates. The test splits were not run. |

We found no arXiv paper that runs Jev on a web or desktop benchmark.

### Judging model output

| Source | Finding |
|---|---|
| arXiv 2609.26550 (Carnegie Mellon) | Jev was within three points of GPT-6 where the verdict can be read off the text, at 0.36% of its fee, and behind on math, code and logic. A cascade that escalates low-confidence verdicts was 0.9 points above GPT-6 at 41% of its fee on 1,610 held-out pairs. |
| arXiv 2609.29769 (University of Pennsylvania) | LLM judges cost 16 to 325 times as much as Jev. Jev's accuracy differed significantly from theirs in at most 8 of 27 comparisons. About 96% of LLM verdicts repeated Jev's most confident errors. No cascade beat the best single judge by more than 2.7 points. |

Other judging papers: 2609.27607, 2609.34862, 2609.29429, 2609.33401.

### Other topics

| Topic | Papers and repositories |
|---|---|
| General benchmarks | 2609.37647, 2610.00346, 2609.32160 |
| Medicine | 2609.34024, 2609.27607, 2610.00381 |
| Probability coherence and calibration | 2609.33209, 2609.33971, 2609.37470, 2609.35342, 2610.01006 |
| Agent memory | 2609.23986, 2609.34227, 2609.36059 |
| Reranking | 2609.40241, `anessbelbati/jev-rerank-bench`, `zaesho/S1Rank`, `denser-org/rerank-bench-jev`, `123Satyajeet123/jev-wide` |
| Open decision models and training | 2609.23886, 2609.39111, 2610.02076, 2609.38850, 2610.00831, 2609.36965, 2609.35865, 2609.33843 |
| Security | 2609.28613, 2609.31142, 2609.34862, 2609.33401 |

The SciFact figures in the early project notes (BM25 0.662, BM25 top 200 plus Jev 0.762) come from `123Satyajeet123/jev-wide`.

Searches that returned no arXiv paper:

- Jev on MetaTool or ToolBench
- Jev on Mind2Web, WebArena or OSWorld
- A model trained on Jev output
- Independence of irrelevant alternatives, or decoy options
- Jev output used as embeddings

## Ideas considered

| Idea | Status |
|---|---|
| Tool selection across position, option count and shuffling | In the plan, stages 1 and 4 |
| Comparison with open-weight and fine-tuned models | In the plan, stages 2 and 3 |
| Browsing and computer use | In the plan, stage 4 |
| Small on-device student model | In the plan, stage 5. The teacher is the fine-tuned open model. |
| Jev as the teacher | Dropped. The terms prohibit it without permission. |
| BM25 plus Jev against embedding retrieval | Not in the plan |
| Jev as a judge | Not in the plan |
| Agent memory, medicine, finance, coding, math, chained calls, embeddings | Not in the plan |

## Datasets

Citations are Semantic Scholar counts on 2026-10-03.

| Benchmark | Released | Citations | Size | Format | Correct answers per example | Licence | Role |
|---|---|---|---|---|---|---|---|
| MetaTool | 2023-10 | 240 | 199 tools. 20,614 query and tool pairs. Five test files of 995, 1,800, 995, 497 and 1,040 examples. | JSON prompts with a numbered tool list. CSV of query and tool pairs. | 1. The multi-tool subtask has 2 and the reliability subtask has 0. Lists hold 5, 10 or 15 candidates. | MIT | Main grid and fine-tuning data |
| ToolBench | 2023-07 | 2,360 | 1,100 official test queries. 16,464 APIs in the paper, 13,862 in the ToolRet copy. | Parquet in the ToolRet copy: query and labelled tools with name, description and parameters | Mean 2.39. 40 queries have exactly 1. | Not checked | Second tool set and fine-tuning data |
| BFCL v4 | 2024-02 to 2025-07 | 573 on 2026-10-04 | 13 single-turn files with 3,641 examples, 4 multi-turn files with 800 and 2 agentic files with 255 | JSON lines: a query or 1 to 8 turns, and a list of function definitions with parameter schemas | Function calls with parameter values, or no call. `live_multiple` has 1,053 examples with one call and 2 to 37 functions in the list. | Apache-2.0 | Test only |
| Mind2Web | 2023-06 | 1,501 | Train: 7,775 actions from 1,009 tasks. Test: 1,339, 1,019 and 4,060 actions for new tasks, new websites and new domains. | Parquet: task, cleaned HTML, positive and negative candidate elements, operation | Usually 1 element. One training shard has a median of 404 candidates per page. | CC-BY-4.0 for the original, OpenRAIL for the multimodal copy | Browsing |
| AndroidControl | 2024-06 | 210 | 15,283 demonstrations of 14,548 tasks in 833 apps | TFRecords: goal, step instructions, accessibility trees, screenshots, actions | 1 action per step. Candidates per screen not measured. | Apache-2.0 repository | Computer use on mobile |
| WebArena | 2023-07 | 2,162 | 812 tasks | Live self-hosted websites | No step labels. One pass or fail per task. | Not checked | Backup |
| OSWorld | 2024-04 | 1,269 | 369 tasks | Live desktop virtual machines | No step labels. One pass or fail per task. | Not checked | Backup |

### Notes on the chosen datasets

MetaTool. The tools are ChatGPT plugins from 2023. The MetaTool authors merged plugins with overlapping functions: the paper reports 390 plugins merged into 195 tools. The repository has 199 tools.

ToolBench. Measured on the 1,100 test queries in ToolRet's copy: 96.4% have two or more relevant APIs. StableToolBench keeps 765 of the 1,100 as solvable, in six test files. 6.9% of the 13,862 ToolBench tools in ToolRet's copy have a blank description. StableToolBench reports that 44.4% of its calls to ToolBench APIs succeeded. This study does not call the APIs. The test set is the 765 solvable queries. How a ToolBench example is posed to the model is not decided.

BFCL. Jev's `choice` question returns one of up to 255 options and no parameter values. For Jev, only the choice of function can be scored. Which test files are used is not decided.

Mind2Web. Jev cannot produce the text for typing actions.

AndroidControl. It covers mobile apps, not desktop. The files include screenshots and are large.

WebArena. Audits report that its string matching inflates success by 1.4 to 5.2% and rejects some acceptable answers. WebArena Verified re-audited all 812 tasks. Many tasks need typed text or a written answer, which Jev cannot produce.

OSWorld. Jev needs a planner model and a text view of the screen to act in it.

### Datasets not chosen

| Dataset | Citations | Reason |
|---|---|---|
| Gorilla and APIBench, the origin of BFCL | 1,707 | Candidate lists of four or fewer |
| tau-bench | 1,333 | Interactive |
| API-Bank | 692 | Not evaluated yet |
| AndroidWorld | 462 | Live. Used by Jev-Mobile. |
| Android in the Wild | 387 | Screenshots only |
| APIGen, `xlam-function-calling-60k` | 229 | Possible training data. CC-BY-4.0, gated. |
| WebLINX | 192 | CC-BY-NC-SA-4.0 |
| AgentNet (OpenCUA) | 150 | Desktop, 22.6K tasks, MIT. The released steps are screenshots. |
| ToolRet | 57 | 7.6k tasks over 43k tools from 35 source datasets, including ToolBench and MetaTool |
| LiveMCPBench | 57 | About 95 tasks |
| When2Call | 45 | Four options per example |

## Models to compare

| Arm | Model | Runs on |
|---|---|---|
| Hosted decision model | Jev `jev-1.13.0` | API |
| Second hosted decision model, optional | Liquid d1 | API |
| Open decision models without task training | `Mapika/decider-2b` (1.88 billion parameters, Apache-2.0, 262,144-token context, 295,509 Hugging Face downloads on 2026-10-04), `convaiinnovations/laya` (421 million parameters, Apache-2.0, context length not verified), one 4B model to be chosen | Local machine |
| Open model without decision training | To be chosen. Read through the probabilities of the option labels. | Local machine |
| Fine-tuned | Two open decision models, one fine-tuned on MetaTool's 20,614 queries and one on ToolBench's training set | Colab |
| Released fine-tuned Mind2Web baselines | `osunlp/MindAct_ActionPrediction_flan-t5-base`, `-large`, `-xl`, and `osunlp/MindAct_CandidateGeneration_deberta-v3-base` | Local machine |
| Student | A smaller model trained from a fine-tuned model | Colab for training, local machine for latency |
| Frontier LLMs | Claude Sonnet 5 and Claude Opus 5, with thinking and tools switched off and with `--effort low` | Claude Code CLI with the machine's sign-in |

`Mapika/decider-0.8b` (752 million parameters) and `heman10x/rlcd-modernbert-151m` (151 million parameters) are also Apache-2.0. Licences of the other open models have not been checked. Each open model has its own input format.

The Claude calls pass `--effort low` to the Claude Code CLI, set in `CLAUDE_ARGS` in `src/grjev/constants.py`. Whether the setting changes an answer when thinking is off has not been measured.

## Cost of one Jev pass

Price: $0.042 per million input tokens.

| Benchmark | Data points | Tokens per call | One pass |
|---|---|---|---|
| MetaTool test subtasks | 4,287 | About 800, estimated | About $0.15 |
| MetaTool query pool | 20,614 | About 500 with 10 candidates, about 7,000 with all 199 tools, estimated | $0.45 to $6 |
| ToolBench | 1,100 | About 1,500 with 20 candidates, about 15,000 with 255, estimated | $0.07 to $0.70 |
| Mind2Web test | 6,418 steps | 50 candidates, or the full page | $0.51 to $4.36 |
| Mind2Web train | 7,775 steps | 50 candidates, or the full page | $0.62 to $5.29 |
| AndroidControl | Steps not counted | Not measured | About $10 at 84,000 steps and 3,000 tokens per step. Both figures are guesses. |
| WebArena | 812 tasks | Not measured | About $2 at 15 steps per task and 4,000 tokens per step. Both figures are guesses. |
| OSWorld | 369 tasks | Not measured | About $1.20 at 15 steps per task and 5,000 tokens per step. Both figures are guesses. |

The Mind2Web rates come from `hosamsh/jev-mind2web`: $0.08 per 1,000 steps at 50 candidates and $0.68 per 1,000 steps with the full page. That run paid $3.50 to $7.38 per 1,000 steps for GPT-5.4.

The grid repeats each example across placements and list lengths. Five placements and five list lengths multiply the number of tool lists by 25, and longer lists have more tokens.

## Constraints

- Jev reads text only, returns no text, and accepts at most 255 options per choice question.
- TypeSafe's terms prohibit training a model on Jev output.
- The local machine is an Apple M4 with 16 GB of memory. Training runs on Google Colab.
- The deadline is the end of October 2026.

## Venues

Not chosen. Earlier project notes list WLLFM at IEEE BigData (26 October), the ECIR 2027 reproducibility track (12 October) and AGENT '27 at ICSE (13 November). These deadlines come from those notes and have not been checked.

## Sources

- TypeSafe documentation: https://docs.typesafe.ai
- TypeSafe Master Customer Agreement: https://typesafe.ai/legal/mca
- MetaTool: https://github.com/HowieHwong/MetaTool and arXiv 2310.03128
- ToolBench: arXiv 2307.16789
- StableToolBench: arXiv 2403.07714 and https://github.com/THUNLP-MT/StableToolBench
- ToolRet: arXiv 2503.01763 and https://huggingface.co/datasets/mangopy/ToolRet-Queries
- BFCL: Patil et al., ICML 2025, and https://github.com/ShishirPatil/gorilla
- Mind2Web: arXiv 2306.06070 and https://huggingface.co/datasets/osunlp/Multimodal-Mind2Web
- AndroidControl: arXiv 2406.03679
- WebArena: arXiv 2307.13854
- WebArena Verified: https://servicenow.github.io/webarena-verified/v1.2.3/
- OSWorld: arXiv 2404.07972
- Liu et al., "Lost in the Middle: How Language Models Use Long Contexts", TACL 2024
- RAG-MCP: arXiv 2505.03275
- BiasBusters: arXiv 2510.00307
- Baker et al., "Lost in the Middle, and In-Between": arXiv 2412.10079
- Levy et al., "Same Task, More Tokens" (FLenQA): arXiv 2402.14848
- Tian et al., LongPiBench: arXiv 2410.14641, ACL Findings 2025
- "JEV-as-a-Judge: Accept When Confident, Escalate When Unsure": arXiv 2609.26550
- "Repair, Not Improvement: Decomposing Constrained Decoding in Tool-Call Abstention": arXiv 2608.13959
- PA-Tool: arXiv 2510.07248
- https://github.com/baibizhe/jev-decision-benchmarks
- https://github.com/kachar/jev-tool-search
- https://github.com/hosamsh/jev-mind2web
- https://github.com/browser-use/jev-ultrafast
- https://github.com/anessbelbati/jev-rerank-bench
- https://github.com/zaesho/S1Rank
- https://github.com/123Satyajeet123/jev-wide

## Appendix A: Jev papers on arXiv

Found on 2026-10-03 by searching titles and abstracts for Jev, TypeSafe, "System One model" and "typed decision".

| arXiv ID | Posted | Title |
|---|---|---|
| 2609.22753 | 2026-09-19 | Replacing Large Language Models with Jev Decision Models for Low-Latency Edge Service Orchestration |
| 2609.23136 | 2026-09-19 | Fast Intent-Driven Service Orchestration with Jev for 6G Edge Networks |
| 2609.23886 | 2026-09-20 | this-that-model-1.0: A typed decision model that decides in 30 ms, for a millionth of a cent |
| 2609.23959 | 2026-09-21 | Open-Jev Judgments on CallScreenBench: Calibrated One-Pass Scam Screening with a Small Language Model |
| 2609.23986 | 2026-09-21 | Jev-Mem: System-One-Controlled Agentic Memory for Efficient AI Agents |
| 2609.24052 | 2026-09-21 | Calibrated Decisions at Scale: Converting Police Crash Narratives into Probabilistic Crash Variables with a System One Model (Jev) |
| 2609.24395 | 2026-09-21 | JEVQA - Video Quality from Metadata, Bitstream, and Pixel Features with a General-Purpose Decision Model |
| 2609.24965 | 2026-09-21 | Jev for Scientific Decisions: Evaluating Semantic Choices and Their Consequences |
| 2609.25498 | 2026-09-21 | Universal Fractal Natural Language Decision Map: Real-Time Edge Triage Across Heterogeneous Domains |
| 2610.00213 | 2026-09-21 | Counting the Uncounted: Population-Level Surveillance of Documented Pregnancy and Fetal Harm in Police Crash Narratives with a System One Model (Jev) |
| 2609.25845 | 2026-09-22 | Visual Jev: Accurate and Efficient Decisions from Shared Visual Context |
| 2609.26532 | 2026-09-22 | REFLEX with Jev for Efficient Selective Control in LLM Agents |
| 2609.26550 | 2026-09-22 | JEV-as-a-Judge: Accept When Confident, Escalate When Unsure |
| 2609.26758 | 2026-09-22 | Type-Safe Is Not Error-Free: A Constrained Decision Head Follows the Option Name, Not the Rubric Bound to It |
| 2609.27331 | 2026-09-23 | JEV-Star: Fast, Low-Cost StarCraft II Control with Language-Model Planning |
| 2609.27535 | 2026-09-23 | KITE: Scaling Jev Population Experiments with Sparse Flagship Calibration |
| 2609.27607 | 2026-09-23 | Can Jev Judge Radiology Reports? Evaluating a System One Model for Clinical Factuality |
| 2609.27678 | 2026-09-23 | Same Scores, Different Decisions: Evaluating JEV and Language Models for Legal Document Understanding |
| 2609.28587 | 2026-09-23 | NumericJev: Jev-like LLM Numerical Decoding with Multiway Decision Trees |
| 2609.28613 | 2026-09-23 | Decision Hijacking: Prompt Injection Attacks on Jev's Typed Probabilistic Decisions |
| 2609.28919 | 2026-09-24 | Harness Tokenomics: A Router for the Enterprise Agentic Control Plane |
| 2609.28940 | 2026-09-24 | Calibrated Decision Models for Autonomous Penetration-Testing Harnesses: JEV and Laya as System One Decision Layers for LLM-Driven Pentest Agents |
| 2609.29283 | 2026-09-24 | From Text Decisions to Pixels: An Study of Jev-Style Visual Choice Model |
| 2609.29429 | 2026-09-24 | Just Ask Jev: Reinforcement Learning for Calibrated Decisions as a Zero-Shot Detector of AI Alignment Failures |
| 2609.29769 | 2026-09-24 | JEV vs. LLMs as Rubric Judges: Cheaper, Faster, and Wrong in the Same Places |
| 2609.30186 | 2026-09-24 | Jev-Mobile: Jev as an Executor for Mobile GUI Agents |
| 2609.30216 | 2026-09-24 | Jev in the Wild: A Data-Driven Analysis of the Jev Model's Functionality, Applications and Ecosystem |
| 2609.30243 | 2026-09-24 | JevOut: Natural Context Can Flip Decision Models |
| 2609.30706 | 2026-09-25 | LAVOIR: Teaching a Single-Pass Decision Encoder When and What to Ask with Amortized Value of Information |
| 2609.30922 | 2026-09-25 | JevSoup: System-One Routing for Training-Free LoRA Composition |
| 2609.31142 | 2026-09-25 | JevAdvBench: A Benchmark and Black-Box Attacks for Reinforcement Learning for Calibrated Decisions Models |
| 2609.32160 | 2026-09-26 | Typed Decision Models: An Early Evidence Audit and Evaluation Checklist |
| 2609.35865 | 2026-09-26 | PACT: Pairwise-Anchored Calibrated Tuning for Single-Token Typed Decisions |
| 2609.33209 | 2026-09-27 | Beyond Calibration: Do a Typed-Decision Model's Probabilities Obey the Probability Axioms? |
| 2609.33282 | 2026-09-27 | Multi-Dimensional Comparative Scale Construction for Efficient Personalized Subjective Judgment in High-Traffic Applications |
| 2609.33401 | 2026-09-27 | Evaluating System One Models for Agent Security Decisions: Reliability, Calibration, and Selective Automation |
| 2609.33538 | 2026-09-27 | Jev Matches 7B Language Models for Speech-Neuroprosthesis Rescoring |
| 2609.33609 | 2026-09-27 | You Only Edit Once: Incentivizing In-Context Capability of LLMs via Local Demonstration Refinement |
| 2609.33689 | 2026-09-27 | Type-Safe Decision Frameworks for Agentic 5G Control: A Theory-Driven Testbed Characterization of Where They Can Be Applied |
| 2609.33843 | 2026-09-27 | Laya as a Typed Probabilistic Assessor: An Independent Reproduction and a Preregistered Study of Calibration and Selective Escalation |
| 2609.33874 | 2026-09-27 | JET: Justification Evaluation in Transformer |
| 2609.33971 | 2026-09-27 | Do System One Decisions Add Up? A Study of Probabilistic Coherence |
| 2609.34024 | 2026-09-27 | Jev in Medicine: A Benchmark Evaluation |
| 2609.37470 | 2026-09-27 | Probability Contracts: Accuracy, Coherence, and Decisions Across LLM Interfaces |
| 2609.34180 | 2026-09-28 | Decision Readouts for Text-Mediated Video Anomaly Detection: An Exploratory Evaluation of Jev and Qwen |
| 2609.34227 | 2026-09-28 | When Does Selection Replace Extraction? A Pre-Registered Test of Agent Memory with a Typed Decision Model |
| 2609.34261 | 2026-09-28 | RoboICL: Embodied In-Context Learning with GPT-6 Astra |
| 2609.34862 | 2026-09-28 | JEV as a Judge for Agent Trace Security: An Empirical Comparison with Generative LLM Judges |
| 2609.34963 | 2026-09-28 | JevVibe: Efficient Classification-Guided Secure Code Generation |
| 2609.34969 | 2026-09-28 | NavJev: Efficient Vision-Language Navigation via Action-Centric Visual Compression and Discriminative Action-Semantic Memory |
| 2609.35286 | 2026-09-28 | The Argument and the Letterhead: Source-Position Coherence in AI Evaluation |
| 2609.35293 | 2026-09-28 | Decide, Don't Generate: Competitive Dimensional ABSA with Jev's Typed Decisions |
| 2609.35342 | 2026-09-28 | Jev thinks "I don't know'', but doesn't say it: Introducing Sys1Cal-v1 Dataset for Probability Calibration |
| 2609.36059 | 2026-09-28 | Mnemon: Raw Records, Fast Judgments, Slow Thoughts |
| 2609.36115 | 2026-09-28 | Koa-action: Fast and Consistent Structured Decision Making with Generative LLMs |
| 2609.36154 | 2026-09-28 | More Features Are Not More Evidence: Limits of Training-Free Human Activity Recognition with Jev |
| 2609.36399 | 2026-09-28 | Calibrated to Whom? Persona and Language Effects on Cultural Values in JEV |
| 2609.36965 | 2026-09-29 | Chinese-Jev: Bringing System One Model to Chinese-Language Tasks |
| 2609.37647 | 2026-09-29 | Evaluating and Benchmarking the System One Model Jev |
| 2610.00346 | 2026-09-29 | Benchmarking System One decision models against trained classifiers and language models for automated decision gates |
| 2609.38827 | 2026-09-30 | More Choices, Fewer Decisions: Ordinal-Scale Bias in JEV-like Direct-Decision Models |
| 2609.38850 | 2026-09-30 | OpenJev-RLCD: A Working RLCD Implementation |
| 2609.39111 | 2026-09-30 | Bongard: Training Machine Intuition |
| 2609.39496 | 2026-09-30 | When the Right Answer Is Missing: An Arithmetic-Dependent Rejection Bottleneck in Jev |
| 2609.40241 | 2026-09-30 | Decision-Oriented Recommendation Reranking: An Empirical Study of Jev |
| 2610.00376 | 2026-09-30 | A First Glance at Jev for Network Traffic Classification: Accuracy, Processing Time, and Cost |
| 2610.00381 | 2026-09-30 | OmniMed-Jev: Calibrating LVLM Confidence for Trustworthy Medical Multimodal Decisions via System One |
| 2610.00437 | 2026-09-30 | JevSpawn: Adaptive Agentic Inference through Compositional Action Spaces |
| 2610.00831 | 2026-09-30 | AnyJev Technical Report |
| 2610.01006 | 2026-10-01 | Beyond Answer Confidence: A Controlled Audit of Self-Knowledge in a Black-Box Decision Model |
| 2610.01079 | 2026-10-01 | Jev-IDS: System One Models for Network Intrusion Detection |
| 2610.01231 | 2026-10-01 | Judgement in the Age of Jev: From Evaluation Scarcity to Evaluation Abundance |
| 2610.01834 | 2026-10-01 | Code Owns the Simulation, Jev Owns the Evaluation |
| 2610.02046 | 2026-10-01 | Prune First, Decide Fast: Scalable Semantic Query Processing with JEVDB |
| 2610.02048 | 2026-10-01 | HydroJEV: A one-second, training-free screen for cyber-attack and fault attribution in water distribution networks |
| 2610.02076 | 2026-10-01 | LLM2Jev: LLMs Are Already Jev-Style Decision Models -- When and How to Fine-Tune Them |
