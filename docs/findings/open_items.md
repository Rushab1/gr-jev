# Open items before the first Jev run on MetaTool

Written by Claude Code on 2026-10-04 and updated the same day, after Rushab's decisions and a second pass over `docs/plan.md`.

## Items 1 to 10

Rushab decided all ten on 2026-10-04. `open_items_response.md` holds the check of each proposal, and `docs/plan.md` holds the plan that results.

| # | Item | Proposal (Claude Code) | Decision (Rushab) |
|---|---|---|---|
| 1 | Where "None" sits in the list | Last in every list, and a second run of the 995 reliability examples with "None" first | Always last. No run with "None" first. |
| 2 | How Jev returns two tools on the 497 multi-tool examples | Two rounds: Jev selects a tool, the tool is removed from the list, and Jev selects again | The two highest probabilities of one question. A tie for second place counts as a miss, and the ties are counted. A second question is a spare. |
| 3 | List lengths | 5, 10, 20, 50, 100 and 199 tools | The lengths are not confirmed. A longer list contains the shorter ones of the same query. |
| 4 | Distractors added to a list | Random and most similar, at every length | Random only. The most similar tools are a spare. |
| 5 | Positions of the correct tool | First, 25%, middle, 75% and last | First, 25%, 50%, 75% and last |
| 6 | Number of shuffled orders for a query | 5, with the distractors reshuffled at each placement | 5 placements, with one order of the distractors per example |
| 7 | Identical repeats | A second run of every request at 10 tools | No second run until a result needs it |
| 8 | Prompt formats | 4 formats, at 10 tools only | A spare |
| 9 | Which queries run, and how they count | The 1,790 different single-tool queries, each once. Accuracy over the queries and as the mean over the 199 tools. | The first run sends every example of each test file. The list-length runs use the 1,790 queries. The score is the plain CSR, and a mean over tools is a spare. |
| 10 | Lists longer than 199 tools | Not on MetaTool | Not on MetaTool |

The first version of this file also recorded a decision that every list gets a "None" option. Rushab replaced it: the rule is in `docs/plan.md`, section 'The "None" answer'.

The first version counted 98,450 tool lists for the proposals of items 3 to 6. That count no longer describes the plan. `docs/plan.md` gives 22,238 tool lists in 4,287 requests for the first run and 53,700 tool lists in 10,740 requests for the list-length runs.

## Items 11 to 13

Added in the second pass. The proposals are from Claude Code, and Rushab has decided none of them. None adds a run.

| # | Item | Proposal (Claude Code) |
|---|---|---|
| 11 | The threshold of a confidently wrong answer. `docs/plan.md` lists it as not decided, and the first run measures confidently wrong answers. The checklist of arXiv 2609.32160, which the plan applies, asks for thresholds fixed before evaluation. | Fix it before the result of the first run is read: 0.9, the value at which arXiv 2609.26550 counts, with the grid 0.5 to 0.99 reported next to it. |
| 12 | The spare "a second run of identical requests". If the share of examples whose selection changes between placements is taken over the 5 lists of an example and the noise over 2 identical requests, the two shares are not comparable. Example: a model that gives one selection 90% of the time and another 10% of the time, at random, differs in 18% of pairs of answers and in 41% of sets of 5 answers. | Take both shares over pairs: two placements of an example, and two runs of one placement. |
| 13 | Accept or escalate gives Claude one call per example. `docs/plan.md` does not say which tool list of the example that call uses. In the released order the correct tool is at position 1 in all 995 similar-tools examples. | Settle it with the design: Jev and Claude answer the same list, at one placement chosen with a seed for each example. |

Findings 6 to 8 of `review_2026-10-04.md` also concern the plan.

## Other open items

`docs/plan.md` lists them under "Not decided for the position runs" and "Open items", and the dashboard lists them in its Open tab.
