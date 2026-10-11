# Paper plan: the probability distribution of decision models

Last updated 2026-10-10. Rushab, 2026-10-10: "the whole reason this paper is important is because we want to study the probability distribution of decision models". The paper is not about tool selection. This file holds the five properties of the distribution that the paper tests, the datasets, the results so far, the runs on every example with their cost, and what is not built or not decided. The history of the runs is in `docs/plan.md`. The figures of every run and model are in `docs/all_runs.md`.

## Terms

- **Decision model**: a model that takes a query and typed questions and returns probabilities and no text. The four tested are Jev (TypeSafe AI), Liquid d1 (Liquid AI), GPT-6 Luna Decisions (OpenAI) and Laya (Convai Innovations).
- **Option**: one entry of the list sent with a query: a tool on MetaTool, a passage on HotpotQA, a choice on MMLU, an article of the Convention on ECtHR.
- **Correct option** and **distractor**: an option that the dataset labels as correct for the query, and an option that it does not.
- **List question**: one question of type `choice` with a list of options. The answer holds one probability per option, and the probabilities sum to 1. The distribution studied here is this answer.
- **Yes/no question**: one question of type `noul` about one option. The answer is one probability of "yes". Questions do not share a total.
- **Prediction**: the option that the model selects. **Confidence**: the highest probability of an answer.
- **Duplicate options**: 5 copies of one correct option whose names differ only by extra spaces.
- **NOTA**: an option that says no other option is correct: "None" on MetaTool, "None of the above" on MMLU.
- **Refusal**: an answer of type `refusal` with no probabilities. Only GPT-6 Luna Decisions returns it.

## The five properties

A dataset is used where its labels say which options are correct. Order is the one property with a required answer, and it leads the paper. The other four describe how the distribution behaves and whether a user can read a probability as a score of how suitable an option is. A list question must give probabilities that sum to 1, and an uneven split between two correct options, or a high probability when no option is correct, is not a malfunction by that fact.

| | Property | Question | Reference | Result so far |
|---|---|---|---|---|
| 1 | Order | Does the distribution change when the same options are in another order? | Required: an identical option has the same probability at every position. 0.20 for each of 5 duplicate options | With 5 duplicates the favoured position gets 0.22 to 0.81 on average. Jev favours the last position, and Liquid d1, GPT-6 Luna Decisions and Laya the first. With one correct option among distractors the position makes no difference |
| 2 | Allocation | How is the probability divided among options that are all correct? | For comparison: 0.50 each for 2 correct options. A model may prefer one of them | The highest correct option gets 0.80 to 0.85 and the lowest 0.11 to 0.14, on MetaTool queries that need 2 tools |
| 3 | Abstention | What does the distribution do when no option is correct? | For comparison: equal probabilities, a refusal, or NOTA when it is offered | Mean confidence 0.56 to 0.84 on 5 random distractors. GPT-6 Luna Decisions refuses 125 and 207 of 250 lists. Jev and Liquid d1 never refuse |
| 4 | Calibration | Does confidence match accuracy at each level of confidence, when one option is correct? | Required: accuracy equal to confidence within each of 10 bins of confidence. Measured as ECE, with the 10 bins reported. Refusals are counted apart | Mean confidence is 0.04 to 0.07 above accuracy on MMLU with 4 choices. The bins are not reported yet |
| 5 | Dependence on the list | Does the probability of an option depend on the option, or on the other options of the list? | For comparison: the probability of the same option when a correct option is removed from the list, and as a yes/no question about that option alone with the same wording | On one HotpotQA question a supporting passage has 0.00 to 0.05 in the list of 10, 0.90 to 1.00 when the other supporting passage is removed, and 0.57 to 1.00 as a yes/no question |

Notes on the properties:

- Rushab, 2026-10-09: "A choice answer sums to 1, so of course the second correct option gets little" is wrong. A sum of 1 means the correct options share the probability. It does not make one of them take 0.85 or more.
- Two reviews of this plan, on 2026-10-09 and by Codex on 2026-10-10, are followed. An observation is kept apart from a failure. The labels must match the question that is asked. Calibration is measured by level of confidence. A pilot comes before the runs on every example. The script that computes the figures is checked first.
- The yes/no questions are a control of property 5 and not a property. Rushab, 2026-10-10: the recommended setup, with yes/no questions on 500 HotpotQA questions and on the ECtHR test cases, one wording.
- A second run of the same requests on Jev gives the same prediction in 1,158 of 1,182 answers on StableToolBench and in 1,526 of 1,550 on MetaTool.
- The instruction "Choose all of them with equal probability." does not give an equal split. On StableToolBench Jev's highest correct API has 0.72 and its lowest 0.13.

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

Rushab, 2026-10-10: 3 or 4 datasets from different domains. A dataset is in the list when its labels say which options are correct, for the list structures below.

| Domain | Dataset | Lists with one correct option | Lists with several correct options | Lists with no correct option | In the repository |
|---|---|---|---|---|---|
| Tool selection | MetaTool | 2,795 queries in `similar_tools` and `scenario` | 497 queries in `multi_tool`, which need 2 tools | 995 queries in `reliability`, where "None" is correct | Yes |
| Passage selection | HotpotQA, distractor setting, validation split | None | All 7,405 questions: 2 supporting passages, among 10 passages in 7,345 of them | Built by removing both supporting passages | No. Downloaded outside the repository on 2026-10-09 from `hotpotqa/hotpot_qa`, revision `1908d6af` |
| Knowledge questions | MMLU | 13,096 questions of `test_standalone`, 4 choices | Not possible: 1 correct choice | Built with random distractors, or with the 3 other choices and NOTA as in Tam et al. (2025) | Yes |
| Legal classification | ECtHR, Task A of LexGLUE, test split | 655 cases with 1 violated article | 192 cases with 2 to 4 violated articles | 153 cases with no violated article | No. Two files downloaded outside the repository on 2026-10-10 from `coastalcph/lex_glue`, revision `c23fdff1` |

- ECtHR: a case is the facts of a judgment of the European Court of Human Rights, and its labels are the articles of the Convention that the Court found violated, among 10: Articles 2, 3, 5, 6, 8, 9, 10, 11 and 14, and Article 1 of Protocol 1. The facts have 1,926 words on average, a median of 1,412 and at most 15,919. The licence of LexGLUE is CC BY 4.0. No ECtHR case has been sent to a model.
- HotpotQA: Rushab chose it on 2026-10-09 for lists with several correct options. Its licence is CC BY-SA 4.0. OpenAlex lists 553 papers of 2026 that name it in the title or abstract.
- MetaTool is kept and StableToolBench is left out. Rushab asked on 2026-10-10 for one of the two. The `multi_tool` queries of MetaTool need both tools, and 44% of the StableToolBench queries name a relevant API. The figures of the StableToolBench runs on 50 examples stay in this file and in `docs/all_runs.md`. With StableToolBench the plan loses its lists with 3 to 6 correct options. ECtHR has 46 cases with 3 or 4.
- Looked at and left out. MultiRC: Rushab, "these are very basic pre-llm tests". BFCL: a correct answer is a function call with arguments, and 752 of its 1,124 lists with no fitting function hold 1 function or none. NFCorpus: 11,758 of its 12,334 relevance labels have the lower of two scores, and its queries have a median of 2 words. The Jigsaw toxic comments, GoEmotions, CLINC150, MedQA, Banking77 and FiQA were named and not downloaded.

## Results so far

Each run has 50 examples unless stated. Jev was asked from 2026-10-05 to 2026-10-08, and the gateway models on 2026-10-09 with the same requests. GPT-6 Luna Decisions refused some lists, and its figures are over the lists it answered.

### Property 1, order: 5 duplicate options

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

### Property 2, allocation: several correct options

Mean probability of the highest and of the lowest correct option. Two correct options at 0.50 each give a difference of 0:

| Run | Jev | Liquid d1 | GPT-6 Luna Decisions |
|---|---|---|---|
| MetaTool `multi_tool`, 2 correct tools, "Choose one of them." | 0.85 and 0.12 | 0.80 and 0.14 | 0.80 and 0.11 |
| StableToolBench, 2 to 6 correct APIs, "Choose all of them." | 0.75 and 0.12 | 0.73 and 0.11 | 0.69 and 0.11 |

On MetaTool `multi_tool` with "Choose one of them.", the highest correct tool minus the lowest is 0.95 or more in 130, 85 and 106 of 450 answers on Jev, Liquid d1 and GPT-6 Luna Decisions.

### Property 3, abstention: no correct option

| Run | Jev | Liquid d1 | GPT-6 Luna Decisions |
|---|---|---|---|
| MetaTool, 5 random distractors, mean confidence | 0.81 | 0.80 | 0.84 on 125 lists, 125 refused |
| MMLU, 5 random distractors, mean confidence | 0.56 | 0.59 | 0.73 on 43 lists, 207 refused |
| MetaTool, 4 random distractors and NOTA, share of the answers that are NOTA | 0.93 | 0.95 | 0.90 |
| MMLU, 4 random distractors and NOTA, share of the answers that are NOTA | 1.00 | 1.00 | 1.00 |
| MMLU, the 3 distractors of the question and NOTA, share of the answers that are NOTA | 0.79 | 0.86 | 0.59 |

### Property 4, calibration: MMLU with the 4 choices of the question

| | Jev | Liquid d1 | GPT-6 Luna Decisions |
|---|---|---|---|
| Accuracy | 0.91 | 0.84 | 0.81 |
| Mean confidence | 0.96 | 0.88 | 0.88 |
| Overconfidence: mean confidence minus accuracy | +0.05 | +0.04 | +0.07 |

### Property 5, dependence on the list: one HotpotQA question

Question `5a8d5fc6554299585d9e37c6`: "What's the name of the fantasy film starring Sarah Bolger, featuring a New England family who discover magical creatures around their estate?" Its supporting passages are "The Spiderwick Chronicles (film)" and "Sarah Bolger". The first holds the answer. It was asked on 2026-10-09 as a list and as one yes/no question per passage, each with two wordings:

- "is needed": the list instruction "Choose every passage in the list that is needed to answer the question.", and the yes/no question "Is this passage needed to answer the question?"
- "may support": the list instruction "Choose every passage in the list that may support the answer to the question.", and the yes/no question "May this passage support the answer to the question?"

| Passage | Asked as | Wording | Jev | Liquid d1 | GPT-6 Luna Decisions |
|---|---|---|---|---|---|
| The Spiderwick Chronicles (film) | List of 10 | is needed | 0.99 | 0.96 | 0.97 |
| The Spiderwick Chronicles (film) | List of 10 | may support | 1.00 | 0.95 | 0.99 |
| The Spiderwick Chronicles (film) | Yes/no | is needed | 0.92 | 0.73 | 0.98 |
| The Spiderwick Chronicles (film) | Yes/no | may support | 0.98 | 0.99 | 1.00 |
| Sarah Bolger | List of 10 | is needed | 0.01 | 0.04 | 0.02 |
| Sarah Bolger | List of 10 | may support | 0.00 | 0.05 | 0.01 |
| Sarah Bolger | Yes/no | is needed | 0.64 | 0.15 | 0.89 |
| Sarah Bolger | Yes/no | may support | 0.76 | 0.84 | 1.00 |

The two lists with passages removed, with the wording "is needed":

| List | Passage | Jev | Liquid d1 | GPT-6 Luna Decisions |
|---|---|---|---|---|
| 9 passages, "The Spiderwick Chronicles (film)" removed | Sarah Bolger | 1.00 | 0.98 | 0.90 |
| The 8 distractors | The distractor with the highest probability | 0.31 | 0.73 | 0.36 |

- The highest yes/no probability of a distractor is 0.04, 0.03 and 0.00 with "may support", and 0.07, 0.09 and 0.59 with "is needed". With "is needed" GPT-6 Luna Decisions gives 0.59, 0.45 and 0.41 to three distractors.
- "Sarah Bolger" does not hold the answer, and 0.15 from Liquid d1 for "is needed" as a yes/no question fits that.
- Three wordings were asked the same day, as a list and as a yes/no question: "may support", "supports" and "definitely supports" the answer to the question. The probability of "Sarah Bolger":

| Asked as | Wording | Jev | Liquid d1 | GPT-6 Luna Decisions |
|---|---|---|---|---|
| List of 10 | may support | 0.00 | 0.05 | 0.01 |
| List of 10 | supports | 0.00 | 0.04 | 0.01 |
| List of 10 | definitely supports | 0.00 | 0.03 | 0.02 |
| Yes/no | may support | 0.76 | 0.84 | 1.00 |
| Yes/no | supports | 0.66 | 0.68 | 0.99 |
| Yes/no | definitely supports | 0.57 | 0.73 | 0.77 |

- With these three wordings "The Spiderwick Chronicles (film)" has 0.95 to 1.00 in all 6 cases, and no distractor has more than 0.04.
- This is one question. It is not a rate.

## Runs on every example

Rushab, 2026-10-10: the recommended setup. MMLU is run on 1,000 questions, a seeded sample of the 13,096. The yes/no questions are a control on 500 HotpotQA questions and on the ECtHR test cases. The full HotpotQA list is asked with three wordings. The other three datasets are run on every example, and the three HotpotQA runs with 5 cyclic permutations on 1,000 questions.

One request holds every list of one example. A HotpotQA question is one request for its full list in 3 wordings, its 2 lists without one supporting passage, and its list without both.

| Property | Run | Dataset | Requests per model |
|---|---|---|---|
| 1 Order | 5 duplicates of a correct option, 5 cyclic permutations | MetaTool | 3,292 |
| 1 Order | 5 duplicates of a correct option, 5 cyclic permutations | MMLU, 1,000 questions | 1,000 |
| 1 Order | 5 duplicates of a supporting passage, 5 cyclic permutations | HotpotQA, 1,000 questions | 1,000 |
| 1 Order | 5 duplicates of a violated article, 5 cyclic permutations | ECtHR, 847 cases | 847 |
| 1 Order | 5 paraphrased options, 5 cyclic permutations | MetaTool, 1,767 examples | 1,767 |
| 1 Order and 4 Calibration | One correct option, placed at every position | MetaTool `similar_tools`, `scenario`, `reliability` | 3,790 |
| 1 Order and 4 Calibration | One correct option, 4 cyclic permutations | MMLU, 1,000 questions | 1,000 |
| 2 Allocation | The list of the example, "Choose one of them." and "Choose both." | MetaTool `multi_tool` | 994 |
| 2 Allocation, 3 Abstention and 5 Dependence | The list, the list without each correct option, and the list without every correct option, in one request | MetaTool `multi_tool` | 497 |
| 2 Allocation, 3 Abstention and 5 Dependence | The same, with the full list in 3 wordings | HotpotQA | 7,405 |
| 2 Allocation, 3 Abstention and 5 Dependence | The same | ECtHR, 847 cases | 847 |
| 2 Allocation, 3 Abstention and 4 Calibration | The list of 10 articles, 10 cyclic permutations | ECtHR | 1,000 |
| 3 Abstention | 5 random distractors, 5 cyclic permutations | MetaTool | 3,292 |
| 3 Abstention | 5 random distractors, 5 cyclic permutations | MMLU, 1,000 questions | 1,000 |
| 3 Abstention | 5 random distractors, 5 cyclic permutations | HotpotQA, 1,000 questions | 1,000 |
| 3 Abstention | The distractors of the example, no correct option | MetaTool `similar_tools` | 995 |
| 3 Abstention | The distractors of the example, no correct option | MMLU, 1,000 questions | 1,000 |
| 3 Abstention | 4 random distractors and NOTA, 5 cyclic permutations | MetaTool `similar_tools` | 995 |
| 3 Abstention | 4 random distractors and NOTA, 5 cyclic permutations | MMLU, 1,000 questions | 1,000 |
| 3 Abstention | 4 random distractors and NOTA, 5 cyclic permutations | HotpotQA, 1,000 questions | 1,000 |
| 3 Abstention | The distractors of the example and NOTA | MMLU, 1,000 questions | 1,000 |
| 3 Abstention | The distractors of the example and NOTA | HotpotQA | 7,405 |
| 3 Abstention | The list of 10 articles and NOTA | ECtHR | 1,000 |
| 5 Dependence, control | A yes/no question per passage, wording "supports" | HotpotQA, 500 questions | 500 |
| 5 Dependence, control | A yes/no question per article | ECtHR | 1,000 |
| | **Total** | | **44,626** |

| Dataset | Requests per model | Cost, three models |
|---|---|---|
| MetaTool | 15,622 | $4.00 |
| MMLU | 6,000 | $0.70 |
| HotpotQA | 18,310 | $11.17 |
| ECtHR | 4,694 | $2.38 |
| **Total** | **44,626** | **about $18.25** |

- The cost is an estimate: about $4.40 on Jev, $3.40 on Liquid d1 and $10.40 on GPT-6 Luna Decisions. The MetaTool and MMLU figures use the input tokens measured in the runs on 50 examples. The HotpotQA figure is scaled from one question, and the ECtHR figure from the 1,926 words of an average case. The pilot replaces both.
- HotpotQA wordings. The three list instructions are "Choose every passage in the list that may support the answer to the question.", the same with "supports", and the same with "definitely supports". The labels of HotpotQA mark sentences that support the answer, and a passage with such a sentence can support an answer without being needed for it. The three wordings are reported separately. The lists without a supporting passage and the yes/no questions use "supports".
- ECtHR wording. The labels are the articles that the Court found violated, not every article that the facts could concern. The instruction asks for the Court's finding, and a case with no label is a case in which the Court found no violation of the 10 articles. Its wording is fixed in the pilot.
- On ECtHR one run with the list of 10 articles covers three properties: its cases have one, several or no violated article.
- The MetaTool run with the distractors of the example and NOTA is left out. The label "None" of that run is not verified.
- Paraphrased options exist for 38 MetaTool tools only.
- HotpotQA questions of type `bridge` (5,918) and of type `comparison` (1,487) are reported separately. A comparison question needs both supporting passages.
- MMLU has no list with several correct options, and HotpotQA none with one correct option.
- A refusal of GPT-6 Luna Decisions is counted and reported for every run, apart from its answers.

### List length

Rushab, 2026-10-09: decided later. Possibly a short section at the end of the paper on 50 examples, enough for a side claim.

- The runs on 50 examples exist for Jev, Liquid d1 and GPT-6 Luna Decisions, and their figures are in `docs/all_runs.md`.
- From 5 to 199 MetaTool tools, accuracy falls from 0.86 to 0.73 on Jev, from 0.80 to 0.71 on Liquid d1 and from 0.82 to 0.66 on GPT-6 Luna Decisions. Overconfidence goes from +0.05 to +0.07 on Jev, from +0.09 to +0.05 on Liquid d1 and from +0.08 to +0.17 on GPT-6 Luna Decisions.
- On every example the MetaTool list-length run would cost about $25.62 for the three models: $7.50 on Jev, $4.45 on Liquid d1 and $13.66 on GPT-6 Luna Decisions.

## Steps

1. The figures in the repository. Done on 2026-10-10. `src/grjev/distribution.py` computes the figures of `docs/all_runs.md` and `src/grjev/tables.py` builds its tables, with tests. `python scripts/runs_table.py all_runs --out docs/all_runs.md` rebuilds the file. The rebuilt tables are identical to those of the script outside the repository, which they replace. `scripts/results_figures.py` prints the same figures for one run.
2. HotpotQA and ECtHR in the repository: a pinned download and a converter to the common format with its test, for each.
3. The new runs in the runner, with tests: the lists without correct options, a yes/no question per option, and the distractors of the example with no correct option. The runs with duplicates, random distractors and NOTA exist and need their entries for HotpotQA and ECtHR.
4. A pilot on 50 examples per dataset and model, about 900 Jev calls. One exact request of HotpotQA and one of ECtHR are shown to Rushab before it.
5. Rushab raises `JEV_CALL_LIMIT` for the runs on every example. It is 5,000 since 2026-10-09 and 2,023 calls are saved. The runs need 44,626 Jev calls.
6. The runs on every example. Vercel AI Gateway credit: Rushab added $25 on 2026-10-08, about $24 is left, and the runs need about $14 for the two gateway models.

## Not decided

- The venue. Rushab's goal is two workshop papers by the end of October 2026. A paper in Findings is submitted to a main track through ACL Rolling Review. Its dates were not checked.
- Whether the paper reports a way to avoid the behaviours, such as a yes/no question per option, an average over several orders of a list, or NOTA in every list. None has been tested beyond one question.
- Related work is not read. To read: SATA-Bench (Xu et al., 2025, arXiv 2506.00643), which tests LLMs on questions with several correct answers, and the work on the order of options in multiple-choice questions for LLMs. Tam et al. (2025) is read, and its figures are in `docs/papers/README.md`.
- List length, under "List length" above.
