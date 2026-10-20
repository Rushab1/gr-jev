# Open items, 2026-10-20

Checked by Claude Code on 2026-10-20 against commit f8e0093 and the working tree. This file holds the items still open
from the findings files of 2026-10-04 to 2026-10-19, which were deleted, and the new items found in the check.

## Paper

| # | Where | Item | Source |
|---|---|---|---|
| 1 | `paper/sections/results.tex:39` | The first sentence of the copies paragraph says the gap between the highest and the lowest copy is "17 to 78 percentage points". Table 4 (`paper/tables/copies.tex`) gives 17 to 79, as do the same paragraph, the abstract and `paper/sections/introduction.tex:31`. | New |
| 2 | `paper/tables/threshold_detail.tex` | No script in `scripts/` or `src/` writes the table. `AGENTS.md` asks for every paper table to be built by code in the repository. | Remaining items of 2026-10-19, item 9 |
| 3 | `paper/tables/sharapova_rubin_short.tex` | The bold dates and the ellipsis in place of Sharapova's Russian name are edits by hand (`paper/sections/introduction.tex:7`). Running `scripts/paper/paper_request.py` again overwrites them. | Review of 2026-10-19, row 12 |
| 4 | `paper/sections/appendix/terms.tex`, `paper/sections/appendix/refusals.tex` | The "Choice" entry and the refusal counts (20,404 of 186,103 questions, 2,054 of 34,530 lists) are in the working tree only, not committed. | Remaining items of 2026-10-19, items 13 and 14 |
| 5 | Introduction, setup, related work | Their length, rows 5, 7, 9 and 10 of the review of 2026-10-19, is left for the cut later. | Remaining items of 2026-10-19, item 8 |

## Findings files

| # | Where | Item | Source |
|---|---|---|---|
| 6 | `docs/findings/review_2026-10-15_thresholds.md:19-32` | The table "Figures checked" and the paragraph under it no longer match `docs/thresholds.md`, rebuilt on 2026-10-19. HotpotQA now has 983 to 1,000 examples, not 494 to 498. At 0.25, yes/no recall is 0.52 to 0.97, not 0.54 to 0.97. The recall of the other correct choices at 0.25 is 0.15 to 0.35 for the list and 0.25 to 0.96 for yes/no, not 0.15 to 0.36 and 0.28 to 0.96. | New |

## `docs/plan.md`

None of these items changes the paper. They concern measures of the first MetaTool run that the paper does not use.

| # | Where | Item | Source |
|---|---|---|---|
| 7 | `docs/plan.md:777` | The plan says the similar-tools and reliability files test each query "on the same 11 candidates". For all 995 queries, the two lists of 10 tools share no tool. MetaTool builds a reliability list from tools outside the 20 nearest to the correct tool. | Review of 2026-10-04, finding 8 |
| 8 | `docs/plan.md:802` | The share of selections in each fifth of the list, summarised as half the sum of the gaps to 20%, does not start at 0% on the multi-tool file. In a list of 10 tools the 8 orders of two correct tools put 25% of the correct-tool positions in the first, third and last fifths and 12.5% in the second and fourth. A model that selects both correct tools in every order scores 15%. | Review of 2026-10-04, finding 6 |
| 9 | `docs/plan.md:723`, `:793`, `:801` | "CSR in the released order minus mean CSR over the 5 positions" changes the position of the correct tool and the order of the distractors at once. CSR at the first placement minus mean CSR over the 5 positions changes the position only. | Review of 2026-10-04, finding 7 |
| 10 | `docs/plan.md:884`, `:944` | The probability threshold of a confidently wrong answer is not decided. The proposal was 0.9, with the grid 0.5 to 0.99. | Open items of 2026-10-04, item 11 |
| 11 | `docs/plan.md:866` | The spare "a second run of identical requests" compares a share over the 5 lists of an example with a share over 2 identical requests. A model that gives one selection 90% of the time differs in 18% of pairs and in 41% of sets of 5. The proposal was to take both shares over pairs. | Open items of 2026-10-04, item 12 |
| 12 | `docs/plan.md:887` | Accept or escalate gives Claude one call per example, and the plan does not say which tool list of the example that call uses. In the released order the correct tool is at position 1 in all 995 similar-tools examples. | Open items of 2026-10-04, item 13 |
