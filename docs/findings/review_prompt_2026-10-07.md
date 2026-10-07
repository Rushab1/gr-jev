# Review prompt: two results on Jev as a tool selector

Claude Code wrote this prompt on 2026-10-07 at Rushab's request. It is for a reviewer with no context. The text between the two lines is the prompt.

---

REVIEW REQUEST: two findings about Jev as a tool selector

You are reviewing research results before a workshop paper is built on them. You have no prior context, so everything you need is below. Please read the rules first.

## Rules for the review

1. Read only. Do not edit files, commit, push, or start any run. Do not call the Jev API. The two scripts named in section 9 only read saved results.
2. Form your own reading of the tables in section 5 before you read our claims in section 6.
3. Report only problems you checked yourself, each with its evidence and its consequence for a claim. Leave out style points, anything listed in section 7, and anything you could not verify.
4. Do not propose statistical machinery such as intervals or tests. The project is at the stage of finding results. To judge whether a difference could be noise, use the run-to-run change given in section 5.
5. Do not spend most of your time on a minor detail.

## 1. What Jev is

Jev, version `jev-1.13.0`, is a decision model from TypeSafe AI. It does not generate text. A request holds a "state", which here is the user's query, and one or more questions. A question holds an instruction and a list of named options, each with a description. For each question Jev returns a probability for every option, with two decimals and a sum of 1, and the option it selects. Questions in one request are answered independently. Jev has no seed, and the same request can return slightly different numbers.

## 2. Terms

- Query: the user's request in a benchmark example. It is sent as the state.
- Tool: something a model can select, with a name and a description. In StableToolBench the unit is an API, which is one function of a tool. "Entry" and "option" mean one item of the list sent to Jev.
- Tool list: the entries offered for one query, in the order sent.
- Place: where an entry stands in the list sent. The first place is the start of the list, and the last place its end.
- Answer: Jev's response to one question, which is one query, one list and one instruction.
- Top entry: the entry with the highest probability of an answer. Second entry: the entry with the second-highest. "Top minus second" is the difference between these two probabilities.
- Selected entry: the option Jev returns as its choice. It is the top entry except when two entries tie.
- Even split: every entry has the same probability, which is 0.20 with 5 entries.
- Entropy: H = minus the sum of p times log2(p) over the probabilities of one answer, in bits. It is 0 when one entry has 1.00 and 2.32 for an even split over 5 entries.
- Correct tool: the entry that the benchmark marks as right for the query. StableToolBench calls these relevant APIs, and 738 of its 765 queries have 2 or more.
- Highest correct and lowest correct: for a query with several correct tools, the correct tool with the highest probability and the one with the lowest.
- Correct answer: for a query with one correct tool, Jev selects that tool. For a query with k correct tools, Jev's k highest probabilities are the k correct tools.
- Normal list: the list that the benchmark gives for the query. Its entries are different tools under their own names and descriptions.
- "None" entry: an option named "None" with the description "No tool in the list is applicable to the user's query." The MetaTool runs on the similar-tools, scenario and reliability files offer it at the last place. The run of experiment G moves it. No other run offers it.
- Random: drawn with the fixed seed 2026. It applies to the sample of queries, to other tools added to a short list, to shuffled orders, and to the places of the extra spaces in a copy.
- Run: one set of requests sent once. Second run: the same requests sent again. Run-to-run change: the difference between the two answers to one request.
- Rewording: a rewritten name and description of one tool with the same meaning. Each tool has 5. Claude Opus 5.5 wrote them. The cosine similarity of a rewording to its tool on Qwen3-Embedding-0.6B embeddings is 0.907 or more.
- Copy: the same tool again with the same description. Jev needs a name of its own for each entry, and the names of the 5 copies differ only by extra spaces: 1 or 2 inside a StableToolBench name, and 1 to 5 at the end of a MetaTool name.
- Written order: the order in which the 5 rewordings are stored. Shuffled order: a random order for each query. Rotated orders: 5 orders of the same 5 entries, each moved by one place, with each entry at each place once. The 5 orders are 5 questions of one request.

## 3. The two benchmarks

MetaTool has 199 tools, which are ChatGPT plugins from 2023, and four test files:

- Similar-tools: 995 queries with 1 correct tool and a list of 10 tools, which are the correct tool and the 9 tools most similar to it.
- Scenario: 1,800 queries with 1 correct tool and a list of 5, 10 or 15 tools, which is one of 9 fixed lists.
- Multi-tool: 497 queries with 2 correct tools and a list of 10 tools.
- Reliability: the 995 similar-tools queries with a list of 10 tools that are unrelated to the query. No tool is correct, and the correct answer is "None".

StableToolBench has 765 queries in six test files and 2,490 APIs. A list holds the APIs of the query, with random other APIs added up to 5, in a random order. 336 of the 765 queries (43.9%) contain the name of a relevant API or of its tool. On MetaTool 170 of 3,292 queries (5.2%) contain the name of a correct tool.

## 4. The experiments

Every run is a seeded sample. Instructions:

- MetaTool, one correct tool: "Choose the tool that is applicable to the user's query. If no tool in the list is applicable, choose None."
- MetaTool, two correct tools: "Two tools in the list are appropriate to solve the user's query. Choose one of them." or the same with "Choose both."
- StableToolBench wording run: "<N> tools in the list are appropriate to solve the user's query." followed by "Choose one of them.", "Choose all of them." or "Choose all of them with equal probability.", and a fourth instruction, "Choose every tool in the list that is needed to solve the user's query."
- Runs with rewordings and with copies: "Pick all the tools in the list that are relevant to the task at hand."

| | Experiment | Results folders |
|---|---|---|
| A | MetaTool position run. 50 queries of each test file with normal lists. The correct tool is placed first, at one quarter, in the middle, at three quarters and last. | `results/metatool_position/2026-10-05_04`, and `2026-10-05_05` for "Choose both." |
| B | Second run of A. | `results/metatool_position/2026-10-07_01` and `2026-10-07_02` |
| C | StableToolBench wording run. 300 queries with normal lists and the four instructions. | `results/stabletoolbench_wording/2026-10-06_01`, second run `2026-10-06_02` |
| D | StableToolBench list-length run. 50 queries with normal lists grown to 199 APIs. | `results/stabletoolbench_growth/2026-10-06_02` |
| E | Rewordings. The list holds only the 5 rewordings of one correct tool, for 50 queries. | StableToolBench: `results/stabletoolbench_reworded/2026-10-06_02` (written order), `results/stabletoolbench_reworded/2026-10-07_01` (shuffled order), `results/stabletoolbench_rotated/2026-10-07_01` (rotated orders). MetaTool: `results/metatool_rotated/2026-10-07_01` (rotated orders) |
| F | Copies. The list holds only 5 copies of one correct tool, in rotated orders, for 50 queries of each benchmark. | `results/stabletoolbench_copied/2026-10-07_01`, `results/metatool_copied/2026-10-07_01` |
| G | The correct tool removed. 50 MetaTool similar-tools queries with a list of 4 of the 9 similar tools and "None", in rotated orders. No tool is correct. | `results/metatool_absent/2026-10-07_01` |

## 5. The results

Result 1: how Jev spreads its probability.

| The list holds | StableToolBench | MetaTool |
|---|---|---|
| 5 copies: mean probability from the highest of an answer to the lowest | 0.34, 0.24, 0.18, 0.14, 0.10 | 0.32, 0.23, 0.19, 0.15, 0.11 |
| 5 rewordings: the same | 0.43, 0.24, 0.16, 0.10, 0.06 | 0.45, 0.25, 0.16, 0.09, 0.05 |
| A normal list: the three highest probabilities | 0.84, 0.12, 0.03 | 0.85, 0.14, 0.01 for the multi-tool file |
| A normal list: top minus second | 0.55 to 0.64 over the 4 instructions | 0.70 to 0.80 over the 4 test files |
| 2 correct tools: highest correct and lowest correct | 0.80 and 0.14 with "Choose all of them." | 0.84 and 0.13 with "Choose both." |
| 2 or more correct tools: the top entry is correct | 276 or 277 of 294 queries | 446 of 450 answers |
| The same queries: every correct tool is found | 203 to 218 of 294 | 314 of 450 with "Choose one of them.", 378 with "Choose both." |
| Asked for equal probabilities | Entropy 0.75 for 2 relevant APIs, against 1.00 for an even split | Not sent |
| The same request sent twice: same selected entry | 1,158 of 1,182 answers | 1,526 of 1,550 answers |

Result 2: how the place in the list changes the answer.

| Run | StableToolBench | MetaTool |
|---|---|---|
| Copies: answers that select the first, second, third, fourth and fifth place, of 250 | 12, 8, 21, 47, 162 | 77, 0, 4, 67, 102 |
| Copies: mean probability at the five places | 0.14, 0.13, 0.19, 0.23, 0.31 | 0.22, 0.12, 0.17, 0.24, 0.26 |
| Copies: answers that select each of the 5 copies, of 250 | 42 to 60 | 46 to 57 |
| Rewordings: answers that select the five places, of 250 | 30, 44, 47, 51, 78 | 51, 46, 36, 56, 61 |
| Rewordings: queries whose selected entry differs between the 5 orders | 37 of 50 | 28 of 50 |
| A normal list with one correct tool: correct answers with it first and with it last, of 50 | Not run | 39 and 38 on similar-tools, 41 and 41 on scenario |
| A normal list: change of the correct tool's probability between its 5 places, mean | Not run | 0.08 on similar-tools, 0.05 on scenario |
| The correct tool removed: answers of "None" with "None" at the first to the fifth place, of 50 | Not run | 35, 35, 34, 37, 37 |
| The same request sent twice: largest change of one probability | 0.10 | 0.10 |

Other facts:

- When the selected entry differs between two runs of one request, the first run gave the two entries probabilities at most 0.10 apart.
- With copies on MetaTool, the first place is selected in 50 of the 85 similar-tools answers, in 16 of the 85 scenario answers and in 11 of the 80 multi-tool answers.
- With the correct tool removed, Jev selects the same entry in all 5 orders for 42 of the 50 queries: "None" for 32 and one tool for 10.
- Two single requests listed one StableToolBench API 5 times. With names that end in "(1)" to "(5)" Jev gave 0.92, 0.04, 0.01, 0.01 and 0.02. With one extra space in each name it gave 0.04, 0.07, 0.16, 0.34 and 0.39 from the first place to the last.
- TypeSafe's documentation says that `jev-1.13` "leans toward the option that comes first".

## 6. Our claims

Read these after you have formed your own view.

a. Jev gives most of its probability to one entry. With several correct tools it finds one and gives the others too little to be read from the answer.
b. Part of this is not about relevance: entries that are the same tool, as rewordings or as copies, get unequal probabilities.
c. The place in the list changes the probabilities in every setting. It decides the selected entry only when the entries are close: with copies, in part with rewordings, and not when Jev gives one entry a lead of 0.7.
d. The answers are stable from run to run, which rules out noise as the source of a and b.

## 7. Known weaknesses

Do not report these back.

- One model. No open-weight decision model has been run.
- 50 queries for each run with rewordings, with copies and with the correct tool removed. No margin of error is given, by decision.
- The 5 rewordings of a tool follow one order of styles: a short description, one that starts with "Use this", one that starts with a verb, one that starts with "Given", and one in the passive. Jev selects the second most often on both benchmarks.
- 43.9% of the StableToolBench queries name a relevant API or its tool.
- Two of the 50 MetaTool queries of the rewording run are the same query with the same tool.
- The result for names that end in "(1)" to "(5)" is one query.
- The place of the correct tool was never varied on StableToolBench with normal lists.

## 8. What we need from you

1. Your own reading of the tables of section 5, in at most 5 sentences, written before you read section 6.
2. The problems you found and checked: what you checked, the evidence, and the claim it weakens.
3. For each claim a to d: supported, partly supported or not supported, with one line. Name any other explanation that fits the numbers as well.
4. Experiment G was run to test claim c with similar tools. Does its result fit claim c, and what else could explain it?
5. The single most important thing that is missing before this is a paper.

## 9. If you have the repository

The path is `/Users/rushab/Projects/research/gr-jev`, on the branch `claude/dataset-stats`.

- `python scripts/results_figures.py <results folder>` prints the figures of one run.
- `python scripts/compare_runs.py <folder> <folder>` compares two runs of the same queries.
- `docs/plan.md` describes the runs. "Two results so far" holds the tables above with their sources.
- Each results folder holds `rows.jsonl` with one row per query: the entries in the order sent, the selected entry and every probability.

---
