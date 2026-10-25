# When Multiple Choices Are Correct: Asymmetric Probability Allocation in Jev and Other Decision Models

[![arXiv](https://img.shields.io/badge/arXiv-2610.29217-b31b1b.svg)](https://arxiv.org/abs/2610.29217)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Code and model instructions for the paper **[When Multiple Choices Are Correct: Asymmetric Probability Allocation in Jev and Other Decision Models](https://arxiv.org/abs/2610.29217)** by Rushab Munot (arXiv:2610.29217, cs.AI and cs.CL, 2026).

The paper studies how decision models distribute probability over a list of choices when several choices are correct. It evaluates three decision models, Jev (TypeSafe AI, `jev-1.13.0`), Liquid d1 (`liquid/d1`) and GPT-6 Luna Decisions (`openai/gpt-6-luna-decisions`, OpenAI Decisions API). The datasets are MetaTool (tool selection), HotpotQA (supporting passages) and ECtHR (violated articles). ChaosNLI gives the votes of 100 annotators for comparison.

- **Paper:** [arxiv.org/abs/2610.29217](https://arxiv.org/abs/2610.29217) ([PDF](https://arxiv.org/pdf/2610.29217), [HTML](https://arxiv.org/html/2610.29217))
- **Code:** this repository, version tagged [`arxiv-v1`](https://github.com/Rushab1/gr-jev/tree/arxiv-v1)

## Abstract

Decision models return normalized probability distributions over candidate choices, which downstream applications can use to select among choices. Although their providers emphasize the reliability of these probabilities, calibration on tasks with a single correct choice does not establish their reliability when multiple choices are correct. We evaluate three decision models (Jev, Liquid d1, and GPT-6 Luna Decisions) on three diverse datasets (MetaTool, HotpotQA, and ECtHR) to study probability allocation and thresholding. Even when models rank every correct choice above every distractor, in 28% to 50% of those lists, at least one correct choice receives a probability below the uniform probability of 1/n, where n is the number of choices. We also present each model with five identical copies of a correct choice and observe probability disparities, with mean gaps ranging from 17 to 79 percentage points. We further show how these allocation disparities affect the recovery of multiple correct choices under probability thresholding. Decision-model probabilities can rank correct choices, but a probability threshold does not identify the set of correct choices.

## What the repository measures

- The probability gap between the highest and the lowest correct choice in lists with several correct choices (multi-label selection).
- The probabilities of five identical copies of one correct choice, sent in their five cyclic permutations.
- Exact set accuracy of a probability threshold, and the threshold that maximizes it.
- Calibration (ECE) of the confidence on lists with one correct choice, and of yes/no questions per choice.
- Position bias, lists with no correct choice, "none of the above" choices, and refusals.
- The model probabilities against the vote shares of the ChaosNLI annotators (Jensen-Shannon distance, entropy, ECE).

## Setup

```
uv sync
source .venv/bin/activate
cp .env.example .env   # add TYPESAFE_API_KEY and VERCEL_GATEWAY_API_KEY
python scripts/data/download_data.py metatool
python scripts/data/process_data.py metatool
python scripts/run/run_experiment.py position --dry-run
```

Python 3.13. Jev is called through TypeSafe's API. Liquid d1 and GPT-6 Luna Decisions are called through Vercel AI Gateway. `scripts/paper/` writes the tables and figures of the paper from `results/`. `AGENTS.md` describes every script, the layout and the code standard. The saved model responses are not in the repository.

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

decision models, Jev, TypeSafe AI, System One, Liquid d1, GPT-6 Luna Decisions, OpenAI Decisions API, probability allocation, calibration, expected calibration error, probability threshold, multiple correct answers, multi-label selection, tool selection, tool retrieval, MetaTool, HotpotQA, ECtHR, ChaosNLI, position bias, identical choices, annotator disagreement

## License

MIT. See [LICENSE](LICENSE). Jev output may not be used to train models under TypeSafe's customer agreement.
