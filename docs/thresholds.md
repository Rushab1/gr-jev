# Choices selected by a probability threshold

![The measures against the threshold](thresholds.png)

| Dataset | Model | Form | Examples | Measure | t = 0.1 | t = 0.25 | t = 0.5 | Best value (t) |
|---|---|---|---|---|---:|---:|---:|---:|
| MetaTool | Jev | list | 497 | Exact set accuracy | 0.35 | 0.15 | 0.00 | 0.57 (0.02) |
| MetaTool | Jev | list | 497 | Precision | 0.92 | 0.95 | 0.98 |  |
| MetaTool | Jev | list | 497 | Recall | 0.70 | 0.57 | 0.48 |  |
| MetaTool | Jev | list | 497 | Recall of the other correct choices | 0.40 | 0.16 | 0.00 |  |
| MetaTool | Jev | list | 497 | F1 | 0.79 | 0.72 | 0.65 | 0.87 (0.02) |
| MetaTool | Jev | yes/no | 497 | Exact set accuracy | 0.18 | 0.29 | 0.28 | 0.31 (0.35) |
| MetaTool | Jev | yes/no | 497 | Precision | 0.58 | 0.68 | 0.73 |  |
| MetaTool | Jev | yes/no | 497 | Recall | 0.96 | 0.90 | 0.73 |  |
| MetaTool | Jev | yes/no | 497 | Recall of the other correct choices | 0.92 | 0.80 | 0.53 |  |
| MetaTool | Jev | yes/no | 497 | F1 | 0.72 | 0.78 | 0.73 | 0.78 (0.25) |
| MetaTool | Liquid d1 | list | 497 | Exact set accuracy | 0.44 | 0.27 | 0.00 | 0.46 (0.06) |
| MetaTool | Liquid d1 | list | 497 | Precision | 0.83 | 0.88 | 0.92 |  |
| MetaTool | Liquid d1 | list | 497 | Recall | 0.78 | 0.62 | 0.42 |  |
| MetaTool | Liquid d1 | list | 497 | Recall of the other correct choices | 0.57 | 0.27 | 0.00 |  |
| MetaTool | Liquid d1 | list | 497 | F1 | 0.80 | 0.73 | 0.58 | 0.83 (0.05) |
| MetaTool | Liquid d1 | yes/no | 497 | Exact set accuracy | 0.22 | 0.30 | 0.36 | 0.38 (0.60) |
| MetaTool | Liquid d1 | yes/no | 497 | Precision | 0.59 | 0.68 | 0.74 |  |
| MetaTool | Liquid d1 | yes/no | 497 | Recall | 0.96 | 0.91 | 0.85 |  |
| MetaTool | Liquid d1 | yes/no | 497 | Recall of the other correct choices | 0.93 | 0.82 | 0.71 |  |
| MetaTool | Liquid d1 | yes/no | 497 | F1 | 0.74 | 0.78 | 0.79 | 0.79 (0.47) |
| MetaTool | GPT-6 Luna Decisions | list | 497 | Exact set accuracy | 0.29 | 0.15 | 0.00 | 0.34 (0.05) |
| MetaTool | GPT-6 Luna Decisions | list | 497 | Precision | 0.77 | 0.80 | 0.83 |  |
| MetaTool | GPT-6 Luna Decisions | list | 497 | Recall | 0.69 | 0.54 | 0.37 |  |
| MetaTool | GPT-6 Luna Decisions | list | 497 | Recall of the other correct choices | 0.40 | 0.17 | 0.00 |  |
| MetaTool | GPT-6 Luna Decisions | list | 497 | F1 | 0.73 | 0.64 | 0.51 | 0.75 (0.05) |
| MetaTool | GPT-6 Luna Decisions | yes/no | 497 | Exact set accuracy | 0.24 | 0.23 | 0.24 | 0.24 (0.10) |
| MetaTool | GPT-6 Luna Decisions | yes/no | 497 | Precision | 0.68 | 0.72 | 0.75 |  |
| MetaTool | GPT-6 Luna Decisions | yes/no | 497 | Recall | 0.74 | 0.70 | 0.66 |  |
| MetaTool | GPT-6 Luna Decisions | yes/no | 497 | Recall of the other correct choices | 0.56 | 0.49 | 0.44 |  |
| MetaTool | GPT-6 Luna Decisions | yes/no | 497 | F1 | 0.71 | 0.71 | 0.70 | 0.71 (0.12) |
| HotpotQA | Jev | list | 498 | Exact set accuracy | 0.55 | 0.34 | 0.00 | 0.63 (0.04) |
| HotpotQA | Jev | list | 498 | Precision | 0.93 | 0.95 | 0.97 |  |
| HotpotQA | Jev | list | 498 | Recall | 0.80 | 0.66 | 0.47 |  |
| HotpotQA | Jev | list | 498 | Recall of the other correct choices | 0.60 | 0.34 | 0.00 |  |
| HotpotQA | Jev | list | 498 | F1 | 0.86 | 0.78 | 0.64 | 0.87 (0.05) |
| HotpotQA | Jev | yes/no | 498 | Exact set accuracy | 0.28 | 0.24 | 0.10 | 0.32 (0.18) |
| HotpotQA | Jev | yes/no | 498 | Precision | 0.51 | 0.65 | 0.75 |  |
| HotpotQA | Jev | yes/no | 498 | Recall | 0.89 | 0.66 | 0.40 |  |
| HotpotQA | Jev | yes/no | 498 | Recall of the other correct choices | 0.79 | 0.41 | 0.12 |  |
| HotpotQA | Jev | yes/no | 498 | F1 | 0.64 | 0.66 | 0.52 | 0.68 (0.16) |
| HotpotQA | Liquid d1 | list | 498 | Exact set accuracy | 0.57 | 0.35 | 0.00 | 0.64 (0.03) |
| HotpotQA | Liquid d1 | list | 498 | Precision | 0.91 | 0.96 | 0.97 |  |
| HotpotQA | Liquid d1 | list | 498 | Recall | 0.81 | 0.67 | 0.46 |  |
| HotpotQA | Liquid d1 | list | 498 | Recall of the other correct choices | 0.63 | 0.36 | 0.00 |  |
| HotpotQA | Liquid d1 | list | 498 | F1 | 0.86 | 0.79 | 0.62 | 0.88 (0.04) |
| HotpotQA | Liquid d1 | yes/no | 498 | Exact set accuracy | 0.26 | 0.18 | 0.08 | 0.28 (0.06) |
| HotpotQA | Liquid d1 | yes/no | 498 | Precision | 0.60 | 0.71 | 0.75 |  |
| HotpotQA | Liquid d1 | yes/no | 498 | Recall | 0.72 | 0.54 | 0.38 |  |
| HotpotQA | Liquid d1 | yes/no | 498 | Recall of the other correct choices | 0.51 | 0.28 | 0.12 |  |
| HotpotQA | Liquid d1 | yes/no | 498 | F1 | 0.65 | 0.61 | 0.50 | 0.66 (0.07) |
| HotpotQA | GPT-6 Luna Decisions | list | 494 | Exact set accuracy | 0.51 | 0.31 | 0.00 | 0.52 (0.08) |
| HotpotQA | GPT-6 Luna Decisions | list | 494 | Precision | 0.89 | 0.94 | 0.96 |  |
| HotpotQA | GPT-6 Luna Decisions | list | 494 | Recall | 0.79 | 0.64 | 0.43 |  |
| HotpotQA | GPT-6 Luna Decisions | list | 494 | Recall of the other correct choices | 0.59 | 0.31 | 0.00 |  |
| HotpotQA | GPT-6 Luna Decisions | list | 494 | F1 | 0.84 | 0.76 | 0.60 | 0.84 (0.07) |
| HotpotQA | GPT-6 Luna Decisions | yes/no | 494 | Exact set accuracy | 0.27 | 0.23 | 0.16 | 0.29 (0.06) |
| HotpotQA | GPT-6 Luna Decisions | yes/no | 494 | Precision | 0.61 | 0.69 | 0.74 |  |
| HotpotQA | GPT-6 Luna Decisions | yes/no | 494 | Recall | 0.73 | 0.62 | 0.51 |  |
| HotpotQA | GPT-6 Luna Decisions | yes/no | 494 | Recall of the other correct choices | 0.53 | 0.38 | 0.25 |  |
| HotpotQA | GPT-6 Luna Decisions | yes/no | 494 | F1 | 0.67 | 0.65 | 0.60 | 0.67 (0.12) |
| ECtHR | Jev | list | 192 | Exact set accuracy | 0.45 | 0.27 | 0.00 | 0.52 (0.04) |
| ECtHR | Jev | list | 192 | Precision | 0.89 | 0.94 | 0.95 |  |
| ECtHR | Jev | list | 192 | Recall | 0.75 | 0.57 | 0.38 |  |
| ECtHR | Jev | list | 192 | Recall of the other correct choices | 0.56 | 0.26 | 0.00 |  |
| ECtHR | Jev | list | 192 | F1 | 0.81 | 0.71 | 0.55 | 0.87 (0.03) |
| ECtHR | Jev | yes/no | 192 | Exact set accuracy | 0.09 | 0.32 | 0.42 | 0.44 (0.53) |
| ECtHR | Jev | yes/no | 192 | Precision | 0.39 | 0.63 | 0.80 |  |
| ECtHR | Jev | yes/no | 192 | Recall | 1.00 | 0.97 | 0.85 |  |
| ECtHR | Jev | yes/no | 192 | Recall of the other correct choices | 1.00 | 0.96 | 0.76 |  |
| ECtHR | Jev | yes/no | 192 | F1 | 0.56 | 0.76 | 0.82 | 0.83 (0.45) |
| ECtHR | Liquid d1 | list | 192 | Exact set accuracy | 0.38 | 0.20 | 0.00 | 0.48 (0.02) |
| ECtHR | Liquid d1 | list | 192 | Precision | 0.89 | 0.93 | 0.98 |  |
| ECtHR | Liquid d1 | list | 192 | Recall | 0.69 | 0.54 | 0.39 |  |
| ECtHR | Liquid d1 | list | 192 | Recall of the other correct choices | 0.45 | 0.20 | 0.00 |  |
| ECtHR | Liquid d1 | list | 192 | F1 | 0.78 | 0.69 | 0.56 | 0.85 (0.01) |
| ECtHR | Liquid d1 | yes/no | 192 | Exact set accuracy | 0.24 | 0.42 | 0.49 | 0.54 (0.63) |
| ECtHR | Liquid d1 | yes/no | 192 | Precision | 0.57 | 0.72 | 0.81 |  |
| ECtHR | Liquid d1 | yes/no | 192 | Recall | 0.99 | 0.97 | 0.94 |  |
| ECtHR | Liquid d1 | yes/no | 192 | Recall of the other correct choices | 0.99 | 0.95 | 0.89 |  |
| ECtHR | Liquid d1 | yes/no | 192 | F1 | 0.72 | 0.83 | 0.87 | 0.87 (0.57) |
| ECtHR | GPT-6 Luna Decisions | list | 160 | Exact set accuracy | 0.38 | 0.14 | 0.00 | 0.54 (0.04) |
| ECtHR | GPT-6 Luna Decisions | list | 160 | Precision | 0.91 | 0.93 | 0.98 |  |
| ECtHR | GPT-6 Luna Decisions | list | 160 | Recall | 0.70 | 0.51 | 0.39 |  |
| ECtHR | GPT-6 Luna Decisions | list | 160 | Recall of the other correct choices | 0.47 | 0.15 | 0.00 |  |
| ECtHR | GPT-6 Luna Decisions | list | 160 | F1 | 0.79 | 0.66 | 0.56 | 0.85 (0.04) |
| ECtHR | GPT-6 Luna Decisions | yes/no | 160 | Exact set accuracy | 0.32 | 0.38 | 0.38 | 0.38 (0.31) |
| ECtHR | GPT-6 Luna Decisions | yes/no | 160 | Precision | 0.71 | 0.77 | 0.91 |  |
| ECtHR | GPT-6 Luna Decisions | yes/no | 160 | Recall | 0.87 | 0.82 | 0.68 |  |
| ECtHR | GPT-6 Luna Decisions | yes/no | 160 | Recall of the other correct choices | 0.77 | 0.70 | 0.48 |  |
| ECtHR | GPT-6 Luna Decisions | yes/no | 160 | F1 | 0.78 | 0.80 | 0.78 | 0.80 (0.18) |
