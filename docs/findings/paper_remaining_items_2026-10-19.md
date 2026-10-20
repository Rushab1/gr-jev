# Remaining items of the paper, 2026-10-19

Checked by Claude Code on 2026-10-19 against commit b92e190 and updated on 2026-10-20. The column "Review #" gives the
number of the item in `paper_open_items_2026-10-19.md`. Items 4, 12 and 14 of that file are closed or done and are left
out.

| # | Review # | Item | Status | What was done or remains |
|---|---|---|---|---|
| 1 | 1 | Copies paragraph | Done | The copies were sent again with random IDs as names, and Tables 4, 5 and 9 and the text use those runs (`results/*_copied*/2026-10-19_01`). "The difference" now reads "the gap between the highest and the lowest copy". |
| 2 | 2 | ECE method in the setup | Done | The calibration paragraph of `paper/sections/setup.tex` has no formula. The first-bin figures are only in the results. |
| 3 | 3 | A correct choice below 1/n | Done | `paper/sections/results.tex` says that correct choices are not equally relevant and that relevance alone does not explain the gap. |
| 4 | 6 | Introduction repeats the abstract | Done | The numbers stay. The copies sentence names the random IDs, a threshold sentence was added and "More striking" was removed. The ECE method and first-bin figures were cut from the introduction. |
| 5 | 8 | Table 2 is dense | Done | Table 2 (`tab:datasets`) describes the datasets. The table of runs (`tab:runs`) is in `paper/sections/appendix/runs.tex`. |
| 6 | 11 | No correct choice | Done | The MMLU comparison with Tam et al. (2025) is not in the paper, and the Tam et al. sentence was cut from the introduction. |
| 7 | 13 | Calibration in the abstract | Done | The abstract studies "probability allocation and thresholding". |
| 8 | 5, 7, 9, 10 | Length of the introduction, setup and related work | Later | |
| 9 | | Appendix table of thresholds | Done | `tab:threshold-detail` in `paper/sections/appendix/thresholds.tex`, from `paper/tables/threshold_detail.tex`, built by a script outside the repo. |
| 10 | | Two pages of results and conclusion | Dropped | Rushab: a matter of reducing content. |
| 11 | | Report of the runs | Done | `docs/paper_runs.html` was rebuilt on 2026-10-20. `docs/paper_runs.pdf` was removed. |
| 12 | | Tables with no reference | Open | `tab:instructions` and `tab:copies-example` in `paper/sections/appendix/lists.tex`. |
| 13 | | Terms entry for "Choice" | Open | `paper/sections/appendix/terms.tex:4` reads "a tool, a choice, a passage", defining a choice as a choice. |
| 14 | | Refusals appendix | Open | `paper/sections/appendix/refusals.tex` was counted with the copies runs of 2026-10-11. GPT-6 Luna Decisions refused 1,374 copies lists with random IDs, against 697 with the old names. |
| 15 | | MMLU copies in the report | Open | `results/mmlu_copied*/2026-10-11_01` is in `scripts/definitions/paper_runs.json`, but the current code builds copies with random IDs and cannot rebuild those requests. It feeds the report only. |
