# TMLR review of the paper, 2026-10-21

Ten Claude subagents each compared `paper/tmlr/main.pdf` with one paper that TMLR accepted in October 2026. Eight read the accepted paper from arXiv. Two could not get the accepted paper and compared ours with what TMLR usually expects. All ten gave the verdict major revision. A TMLR action editor decides accept, accept with minor revision, or reject, so a paper that needs a major revision is rejected.

Claude checked each finding marked as checked against the LaTeX source on 2026-10-21. The reviewers did not doubt the numbers. They doubted how the paper reads them.

## Accepted papers

| Accepted paper | Source read | Main text |
|---|---|---|
| MeGA-MP, Metric Graph Advection Message Passing | arXiv 2607.05167 | about 17 pages |
| Test-Time Scaling of Text-to-Image Flow Matching Models with Noise-Rejuvenated Sequential Monte Carlo | arXiv 2610.25479 | about 13.5 pages |
| DiCoDe, Diffusion-Compressed Deep Tokens for Autoregressive Video Generation | arXiv 2412.04446, CVPR version | about 8 two-column pages |
| Mathematical Theory of Collinearity Effects on Machine Learning Variable Importance Measures | arXiv 2510.00557 | about 10 pages |
| MIDAS, Mosaic Input-Specific Differentiable Architecture Search | arXiv 2602.17700 | about 11 pages |
| The Landscape of Medical Agents, A Survey | not found | unknown |
| Model-Agnostic Association Rule Learning with Tabular Foundation Models | arXiv 2602.14622, earlier version | about 11 pages |
| Deterministic Prediction as Global Velocity, Flow Matching for Probabilistic Time-Series Forecast | arXiv 2610.18621 | about 14 pages |
| Public Profile Matters, A Scalable Integrated Approach to Recommend Citations in the Wild | arXiv 2603.17361 | about 10.5 two-column pages |
| What Survives Eviction? Information Recall Locality in Transformer KV Caches | not found | unknown |

Our main text is 6 pages in the TMLR style.

## Findings

| # | Finding | Reviewers | Checked | Kind of work | Fix |
|---|---|---|---|---|---|
| 1 | The uneven split may follow from probabilities that sum to 1. `results.tex` says "a probability below 1/n by itself is not a wrong allocation". Only the identical copies rule this out, and the paper does not lead with them | 10 of 10 | yes | writing | Lead with the identical copies. State in the introduction which allocation the paper expects and why |
| 2 | No reference point. The paper compares the threshold with no other selection rule, such as top-k with k known, a threshold per example, a generative language model or an independent score per choice | 9 | yes | analysis of saved results | Add top-k with k known |
| 3 | The main text has no figure. The exact set figure and the reliability diagram are in the appendix | 9 | yes | layout | Move both figures into the results |
| 4 | No related work section. Nothing on conformal prediction, set-valued prediction or multi-label calibration | 10 | yes | writing | Write a related work section |
| 5 | The introduction gives 64% to 78% (exact set among lists where every correct choice ranks above every distractor, appendix table `threshold_detail`). The results give 0.34 to 0.64 (all lists). The results do not connect the two | 8 | yes | writing | Report both in the results with their denominators |
| 6 | The second paragraph of the introduction does not follow. "each correct choice must have a baseline probability" | 8 | yes | writing | Rewrite the paragraph |
| 7 | The threshold is chosen on the evaluation data, with no held-out split | 6 | yes | analysis of saved results | Choose the threshold on one half of the examples and report the other half |
| 8 | Each request was sent once, so the paper reports no variation between runs | 6 | yes | new model calls | Report a second run with `--run 2` |
| 9 | The best F1 of a threshold is 0.75 to 0.88 (appendix table `threshold_detail`). The abstract says "a probability threshold does not identify the set of correct choices" | 3 | yes | writing | Limit the claim to exact set accuracy, or argue why F1 does not measure the task |
| 10 | The copies result may be the first-position bias and a tie-break on the random IDs. Liquid d1 and GPT-6 Luna Decisions predict the first copy in 76% to 98% of their answers | 3 | not checked | analysis of saved results | Report the gap over the 5 cyclic orders, separately from position |
| 11 | `availability.tex` links `github.com/Rushab1/gr-jev`, which names the author in a double-blind submission | 1 | yes | layout | Remove the link from the submitted version |
| 12 | The main text is 6 pages. The accepted papers have 10 to 17 | 10 | yes | follows from 1 to 4 | none of its own |

One reviewer said the caption of the dataset table gives every list 10 choices. The caption names the exceptions, so that finding is wrong and is left out.

## Strengths named by the reviewers

- The identical copies in 5 cyclic orders are a cleaner control than the accepted papers have.
- Bootstrap intervals over examples. Most accepted papers report a mean or a standard deviation over 3 to 10 seeds.
- Three models and three datasets, with thousands of examples for each pair.
- A worked example in Table 1, with names replaced by invented ones.
- Saved responses and a pinned Jev version.

## Finding 1

The paper's argument is in the second paragraph of `introduction.tex`. It says that probabilities summing to 1 lower the share of each correct choice as the number of correct choices grows, and that the constraint still allows an even split. Two correct choices in a list of 10 can each receive 0.5, and five identical copies can each receive 0.2.

The reviewers read the main allocation result, a correct choice below 1/n in 28% to 50% of ranked lists, as compatible with a single-choice distribution that works as designed. A model asked for one choice may put most of the probability on the choice it prefers. A reader then needs a case where the expected allocation is known.

The identical copies give that case. Five copies of one correct choice carry the same content, so an even split gives each copy 0.20. The models give the highest copy 17 to 79 percentage points more than the lowest copy. The Sharapova and Rubin example in Table 1 gives a second case. Both passages are needed to answer the question, and the models give one passage more than 0.90.
