# ChaosNLI: probabilities against the split of 100 annotators

Runs of 2026-10-21 on every example of ChaosNLI, on Jev, Liquid d1 and GPT-6 Luna Decisions. Not in the paper yet.

## Question

The paper reports that the models put most of the probability on one choice when several choices are correct. A reviewer can answer that the reference of 1/n is arbitrary. ChaosNLI (Nie, Zhou and Bansal, 2020) gives a measured reference that is not 1/n. Each example has the share of 100 annotators who chose each label.

The share of a label measures how much the annotators disagree. It is not the probability that the label is correct.

## Data

| Test file | Examples | Choices | Query |
|---|---:|---:|---|
| `snli` | 1,514 | entailment, neutral, contradiction | A premise and a hypothesis |
| `mnli_m` | 1,599 | entailment, neutral, contradiction | A premise and a hypothesis |
| `alphanli` | 1,532 | 2 hypotheses, each named by its text | Two observations |

The files come from the Hugging Face dataset `earino/chaosnli` at revision `bf8d66a`, a copy of the ChaosNLI release. The Dropbox link of the ChaosNLI repository returned a web page on 2026-10-21. ChaosNLI is licensed CC BY-NC 4.0. `python scripts/data/download_data.py chaosnli` and `python scripts/data/process_data.py chaosnli chaosnli_alpha` build the datasets `chaosnli` and `chaosnli_alpha`.

## Requests

The `own` experiment sends the labels of every example in every cyclic order, all orders in one request. SNLI and MNLI have 3 orders and alphaNLI has 2.

- SNLI and MNLI. The state is "Premise: ..." and "Hypothesis: ..." on two lines. The instruction is "Choose how the hypothesis relates to the situation or event in the premise." The choices are entailment ("The hypothesis is definitely correct about the situation or event in the premise."), neutral ("... might be correct ...") and contradiction ("... is definitely incorrect ..."). The wording follows the prompt that MNLI gave the annotators who wrote the hypotheses (Williams et al., 2018, Figure 1).
- alphaNLI. The state is "Observation 1: ..." and "Observation 2: ..." on two lines. The instruction is "Choose the more plausible hypothesis of what happened between the two observations." It follows Bhagavatula et al. (2020), who asked people to "choose the more plausible hypothesis".

The runs made 4,645 Jev calls and 4,645 calls to each gateway model. No model refused or rejected a list. The input tokens cost $0.35 for the three models. The results folders are `results/chaosnli_own*/2026-10-21_01` and `results/chaosnli_alpha_own*/2026-10-21_01`.

Before these runs, a script outside the repository sent 100 MNLI examples in one order with other descriptions of the labels. On those 100 examples the models' gap on split examples differs from the figures below by at most 0.06, and the shares by at most 7 percentage points.

## Measures

- An example is split when two labels each have at least 30% of the annotators, and clear otherwise. Claude Code chose the 30%, and the edges of 0.1 and 0.9 below.
- The gap of an example is the share or probability of the label most annotators chose minus that of the second label. For the model, the size of the gap is reported, and the share of answers in which it is negative, where the model favours the label fewer annotators chose.
- The distance is the total variation distance from the annotators' shares: half the sum of the absolute differences over the labels. It is 0 for the same split and 1 for no overlap.
- Each answer to one order counts once.

## Results

On the 1,487 split examples, the annotators split the two labels 55% to 61% against 38% to 39% on average. The models put a gap of 0.62 to 0.80 between the same two labels, against 0.17 to 0.21 for the annotators. In 37% to 51% of the answers the larger probability goes to the label fewer annotators chose. On these examples, the models are further from the annotators than 1/n on each label in 8 of the 9 pairs of model and test file. Jev on SNLI is at 0.30 against 0.31.

On the clear examples, the models are as far from the annotators as a model that puts all the probability on the majority label, within 0.07.

A change in the order of the labels moves the probability of a label by 0.02 to 0.11 on average.

`python scripts/report/annotator_split.py` prints the tables below from the results folders. The code is in `src/grjev/annotators.py`, and the runs are `ANNOTATOR_RUNS` in `src/grjev/constants.py`.

### snli

| Measure | Jev | Liquid d1 | GPT-6 Luna Decisions |
|---|---:|---:|---:|
| Examples | 1,514 | 1,514 | 1,514 |
| Answers, one per order of the labels | 4,542 | 4,542 | 4,542 |
| Labels below 0.1 or above 0.9, annotators | 45% | 45% | 45% |
| Labels below 0.1, model | 53% | 53% | 58% |
| Labels above 0.9, model | 20% | 20% | 25% |
| Labels that 30% to 70% of annotators chose, once per order | 3,177 | 3,177 | 3,177 |
| Of those, below 0.1 or above 0.9, model | 37% | 46% | 68% |
| Split examples, two labels with at least 30% each | 477 | 477 | 477 |
| Split examples, annotators' gap between the two labels | 0.19 | 0.19 | 0.19 |
| Split examples, model's gap between the two labels | 0.62 | 0.68 | 0.80 |
| Split examples, answers that favour the label fewer annotators chose | 37% | 40% | 42% |
| Split examples, distance of the model from the annotators | 0.30 | 0.34 | 0.40 |
| Split examples, distance of 1/n on each label | 0.31 | 0.31 | 0.31 |
| Split examples, distance of all on the majority label | 0.42 | 0.42 | 0.42 |
| Clear examples, distance of the model | 0.15 | 0.16 | 0.22 |
| Clear examples, distance of all on the majority label | 0.16 | 0.16 | 0.16 |
| Mean change of a label's probability over the orders | 0.02 | 0.04 | 0.07 |

### mnli_m

| Measure | Jev | Liquid d1 | GPT-6 Luna Decisions |
|---|---:|---:|---:|
| Examples | 1,599 | 1,599 | 1,599 |
| Answers, one per order of the labels | 4,797 | 4,797 | 4,797 |
| Labels below 0.1 or above 0.9, annotators | 28% | 28% | 28% |
| Labels below 0.1, model | 46% | 44% | 50% |
| Labels above 0.9, model | 13% | 12% | 17% |
| Labels that 30% to 70% of annotators chose, once per order | 5,562 | 5,562 | 5,562 |
| Of those, below 0.1 or above 0.9, model | 43% | 42% | 56% |
| Split examples, two labels with at least 30% each | 795 | 795 | 795 |
| Split examples, annotators' gap between the two labels | 0.17 | 0.17 | 0.17 |
| Split examples, model's gap between the two labels | 0.64 | 0.63 | 0.72 |
| Split examples, answers that favour the label fewer annotators chose | 51% | 49% | 48% |
| Split examples, distance of the model from the annotators | 0.36 | 0.37 | 0.40 |
| Split examples, distance of 1/n on each label | 0.27 | 0.27 | 0.27 |
| Split examples, distance of all on the majority label | 0.45 | 0.45 | 0.45 |
| Clear examples, distance of the model | 0.27 | 0.29 | 0.32 |
| Clear examples, distance of all on the majority label | 0.25 | 0.25 | 0.25 |
| Mean change of a label's probability over the orders | 0.03 | 0.07 | 0.11 |

### alphanli

| Measure | Jev | Liquid d1 | GPT-6 Luna Decisions |
|---|---:|---:|---:|
| Examples | 1,532 | 1,532 | 1,532 |
| Answers, one per order of the labels | 3,064 | 3,064 | 3,064 |
| Labels below 0.1 or above 0.9, annotators | 60% | 60% | 60% |
| Labels below 0.1, model | 34% | 35% | 36% |
| Labels above 0.9, model | 34% | 35% | 36% |
| Labels that 30% to 70% of annotators chose, once per order | 860 | 860 | 860 |
| Of those, below 0.1 or above 0.9, model | 37% | 39% | 46% |
| Split examples, two labels with at least 30% each | 215 | 215 | 215 |
| Split examples, annotators' gap between the two labels | 0.21 | 0.21 | 0.21 |
| Split examples, model's gap between the two labels | 0.63 | 0.64 | 0.68 |
| Split examples, answers that favour the label fewer annotators chose | 43% | 44% | 42% |
| Split examples, distance of the model from the annotators | 0.30 | 0.31 | 0.33 |
| Split examples, distance of 1/n on each label | 0.11 | 0.11 | 0.11 |
| Split examples, distance of all on the majority label | 0.39 | 0.39 | 0.39 |
| Clear examples, distance of the model | 0.11 | 0.12 | 0.13 |
| Clear examples, distance of all on the majority label | 0.07 | 0.07 | 0.07 |
| Mean change of a label's probability over the orders | 0.04 | 0.07 | 0.11 |

## Limits

- The share of the annotators is not the probability that a label is correct. A reviewer can say that a model asked for one label has no duty to reproduce the disagreement. The providers describe the outputs as probabilities, and the paper's introduction states that.
- SNLI, MNLI and alphaNLI are public since 2015, 2018 and 2020, and ChaosNLI since 2020. They may be in the training data of the three models.
- Every SNLI and MNLI example of ChaosNLI has the source `agree_3`: 3 of its 5 original annotators chose the majority label. Split examples are therefore more frequent than in SNLI or MNLI as a whole.
- One wording of the labels per dataset, and one request per example.
