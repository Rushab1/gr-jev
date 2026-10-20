# Review of 2026-10-15: probability thresholds on examples with several correct choices

A reviewer's reading of the threshold charts, saved on Rushab's instruction, with the figures checked against
`docs/thresholds.md` and the points that Rushab noted the same day. The chart and the table are written by
`python scripts/report/threshold_charts.py --chart docs/thresholds.png --table docs/thresholds.md`.

## Rushab's points

1. Good ranking does not guarantee useful probability allocation. Models can distinguish correct choices from distractors while assigning very little probability to some correct alternatives.
2. Probability allocation is inconsistent even for identical alternatives. This is especially compelling because differences in correctness or relevance cannot explain the result.
3. The behavior has practical consequences. Your thresholding experiments show the difference between partial recovery and complete-set selection, while also showing that yes/no elicitation is not always better.

## Figures checked

The ranges run over Jev, Liquid d1 and GPT-6 Luna Decisions. The examples are 497 MetaTool queries, 983 to 1,000 of the
1,000 HotpotQA questions of the yes/no run and 160 to 192 ECtHR cases, each answered both as a list and as yes/no
questions.

| Claim of the review | Checked figure |
|---|---|
| At 0.25, list precision 0.80 to 0.96 | 0.80 to 0.96 |
| At 0.25, list recall 0.51 to 0.67 | 0.51 to 0.67 |
| At 0.25, yes/no recall 0.54 to 0.97 | 0.52 to 0.97 |
| At 0.50, list recall 0.37 to 0.48 | 0.37 to 0.48 |
| At 0.50, yes/no recall 0.66 to 0.85 on MetaTool and 0.68 to 0.94 on ECtHR | 0.66 to 0.85 and 0.68 to 0.94 |
| Models can rank reasonably well | Every correct choice is above every distractor in 52% to 85% of the lists (`docs/below_uniform.md`) |

The list's recall at 0.50 is the highest correct choice of each example alone. Probabilities that sum to 1 cannot put
two choices above 0.50. One correct choice per example gives a recall of 0.50 on MetaTool and HotpotQA, with 2 correct
choices each, and of 0.44 on ECtHR, with 435 correct articles in the 192 cases that Jev and Liquid d1 answered. The recall of the correct choices other
than the highest one is 0.00 at 0.50 for every model and dataset. At 0.25 it is 0.15 to 0.35 for the list, and 0.25 to
0.96 for yes/no. The table gives it as "Recall of the other correct choices".

## The review

> What the results show
>
> 1. Choice probabilities have high precision but substantially lower recall.
> At threshold 0.25:
> - Choice precision: 0.80–0.96
> - Choice recall: 0.51–0.67
> - Yes/no recall: 0.54–0.97
>
> This supports your distinction between correctly identifying promising alternatives and recovering all correct alternatives.
>
> 2. Increasing the threshold disproportionately harms Choice recall.
> At threshold 0.50, Choice recall drops to 0.37–0.48 across the three datasets, while yes/no recall remains 0.66–0.85 on MetaTool and 0.68–0.94 on ECtHR.
> Of course, the Choice decline is partly structural: normalized probabilities cannot assign more than 0.5 to multiple alternatives simultaneously. You should explicitly acknowledge this.
>
> 3. HotpotQA is an important counterexample.
> Yes/no does not consistently achieve better recall on HotpotQA. This suggests that independent binary elicitation is not a universally superior solution, which makes the paper's conclusions more nuanced.
>
> What this means for your evaluation
>
> I now see a particularly coherent empirical story:
>
> | Evaluation | Finding |
> |---|---|
> | Correct-versus-distractor ranking | Models can rank reasonably well |
> | Precision | Selected choices are often correct |
> | Recall | Many correct choices are excluded |
> | Exact-set accuracy | Recovering the complete correct set is difficult |
> | Identical-choice experiment | Allocation disparities persist even when alternatives are identical |
>
> My recommendation remains to prioritize exact-set accuracy in the main paper, with precision and recall as supporting results.
>
> One caution: high precision and lower recall do not necessarily establish poor calibration. They establish a limitation of threshold-based complete-set selection, which is the more defensible claim.
>
> The most compelling message is:
>
> Decision models may distinguish correct choices from distractors reasonably well, yet their normalized probability allocations make recovering every correct choice through a probability threshold substantially harder.
>
> That is a clear, practically relevant result for ACL Findings.

## Second review: the recall of the other correct choices

Saved on Rushab's instruction. It reads the row "Recall of the correct choices other than the highest correct choice
of each example" of `docs/thresholds.png`, whose panels are MetaTool, HotpotQA and ECtHR from left to right.

On the reviewer's last detail: the highest correct choice is removed separately for each form, as the code of
`other_recall` in `src/grjev/thresholds.py` does. The list curve and the yes/no curve can therefore leave out
different correct choices of the same example.

> This may be your most informative downstream figure so far. It directly addresses the concern you raised earlier: ordinary recall may look reasonably high simply because the model assigns substantial probability to its highest-scoring correct choice.
>
> Here, you exclude that choice and measure recall of the remaining correct alternatives.
>
> ### What the figure shows
>
> Assuming the panels are MetaTool, HotpotQA, and ECtHR from left to right:
>
> - MetaTool: Choice recall declines rapidly, while yes/no retains substantially higher recall across most thresholds.
> - HotpotQA: Both formulations struggle, and the advantage of yes/no is much smaller and model-dependent.
> - ECtHR: The contrast is particularly striking. Choice recall falls rapidly, while yes/no recovers many additional correct alternatives even at moderate thresholds.
>
> This provides more targeted evidence for your central claim than ordinary recall.
>
> ### Why this matters for ACL Findings
>
> Your results now distinguish three things:
>
> 1. Ranking: Models can distinguish correct choices from distractors.
> 2. Ordinary recall: Models recover a reasonable fraction of correct choices, partly because their highest-scoring correct choice is often assigned substantial probability.
> 3. Additional-correct-choice recall: Once that choice is excluded, the normalized Choice formulation often struggles to recover the remaining valid alternatives.
>
> The third is especially relevant because your paper asks whether these probabilities can identify multiple correct choices, rather than just one.
>
> ### Two methodological cautions
>
> First, this metric deliberately excludes the highest-probability correct choice. That makes it a diagnostic of probability allocation to secondary correct alternatives, not a conventional overall recall measure. State that clearly.
>
> Second, at thresholds of 0.5 or higher, zero recall for remaining correct choices is largely guaranteed by normalization. The more interesting empirical evidence is therefore at lower thresholds, where multiple choices can still exceed the threshold.
>
> Also, recall alone does not penalize selecting distractors, so retain exact-set accuracy as the complementary selection metric.
>
> ### My recommendation for your ARR paper
>
> I would prioritize:
>
> - Main text: Correct-versus-distractor ranking results, identical-choice inconsistency, and this additional-correct-choice recall figure.
> - Main text or appendix depending on space: Exact-set accuracy versus threshold.
> - Appendix: F1, conventional recall, and precision curves.
>
> One detail is important: specify whether you remove the highest-scoring correct choice separately for each elicitation formulation. If so, the two curves evaluate recovery of each formulation's own lower-ranked correct alternatives, rather than necessarily the same alternatives.
>
> My assessment: This figure strengthens the paper because it isolates precisely what makes multi-answer probability allocation problematic. It shows more than the familiar mathematical constraint that normalized probabilities sum to one; at low thresholds, it reveals substantial empirical differences in how much probability models assign to additional correct choices.
