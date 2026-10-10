# Paper plan: what the probabilities of decision models mean

Last updated 2026-10-09. This file holds the claims of the paper, the results so far, the runs on every example with their cost, and what is not built or not decided. The history of the runs is in `docs/plan.md`. The figures of every run and model are in `docs/all_runs.md`.

## Terms

- **Decision model**: a model that takes a query and typed questions and returns probabilities and no text. The four tested are Jev (TypeSafe AI), Liquid d1 (Liquid AI), GPT-6 Luna Decisions (OpenAI) and Laya (Convai Innovations).
- **Option**: one entry of the list sent with a query: a tool on MetaTool, an API on StableToolBench, a choice on MMLU, a passage on HotpotQA.
- **Correct option** and **distractor**: an option that the dataset labels as correct for the query, and an option that it does not.
- **List question**: one question of type `choice` with a list of options. The answer holds one probability per option, and the probabilities sum to 1.
- **Yes/no question**: one question of type `noul` about one option. The answer is one probability of "yes". Questions do not share a total.
- **Prediction**: the option that the model selects. **Confidence**: the highest probability of an answer.
- **Duplicate options**: 5 copies of one correct option whose names differ only by extra spaces.
- **NOTA**: the option "None" on MetaTool and "None of the above" on MMLU.
- **Refusal**: an answer of type `refusal` with no probabilities. Only GPT-6 Luna Decisions returns it.

## Claims

| | Claim | The answer that the options justify | What the models do in the runs so far |
|---|---|---|---|
| 1 | The position of an option decides its probability when the options are identical | 0.20 for each of 5 duplicate options | The favoured position gets 0.22 to 0.81 on average. Jev favours the last position. Liquid d1, GPT-6 Luna Decisions and Laya favour the first |
| 2 | With several correct options in a list, one of them takes most of the probability | An equal split: 0.50 each for 2 correct options | The highest correct option gets 0.80 to 0.85 and the lowest 0.11 to 0.14, on MetaTool queries that need 2 tools |
| 3 | With no correct option in a list, the models stay confident | A low highest probability, or a refusal | Mean confidence 0.56 to 0.84 on 5 random distractors. GPT-6 Luna Decisions refuses 125 and 207 of 250 lists. Jev and Liquid d1 never refuse |

Rushab, 2026-10-09: "A choice answer sums to 1, so of course the second correct option gets little" is wrong. A sum of 1 means the correct options share the probability. It does not make one of them take 0.85 or more.

Observations that support the claims:

- With one correct option among distractors, the mean probability is the same at every position. MMLU with 4 choices: 0.25, 0.25, 0.25, 0.25 on Jev, 0.24 to 0.26 on Liquid d1 and on GPT-6 Luna Decisions.
- A second run of the same requests on Jev gives the same prediction in 1,158 of 1,182 answers on StableToolBench and in 1,526 of 1,550 on MetaTool.
- The instruction "Choose all of them with equal probability." does not give an equal split. On StableToolBench Jev's highest correct API has 0.72 and its lowest 0.13.
- One HotpotQA question, under "One HotpotQA question" below: a supporting passage has 0.00 to 0.05 in the list, 0.90 to 1.00 when the other supporting passage is removed, and 0.76 to 1.00 as a yes/no question.

## Models

| Model | Asked through | Version | Price per million input tokens |
|---|---|---|---|
| Jev | TypeSafe's API | `jev-1.13.0` | $0.042 |
| Liquid d1 | Vercel AI Gateway, `liquid/d1` | The gateway takes no version | $0.04 |
| GPT-6 Luna Decisions | Vercel AI Gateway, `openai/gpt-6-luna-decisions` | The gateway takes no version | $0.10 |
| Laya | Vercel AI Gateway, `convaiinnovations/laya` | The gateway takes no version | $0 through 2026-10-31 |

- Rushab, 2026-10-08: no model is hosted by us. OpenJev (`openjev/openjev`, 27.4 billion parameters) has no hosted API on Hugging Face, Vercel AI Gateway or OpenRouter, and is left out.
- Laya is left out of the runs on every example. It rejected 2,784 of the 7,667 lists of the 2026-10-09 runs as too long, and its accuracy on MMLU with 4 choices is 0.24. Its figures stay in `docs/all_runs.md`.
- Laya's repository `NandhaKishorM/laya` reports the share of answers that change when the options are permuted: 0.150, 0.040 and 0.000 on three test sets, and "Jev measured at 0.13". The source of the Jev figure is not named there.

## Datasets

| Dataset | Examples in the runs on every example | Correct options in a list | In the repository |
|---|---|---|---|
| MetaTool | 3,292 in `similar_tools`, `scenario` and `multi_tool`, and 995 in `reliability` | 1, or 2 in `multi_tool` | Yes |
| StableToolBench | 765 | 1 to 6 | Yes |
| MMLU | 13,096 questions of `test_standalone` | 1 | Yes |
| HotpotQA, distractor setting, validation split | 7,405 questions, 7,345 of them with 10 passages | 2 supporting passages in every question | No. Downloaded outside the repository on 2026-10-09 from `hotpotqa/hotpot_qa`, revision `1908d6af` |

- Rushab chose HotpotQA on 2026-10-09 as the dataset with several correct options in a list: passage selection for retrieval-augmented generation. Its licence is CC BY-SA 4.0.
- MultiRC was looked at the same day and dropped. Rushab: "these are very basic pre-llm tests". OpenAlex lists 4 papers of 2026 that name MultiRC in the title or abstract, and 553 that name HotpotQA.

## Results so far

Each run has 50 examples unless stated. Jev was asked from 2026-10-05 to 2026-10-08, and the gateway models on 2026-10-09 with the same requests. GPT-6 Luna Decisions refused some lists, and its figures are over the lists it answered.

### Claim 1: 5 duplicate options

Answers with the prediction at each position, from the first to the last:

| Dataset | Jev | Liquid d1 | GPT-6 Luna Decisions | Laya |
|---|---|---|---|---|
| MetaTool | 77, 0, 4, 67, 102 | 250, 0, 0, 0, 0 | 243, 0, 0, 0, 2 | 129, 65, 28, 8, 0 |
| StableToolBench | 12, 8, 21, 47, 162 | 245, 5, 0, 0, 0 | 229, 10, 2, 2, 4 | 123, 67, 35, 5, 0 |
| MMLU | 19, 2, 9, 44, 176 | 208, 25, 8, 4, 5 | 201, 18, 7, 6, 3 | 113, 47, 24, 21, 45 |

Highest minus lowest probability of an answer, mean over the answers. An answer of 0.20 for each duplicate gives 0:

| Dataset | Jev | Liquid d1 | GPT-6 Luna Decisions |
|---|---|---|---|
| MetaTool | 0.20 | 0.78 | 0.76 |
| StableToolBench | 0.24 | 0.68 | 0.61 |
| MMLU | 0.24 | 0.40 | 0.71 |

### Claim 2: several correct options

Mean probability of the highest and of the lowest correct option. Two correct options at 0.50 each give a difference of 0:

| Run | Jev | Liquid d1 | GPT-6 Luna Decisions |
|---|---|---|---|
| MetaTool `multi_tool`, 2 correct tools, "Choose one of them." | 0.85 and 0.12 | 0.80 and 0.14 | 0.80 and 0.11 |
| StableToolBench, 2 to 6 correct APIs, "Choose all of them." | 0.75 and 0.12 | 0.73 and 0.11 | 0.69 and 0.11 |

On MetaTool `multi_tool` with "Choose one of them.", the highest correct tool minus the lowest is 0.95 or more in 130, 85 and 106 of 450 answers on Jev, Liquid d1 and GPT-6 Luna Decisions.

### Claim 3: no correct option

| Run | Jev | Liquid d1 | GPT-6 Luna Decisions |
|---|---|---|---|
| MetaTool, 5 random distractors, mean confidence | 0.81 | 0.80 | 0.84 on 125 lists, 125 refused |
| MMLU, 5 random distractors, mean confidence | 0.56 | 0.59 | 0.73 on 43 lists, 207 refused |
| MetaTool, 4 random distractors and NOTA, share of the answers that are NOTA | 0.93 | 0.95 | 0.90 |
| MMLU, 4 random distractors and NOTA, share of the answers that are NOTA | 1.00 | 1.00 | 1.00 |
| MMLU, the 3 distractors of the question and NOTA, share of the answers that are NOTA | 0.79 | 0.86 | 0.59 |

### Baseline: MMLU with the 4 choices of the question

| | Jev | Liquid d1 | GPT-6 Luna Decisions |
|---|---|---|---|
| Accuracy | 0.91 | 0.84 | 0.81 |
| Mean confidence | 0.96 | 0.88 | 0.88 |
| Overconfidence: mean confidence minus accuracy | +0.05 | +0.04 | +0.07 |

### One HotpotQA question

Question `5a8d5fc6554299585d9e37c6`: "What's the name of the fantasy film starring Sarah Bolger, featuring a New England family who discover magical creatures around their estate?" Its supporting passages are "The Spiderwick Chronicles (film)" and "Sarah Bolger". The instruction of the list question is "Choose every passage in the list that is needed to answer the question." The yes/no question is "May this passage support the answer to the question?" with the passage.

| What is asked | Passage | Jev | Liquid d1 | GPT-6 Luna Decisions |
|---|---|---|---|---|
| List of 10 passages | The Spiderwick Chronicles (film) | 0.99 | 0.96 | 0.97 |
| List of 10 passages | Sarah Bolger | 0.01 | 0.04 | 0.02 |
| List of 9, "The Spiderwick Chronicles (film)" removed | Sarah Bolger | 1.00 | 0.98 | 0.90 |
| List of the 8 distractors | The distractor with the highest probability | 0.31 | 0.73 | 0.36 |
| Yes/no question per passage | The Spiderwick Chronicles (film) | 0.98 | 0.99 | 1.00 |
| Yes/no question per passage | Sarah Bolger | 0.76 | 0.84 | 1.00 |
| Yes/no question per passage | The distractor with the highest probability | 0.04 | 0.03 | 0.00 |

- With "is needed to answer" or "may support the answer" as the instruction of the list question, no probability of the list of 10 changes by more than 0.02.
- With "Is this passage needed to answer the question?" as the yes/no question, GPT-6 Luna Decisions gives 0.59, 0.45 and 0.41 to three distractors, and Liquid d1 gives "Sarah Bolger" 0.15.
- This is one question. It is not a rate.

## Runs on every example

The cost is the number of examples times the input tokens per example times the price. The tokens per example of MetaTool, StableToolBench and MMLU are those measured in the runs on 50 examples. The tokens per example of HotpotQA are those of the one question above. A refusal of GPT-6 Luna Decisions costs fewer tokens than an answer.

| Claim | Run | Examples | Jev | Liquid d1 | GPT-6 Luna Decisions |
|---|---|---|---|---|---|
| 1 | MetaTool, 5 duplicates of a correct tool | 3,292 | $0.18 | $0.12 | $0.39 |
| 1 | StableToolBench, 5 duplicates of a correct API | 765 | $0.05 | $0.03 | $0.10 |
| 1 | MMLU, 5 duplicates of the correct choice | 13,096 | $0.43 | $0.38 | $1.03 |
| 2 | MetaTool `multi_tool`, "Choose one of them." | 497 | $0.08 | $0.05 | $0.16 |
| 2 | MetaTool `multi_tool`, "Choose both." | 497 | $0.08 | $0.05 | $0.16 |
| 2 | StableToolBench, the list of the example, 4 instructions | 765 | $0.05 | $0.03 | $0.11 |
| 2 | HotpotQA, list of 10 passages | 7,405 | $0.47 | $0.32 | $0.88 |
| 2 | HotpotQA, the supporting passage with the highest probability removed | 7,405 | $0.43 | $0.29 | $0.79 |
| 2 | HotpotQA, a yes/no question per passage | 7,405 | $0.49 | $0.50 | $1.94 |
| 3 | MetaTool, 5 random distractors | 3,292 | $0.17 | $0.11 | $0.38 |
| 3 | MMLU, 5 random distractors | 13,096 | $0.44 | $0.38 | $1.05 |
| 3 | HotpotQA, both supporting passages removed | 7,405 | $0.40 | $0.27 | $0.73 |
| 3 | MetaTool `similar_tools`, 4 random distractors and NOTA | 995 | $0.05 | $0.03 | $0.11 |
| 3 | MMLU, 4 random distractors and NOTA | 13,096 | $0.42 | $0.37 | $1.07 |
| 3 | MMLU, the 3 distractors of the question and NOTA | 13,096 | $0.32 | $0.26 | $0.78 |
| Baseline | MMLU, the 4 choices in 4 cyclic permutations | 13,096 | $0.33 | $0.27 | $0.80 |
| Baseline | MetaTool `similar_tools`, `scenario` and `reliability`, the list of the example | 3,790 | $0.37 | $0.24 | $0.75 |
| Baseline | MetaTool and StableToolBench, 5 paraphrased options | 1,864 | $0.10 | $0.06 | $0.19 |
| | **Total** | **110,857 requests per model** | **$4.86** | **$3.75** | **$11.41** |

The three models together cost about $20.02.

- Paraphrased options exist for 38 MetaTool tools and 45 StableToolBench APIs. The runs with them cover 1,767 MetaTool examples and 97 StableToolBench examples.
- The MetaTool run with 4 similar distractors and NOTA is left out. The label "None" of that run is not verified.
- The yes/no run on every example is not decided. Claim 2 does not need it. It shows what a yes/no question returns for the same passages.

### List length

Rushab, 2026-10-09: decided later. Possibly a short section at the end of the paper on 50 examples, enough for a side claim.

- The runs on 50 examples exist for Jev, Liquid d1 and GPT-6 Luna Decisions, and their figures are in `docs/all_runs.md`.
- From 5 to 199 MetaTool tools, accuracy falls from 0.86 to 0.73 on Jev, from 0.80 to 0.71 on Liquid d1 and from 0.82 to 0.66 on GPT-6 Luna Decisions. Overconfidence goes from +0.05 to +0.07 on Jev, from +0.09 to +0.05 on Liquid d1 and from +0.08 to +0.17 on GPT-6 Luna Decisions.
- On every example the two list-length runs would cost about $29.39 for the three models: $8.57 on Jev, $5.06 on Liquid d1 and $15.76 on GPT-6 Luna Decisions.

## Before the runs can start

1. Rushab raises `JEV_CALL_LIMIT`. It is 5,000 since 2026-10-09 and 2,019 calls are saved. The runs above need 110,857 Jev calls.
2. Vercel AI Gateway credit. Rushab added $25 on 2026-10-08, and the runs of 2026-10-09 used about $0.72. The runs above need about $15.16 for the two gateway models.
3. HotpotQA in the repository: a pinned download, a converter to the common format with its test, and four runs. The four are the list of 10 passages, the list without the supporting passage that has the highest probability, the list without both supporting passages, and a yes/no question per passage.
4. The figures of `docs/all_runs.md` in the repository. They come from a script that is not in the repository and has no test: the three differences between correct options and distractors, the probabilities by position, overconfidence and ECE.

## Not decided

- The venue. Rushab's goal is two workshop papers by the end of October 2026. A paper in Findings is submitted to a main track through ACL Rolling Review. Its dates were not checked.
- Whether the paper reports a way to avoid the three behaviours, such as a yes/no question per option, an average over several orders of a list, or NOTA in every list. None has been tested beyond one question.
- Related work is not read. To read: SATA-Bench (Xu et al., 2025, arXiv 2506.00643), which tests LLMs on questions with several correct answers, and the work on the order of options in multiple-choice questions for LLMs. Tam et al. (2025) is read, and its figures are in `docs/papers/README.md`.
- Whether the instructions of the HotpotQA runs stay as in the one question above.
