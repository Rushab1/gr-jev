# When Multiple Choices Are Correct: Asymmetric Probability Allocation in Jev and Other Decision Models

[![arXiv](https://img.shields.io/badge/arXiv-2610.29217-b31b1b.svg)](https://arxiv.org/abs/2610.29217)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Paper** [arxiv.org/abs/2610.29217](https://arxiv.org/abs/2610.29217) ([PDF](https://arxiv.org/pdf/2610.29217), [HTML](https://arxiv.org/html/2610.29217)) by Rushab Munot, 2026. The paper version is tagged [`arxiv-v1`](https://github.com/Rushab1/gr-jev/tree/arxiv-v1).

## What goes wrong

Decision models such as Jev return one probability per choice. TypeSafe and OpenAI suggest a threshold to pick several choices. TypeSafe's documentation sends a support ticket to a second team when that team gets more than 0.25.

### Two passages are needed. Jev keeps one.

The list has 5 short invented passages. Two of them give the birth dates, and both are needed.

Query: "who is older, Jane or John?" Instruction: "Choose every passage in the list that supports the answer to the question."

Picking the passages needed to answer a question shows a critical failure mode of Jev. The bolded values mark the passages with John's and Jane's birth dates. Both passages are necessary and equally relevant. Jev selects only one of them. This example shows that whether decision models work is highly task dependent.

| Position | Name | Passage | Jev 1.13.0 |
|---|---|---|---|
| 1 | John's workshop | John opened a furniture workshop with two friends. | 0.01 |
| 2 | Jane's choir | Jane leads a choir that performs twice a year. | 0.00 |
| 3 | The town fair | John and Jane both helped to organize the town fair last summer. | 0.02 |
| 4 | John | John was born on December 12, 1976. He works as a carpenter. | **0.89** |
| 5 | Jane | Jane was born on January 13, 1990. She teaches music at a school. | **0.08** |

*Ran with Jev (`jev-1.13.0`) on October 25, 2026.*

### Five identical choices get different probabilities.

We send TypeSafe's own support ticket with five copies of "returns", the team that TypeSafe's documented answer puts first. Only a random name tells the copies apart.

Query: "Shoes arrived two weeks late and in the wrong size. Also I see two charges of $120 on my card. What are you going to do about this?" Instruction: "Which team should handle this?"

| Position | Name (random ID) | Choice | Jev 1.13.0 |
|---|---|---|---|
| 1 | `6tt9` | returns: Exchanges, wrong or damaged items | **0.09** |
| 2 | `snge` | returns: Exchanges, wrong or damaged items | 0.12 |
| 3 | `bo7t` | returns: Exchanges, wrong or damaged items | 0.17 |
| 4 | `3y9q` | returns: Exchanges, wrong or damaged items | **0.33** |
| 5 | `hu30` | returns: Exchanges, wrong or damaged items | 0.29 |

The example from TypeSafe's own documentation, where we send five identical copies of the top choice, shows dramatic differences in probabilities.

*Ran with Jev (`jev-1.13.0`) on October 25, 2026.*

## What the paper finds

![Mean probability of the highest and the lowest correct choice, for each model and dataset](docs/figures/allocation_gap.png)

- In lists with several correct choices, the highest correct choice gets 55 to 72 percentage points more than the lowest, on average.
- Five identical copies of a correct choice end up 17 to 79 percentage points apart on average.
- The best single threshold for a dataset picks exactly the correct choices in 34% to 64% of the examples.
- On ChaosNLI, 100 annotators voted on each example. When the two labels with the most votes are within 0.1 of each other, the models' probabilities on them are 0.58 to 0.77 apart on average.

## Models and datasets

| Models | Datasets |
|---|---|
| Jev `jev-1.13.0` (TypeSafe AI API) | MetaTool, tool selection with 2 correct tools |
| Liquid d1 `liquid/d1` (Vercel AI Gateway) | HotpotQA, supporting passages of a question |
| GPT-6 Luna Decisions `openai/gpt-6-luna-decisions` (Vercel AI Gateway) | ECtHR, articles violated in a case |
| | ChaosNLI, votes of 100 annotators on SNLI, MNLI and αNLI |

## Citation

```bibtex
@misc{munot2026multiple,
  title         = {When Multiple Choices Are Correct: Asymmetric Probability Allocation in Jev and Other Decision Models},
  author        = {Munot, Rushab},
  year          = {2026},
  eprint        = {2610.29217},
  archivePrefix = {arXiv},
  primaryClass  = {cs.AI},
  url           = {https://arxiv.org/abs/2610.29217}
}
```

## Keywords

decision models, Jev, Jev calibration, Jev probabilities, Jev threshold, TypeSafe AI, System One, Liquid d1, GPT-6 Luna Decisions, OpenAI Decisions API, probability allocation, calibration, expected calibration error, probability threshold, multiple correct answers, multi-label selection, tool selection for agents, tool retrieval, MetaTool, HotpotQA, ECtHR, ChaosNLI, position bias, identical choices, annotator disagreement

## License

MIT. See [LICENSE](LICENSE). TypeSafe's customer agreement does not allow training a model on Jev output.

## Setup

```
uv sync
source .venv/bin/activate
cp .env.example .env   # add TYPESAFE_API_KEY and VERCEL_GATEWAY_API_KEY
python scripts/data/download_data.py metatool
python scripts/data/process_data.py metatool
python scripts/run/run_experiment.py copied --dry-run
```

Python 3.13. `--dry-run` prints the number of model calls without sending any request. `scripts/paper/` writes the tables and figures of the paper from `results/`. `AGENTS.md` describes every script and the layout. The saved model responses are not in the repository.
