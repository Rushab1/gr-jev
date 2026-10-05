# Response to the open items before the first Jev run on MetaTool

Written by Claude Code on 2026-10-04, in the session that wrote `docs/plan.md`. Each proposal of `open_items.md` was checked against the data and against the plan as Rushab decided it on 2026-10-04. "Accepted" means I agree with the proposal. Rushab decides each item. Nothing was changed for an item.

## Rushab's decisions on 2026-10-04, after this response

The verdicts below are Claude Code's. Rushab's decisions replace them where the two differ, and `docs/plan.md` holds the plan that results.

| # | Item | Decision |
|---|---|---|
| 1 | Where "None" sits | Always last. No run with "None" first. |
| 2 | How Jev returns two tools | The two highest probabilities of one question. No second question. A tie for second place counts as a miss, and the ties are counted. The second question is a spare. |
| 3 | List lengths | A longer list contains the shorter one. For each query the other 198 tools are shuffled once with a seed, and a list of L tools takes the first L − 1. The lengths themselves are not confirmed. |
| 4 | Distractors added to a list | Plain random only. The most similar tools are a spare, run if random distractors do not show the claim. The rule of drawing from outside the 20 nearest tools is dropped. |
| 5 | Positions of the correct tool | First, 25%, 50%, 75% and last |
| 6 | Number of shuffled orders | 5 placements, with one order of the distractors per example. The extra list with reshuffled distractors is dropped. |
| 7 | Identical repeats | No second run until a result needs it. One run first. |
| 8 | Prompt formats | Spare: "not really required just yet". |
| 9 | Which queries run, and how they count | The first run sends every example of each test file. The list-length runs use each of the 1,790 different queries once. The score is the plain CSR. The uneven counts per tool are reported as a property of MetaTool, and a per-tool average is a spare. |
| 10 | Lists longer than 199 tools | Not on MetaTool |

Rushab's rule for all of it: a run is in the plan only if it proves a claim of the paper, the simplest run is run first, and a repeat run, a control or a second variant is added when a result needs it. The two additions to item 2 of this response and the change to item 1 are dropped under that rule.

## The two statements at the top of `open_items.md`

| Statement | Status |
|---|---|
| "every list gets a None option" | Replaced by Rushab on 2026-10-04. "None" is offered on MetaTool's similar-tools, scenario and reliability files and on BFCL. It is not offered on MetaTool's multi-tool file or on StableToolBench. The rule and its reasons are in `docs/plan.md`, section 'The "None" answer'. |
| The grid runs Jev and the open-weight decision models, and Claude is not run on it | Matches the plan |

## Verdicts

| # | Item | Proposal | Verdict |
|---|---|---|---|
| 1 | Where "None" sits | Last in every list. A second run of the reliability file with "None" first. | Accepted, with one change: the second run covers the similar-tools file too. |
| 2 | How Jev returns two tools | Two rounds | Accepted, with two additions |
| 3 | List lengths | 5, 10, 20, 50, 100 and 199 tools | Accepted, on the condition that a longer list contains the shorter one |
| 4 | Distractors added to a list | Random and most similar, at every length | Accepted, with one addition |
| 5 | Positions of the correct tool | First, 25%, middle, 75% and last | Accepted. Rushab decided it on 2026-10-04. |
| 6 | Number of shuffled orders | 5, and each placement reshuffles the distractors | Not accepted. The plan keeps one order of the distractors per example. |
| 7 | Identical repeats | A second run of every request at 10 tools | Accepted |
| 8 | Prompt formats | 4 formats, at 10 tools only | Accepted in part: the scope, not the 4 formats |
| 9 | Which queries run, and how they count | The 1,790 different single-tool queries. Accuracy over queries and as the mean over the 199 tools. | Accepted for the grid of lengths and distractors. The runs on the released lists of each test file stay. |
| 10 | Lists longer than 199 tools | Not on MetaTool | Accepted |

## How the runs fit together

`open_items.md` describes one grid. The plan has two more sets of runs, decided on 2026-10-04.

| Runs | Examples | Tool lists | What it gives | Status |
|---|---|---|---|---|
| Released order | The 4,287 examples of the four test files with a tool list | 4,287 | The row that is comparable with published results | Decided |
| Placements on the released lists | The 3,292 examples with a correct tool | 17,951 | The position effect on MetaTool's own lists. The orders of the reliability lists are not decided. | Decided |
| Lengths and kinds of distractor | The 1,790 different single-tool queries | 98,450 | The effect of list length and of the kind of distractor | Proposed in `open_items.md` |

A request that occurs in two sets is sent once. The response store saves a response under the hash of the request, and the second set reads the saved file.

## 1. Where "None" sits

Checked: with a "None" candidate last, the last position is correct in 995 of the 995 reliability examples, by construction. No reliability list holds a tool named None.

TypeSafe's documentation says `jev-1.13` "leans toward the option that comes first". A run with "None" first puts that lean on the side of "None". The reliability score can rise. The cost is a wrong "None" on lists that have a correct tool, and the reliability file has none.

Change to the proposal: the run with "None" first covers the similar-tools file as well. It has the same 995 queries. The two files together show the rise on one and the fall on the other.

With "None" last, the "last" placement of the correct tool is position N of N + 1 candidates.

One alternative was considered: keep "None" out of the list and ask a separate yes-or-no question, "is any tool in the list applicable". It removes the position of "None" from the design. It differs from MetaTool's prompt and from `baibizhe/jev-decision-benchmarks`, and it needs a threshold. Not recommended.

## 2. How Jev returns two tools

| Way | Requests per tool list | What Jev selects from | Comment |
|---|---|---|---|
| The two highest probabilities of one question | 1 | The tools | The question asks for one tool. If Jev puts nearly all the probability on one tool, the second place is a tie at 0.00, because probabilities have two decimals. Not measured for lists of 10 tools. `123Satyajeet123/jev-wide` reports 95.8% of probabilities at 0.00 with 200 candidates. |
| Two rounds, the proposal | 2 | The tools, then the tools less the first selection | Always returns two tools. The second list has 9 tools, and each tool after the removed one moves up one position. |
| One choice among the 45 pairs | 1 | The 45 pairs of the 10 tools | The form `baibizhe/jev-decision-benchmarks` uses, with a score of 88.33%. The candidates are pairs, so the placement rule for tools does not apply. |

Two rounds is accepted. Two additions:

- Report the two highest probabilities of the first round as well. It costs no request and shows whether one question would have been enough.
- In the released-order run, also ask the 45-pair question, 497 questions. It is the only form comparable with the `baibizhe` score.

Score: an example counts for 2/2 CSR when both rounds select a correct tool. The MetaTool paper reports one CSR for its prompt "choose two tools".

Size: 497 examples, 8 orders and 2 rounds give 7,952 requests for the placement runs.

## 3. List lengths

Accepted: 5, 10, 20, 50, 100 and 199 tools.

Condition: for one query and one kind of distractor, the list of 20 tools contains the list of 10, which contains the list of 5. A longer list is then the shorter list with distractors added. Rushab described the runs that way on 2026-10-04: "multiple runs of same questions with added distractors".

15 tools is not among the lengths. The 300 scenario examples with a released list of 15 tools are run in the placements on the released lists.

The scenario file holds a second series of lengths. Checked: the list of scenario `TopTool_top5` is the first 5 tools of the `TopTool_top10` list, which is the first 10 tools of the `TopTool_top15` list.

## 4. Distractors added to a list

Accepted: random and most similar, at every length.

Checked:

- `dataset/tool_embedding.pkl` holds 201 embeddings of 1,536 numbers each: the 199 tools, and `LawyerPR_PreliminaryReview` and `legal_document_retrieval`, which are not in the tool list.
- With those two removed, the 10 nearest tools by cosine similarity, the tool itself first, are the released similar-tools list in the same order for 199 of 199 tools.
- The file holds lists, dicts, strings and numbers only. It was read with an unpickler that refuses every global.

At 10 tools the most-similar list is therefore the released similar-tools list.

Addition: the random kind draws from the tools outside the 20 nearest to the correct tool. MetaTool builds its reliability and multi-tool lists that way (`get_excluded_tool_list`). The two kinds then add different tools: the nearest ones, and ones that are not near. This holds for lists up to 100 tools. At 199 tools both kinds are the full tool list.

Risk: the most-similar kind adds the tools most likely to answer the query as well. The MetaTool paper calls this the "overlapped issue". `docs/plan.md` lists a check of a sample of errors on the longest lists as not decided.

## 5. Positions of the correct tool

Accepted. Rushab decided on 2026-10-04: first, 25%, 50%, 75% and last, in every list of 5 or more tools. The positions are 1 + q × (N − 1), rounded to the nearest position, with a half rounded down. "Middle" in a list of 10 tools is position 5. The table is in `docs/plan.md`.

## 6. Number of shuffled orders

The count of 5 orders is accepted. The reshuffle of the distractors at each placement is not.

The plan shuffles the distractors once per example with a seed and keeps that order in all 5 placements. The 5 lists of an example then differ only in the position of the correct tool. A change of selection between two of them comes from that position or from run-to-run noise, and item 7 measures the noise.

With a reshuffle at each placement, the same change can also come from the order of the distractors, and the two causes cannot be separated within an example. Mean CSR at each position stays unbiased over many examples and gets noisier.

What the proposal measures and the plan does not: the effect of the order of the distractors with the correct tool held in place. The dashboard lists "Order" as one of four factors.

Suggested instead, for Rushab to decide: one more list per example at 10 tools, with the correct tool at the 50% position and the distractors shuffled with a second seed. It gives the share of examples whose selection changes when only the order of the distractors changes. Size: 1,790 queries and 2 kinds of distractor give 3,580 lists.

Not verified: how Liu et al. order the other documents when they move the correct one.

## 7. Identical repeats

Accepted: a second run of every request at 10 tools, saved as run 2 in the response store. It gives the share of answers that change when the request does not, and every figure on order is read against it.

Size: 1,790 queries, 2 kinds of distractor and 5 placements give 17,900 lists.

## 8. Prompt formats

Accepted: 4 formats, at 10 tools only. One factor changes at a time, and each added format costs 17,900 lists.

Not accepted as proposed: the set of 4. Three of the proposed formats change how the tool name is written, and one adds the prefix "Query:". The format effects reported for Jev so far concern the label of a candidate:

- arXiv 2609.26758: renaming two options from 0/1 to no/yes changed the hosted model's AUC from .8146 to .5806.
- arXiv 2610.00346: swapping yes and no flipped 50.5 answers per hundred.
- `baibizhe/jev-decision-benchmarks` gives Jev option ids made from the list order, not tool names.

Suggested set, for Rushab to decide:

| Format | Candidate label | Candidate text |
|---|---|---|
| 1, the base | The tool name as written | The description |
| 2 | An id made from the position, such as T1 to T10 | The tool name and the description |
| 3 | The tool name split into words | The description |
| 4 | The tool name as written, and the query with the prefix "Query:" | The description |

Format 2 replaces the lower-case name of the proposal. It links the runs to the one existing Jev result on MetaTool.

## 9. Which queries run, and how they count

Checked:

- The similar-tools file has 995 different queries and the scenario file 1,060. 265 are in both. Together they are 1,790 different queries, each with one correct tool.
- 146 tools are the correct tool of 5 of the 1,790 queries, and 53 tools of 20.

Accepted for the grid of lengths and distractors: each of the 1,790 queries once per list. The grid builds its own lists, so a repeated query would repeat a request.

Accepted: accuracy over the queries and as the mean over the 199 tools. The mean over tools gives each tool the same weight. It would settle the open item "Whether accuracy is also reported per tool, and whether a repeated query counts once".

Not accepted as a replacement for the runs on each test file. On 2026-10-04 Rushab asked for the test files to stay in the design, and the plan places the correct tool on the released lists of similar tools, scenario and multi-tool. In the scenario file a query can be in several scenarios, with a different tool list in each: 620 queries are in 1 scenario, 220 in 2, 140 in 3 and 80 in 4. The 1,800 examples are 1,800 different pairs of query and tool list.

## 10. Lists longer than 199 tools

Accepted. MetaTool has 199 tools. The open item "Whether to test lists longer than 199 tools" then concerns ToolBench only.

## Size of the grid

Checked: 1,790 queries, 11 lists and 5 orders give 98,450 tool lists. The mean of 15.2 words in a tool's name and description matches the project's word rule.

The 98,450 are tool lists and not requests. The 5 placements of one list go to Jev as 5 questions of one request. TypeSafe's documentation says every question in a request "is evaluated independently". That gives 19,690 requests. Five placements of 199 tools are about 25,600 tokens at 4 characters per token, under the limit of 64k tokens per request.

Cost: $5.50 under the assumptions of `open_items.md`. At 4 characters per token, which is 25.7 tokens per tool, the same grid is about $6.70. Neither rate is measured for Jev.

Not in the 98,450:

| Runs | Tool lists |
|---|---|
| The repeat of item 7 | 17,900 |
| Three more prompt formats at 10 tools | 53,700 |
| The released-order run | 4,287 |
| Placements on the released lists | 17,951 |
| The runs with "None" first, the second round of multi-tool, and the orders of the reliability lists | Not counted |

Jev calls are limited to 100 until Rushab raises the limit. 1 call has been made.
