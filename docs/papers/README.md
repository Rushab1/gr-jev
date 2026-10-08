# Papers

PDFs of the papers this study builds on. A file is named `<first author><year>_<short title>.pdf` and is committed unchanged. Every paper has a section here with its source, its licence and the figures that `docs/plan.md` or `docs/dashboard.html` quote from it.

## Tam et al. (2025)

Zhi Rui Tam, Cheng-Kuang Wu, Chieh-Yen Lin and Yun-Nung Chen. 2025. None of the Above, Less of the Right Parallel Patterns in Human and LLM Performance on Multi-Choice Questions Answering. In Findings of the Association for Computational Linguistics: ACL 2025, pages 20112 to 20134, Vienna, Austria. Association for Computational Linguistics. DOI 10.18653/v1/2025.findings-acl.1031.

- File: `tam2025_none_of_the_above.pdf`, 23 pages, 429,413 bytes, SHA-256 `862e7b7af89acbcd7952b7fa6fe08adbd7daf29bf0e487ed241f0be05a7efebb`.
- Source: https://aclanthology.org/2025.findings-acl.1031.pdf, downloaded on 2026-10-08.
- Licence: Creative Commons Attribution 4.0 International. The page https://aclanthology.org/2025.findings-acl.1031/ states this licence for material published in or after 2016.

Claude Code read the figures below from the text of the PDF on 2026-10-08.

### Method

- The paper evaluates 28 LLMs on the test split of MMLU, which has 14,042 questions in 57 subjects. 19 LLMs have open weights and 9 have closed weights, and the sizes run from 1.5B to 671B parameters. The prompt is zero-shot chain-of-thought with greedy decoding (appendix E).
- Standard setting: the 4 choices of the question. NA-as-answer: the correct choice is replaced by "None of the above" at its position. NA-as-distractor: one of the 3 distractors, drawn with a fixed seed, is replaced by "None of the above" at its position. The position of "None of the above" is not varied.
- The paper uses the questions that it labels NA-applicable and leaves out the subject moral_scenarios. GPT-4o labels the questions with a 5-shot prompt, and a sample per subject is checked by hand. The share of NA-applicable questions is 0.731 in the STEM subjects, 0.570 in the humanities, 0.553 in the category "Other" and 0.496 in the social sciences, and Figure 4 marks an average of 0.60 over the 56 subjects.
- The paper does not state the number of NA-applicable questions, and it gives no link to the labels.

### Accuracy of the 28 LLMs

Table 8 of the paper, in appendix C:

| Setting | Mean of the 28 LLMs | Highest | Lowest |
|---|---|---|---|
| Standard, named "Baseline" in the table | 0.738 | 0.934, gemini-2.0-flash-exp | 0.250, DeepSeek-R1-Distill-Qwen-1.5B |
| NA-as-answer | 0.350 | 0.657, DeepSeek-V3 | 0.083, Mistral-7B-Instruct-v0.3 |
| NA-as-distractor | 0.674 | 0.862, gemini-2.0-flash-exp | 0.168, Mistral-7B-Instruct-v0.3 |

- The means of the 28 rows, computed again from the table, are 0.7376, 0.3499 and 0.6742.
- The abstract gives the fall from the standard setting to NA-as-answer as "30-50%". In Table 8 the fall is between 0.30 and 0.50 for 20 of the 28 LLMs, below 0.30 for 6 and above 0.50 for 2. It is smallest for DeepSeek-R1-Distill-Qwen-1.5B, from 0.250 to 0.088, and largest for claude-3-haiku-20240307, from 0.802 to 0.206.

### The figures 63.2% and 28.5%

The conclusion gives a fall "from approximately 63.2% under standard conditions down to 28.5%" and names no model. Table 5 holds 0.632 and 0.285 in its column "Baseline", which the caption defines as LLaMA 3 8B Instruct fine-tuned on questions without "None of the above". The two figures are the accuracy of one fine-tuned model in the fine-tuning experiment of section 5.6. They are not a mean of the 28 LLMs. The row Meta-Llama-3-8B-Instruct of Table 8 has 0.696 and 0.312.

### Confidence

Section 5.4 measures confidence for one LLM, gpt-4o-mini, as the token probability of the selected letter. With "None of the above" as the correct answer the confidence changes by -0.03 on average over the subjects, and with "None of the above" as a distractor by -0.00 (Figure 7). The text contains neither "expected calibration error" nor "ECE".

### Other experiments

- Table 3 compares 4 wordings of the choice on 3 LLMs. With "None of the above" the accuracy is 0.323 for LLaMA 8B Instruct, 0.317 for Gemini-1.5-flash and 0.476 for gpt-4o-mini. With "Answer not found" it is 0.134, 0.224 and 0.376.
- Section 5.5 repeats the question on intent classification: 6 LLMs assign a query to one of the 77 classes of Bank-77 or to an added class "other" (Table 4).
- Section 5.6 fine-tunes LLaMA 3 8B Instruct with LoRA. The accuracy in NA-as-answer is 0.285 for the baseline, 0.495 after supervised fine-tuning and 0.577 after Direct Preference Optimization (Table 5).
- Section 6 names Kadavath et al. (2022) as the first work that replaced the correct choice by "None of the above" in all MMLU questions.

### Figures that do not agree

- Section 5.1 gives 90.1% as the accuracy of Gemini 1.5 Pro in the standard setting. Table 8 gives 0.899.
- Section 5.6 says that supervised fine-tuning raises the accuracy in NA-as-answer "from 28.5% to 52.3%". Table 5 has 0.495 in the row "NA as Answer" and 0.523 in the row "NA - Average".
- Section 3.2 gives the agreement between the GPT-4o labels and the human labels on 200 questions as "72.4% (Cohen's k=0.82)". Cohen's kappa is never above the share of labels that agree.
- Section 3.1 counts 352 questions in 46 subjects that already have "None of the above" among their 4 choices, and does not state the search. In `data/mmlu/processed/test.jsonl`, 157 questions in 23 subjects have a choice that contains "none of the above", and 242 questions in 33 subjects have a choice that contains the word "none".

### Use in this study

The section "MMLU" of `docs/plan.md` records the run on Jev with the correct choice replaced by "None of the above", and how that run differs from NA-as-answer.
