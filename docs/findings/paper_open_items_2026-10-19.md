# Open items from the review of 2026-10-19

A reviewer read the draft on 2026-10-19. Rushab and Claude Code went through each weakness. The rows below are the
ones left open or worth another look. Rushab asked to note them here. The numbers are those of the review table;
rows 5, 7, 9 and 10, on the length of the introduction, the setup and the related work, are left for the cut later.

| # | Weakness | Status | What remains |
|---|---|---|---|
| 1 | The copy names differ only by spaces, which the APIs may treat in their own way | Closed by Rushab: no rerun, the copies support the claim of uneven allocation only | The copies paragraph of `paper/sections/results.tex` still gives the first position (99% to 100%) and the last position (59%), and Table 5 (`tab:positions`) gives the positions. These are the figures the whitespace objection is about. In the same paragraph, "the difference" in the sentence after the citation of Deußer et al. reads as the change in accuracy, not the gap between copies. |
| 2 | Allocation and calibration are mixed | Calibration stays as a short study, a precursor to the second paper | The setup still gives the full ECE method with its formula. The Calibration paragraph of the results has 7 sentences, and the appendix holds the calibration table and the reliability figure. The setup is the place to cut. |
| 3 | A correct choice below 1/n does not by itself show a wrong allocation | Agreed, not written | Add at the end of the first results paragraph: "Correct choices can differ in relevance, so a probability below $1/n$ is not by itself a wrong allocation. The identical copies below remove that difference." |
| 4 | The best threshold is chosen on the examples it is scored on | Closed by Rushab: not a limitation | The yes/no cutoff of 0.5 is stated only in the appendix section on thresholds. |
| 6 | The introduction repeats findings of the abstract | Later | |
| 8 | Table 2 is too dense for its importance | Later | |
| 11 | The results do not say why each finding matters | 4 of 5 sentences added | The paragraph on lists with no correct choice is not written. The draft adds that the probabilities of a list sum to 1, and compares the MMLU run with "None of the above" in place of the correct answer (Jev 62%, Liquid d1 71%, GPT-6 Luna Decisions 57%, from `results/mmlu_na_replaced*/2026-10-12_01`) with the mean of 35% for the 28 LLMs of Tam et al. (2025). The paper does not describe the MMLU run yet, so the appendix needs its question set and lists. |
| 12 | The passage text of Table 1 is messy | Done, by hand | `paper/tables/sharapova_rubin_short.tex` is written by `scripts/paper/paper_request.py`. Running it again brings back the Russian name of Sharapova. The comment in `paper/sections/introduction.tex` notes the edit. |
| 13 | The abstract names calibration in its scope | Open | Proposed sentence, before the last one: "Asked one yes/no question per choice, the models are miscalibrated outside the lowest probability bin." |
| 14 | Limitations said "trailing spaces" | Done | |
