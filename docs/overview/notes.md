# Lab notes (Days 1–4)

Shared results across the four local Ollama runs. Per-day source files remain the evidence of record.

| Day | Task | Cases | Model | Prompt | `run_id` | Provider/API cost |
| --- | --- | --- | --- | --- | --- | ---: |
| 1 | extraction | E12, E07, E11 | `mistral:7b` | `baseline` v0 | `e4d221f5-1fda-4d69-bb2c-106060134f60` | $0.00 |
| 2 | summarization | S01–S12 | `mistral:7b` and `qwen3:8b` | `baseline` v0 | `4feb6c0f-074a-4fec-a3cf-3cb4f880e74a` | $0.00 |
| 3 | summarization + extraction | S01–S12, E01–E12 | `mistral:7b` | `summarize` v1, `extract` v2 | `b1017e9e-8ed4-4ef2-a31d-8f7f21bb5a8f` | $0.00 |
| 4 | triage | T01–T12 | `mistral:7b` | `triage` v1 and v2 | `339e7675-a30d-40eb-af1b-919d9c45e24c` | $0.00 |

All runs used temperature `0.0` and `max_output_tokens` `512`. Counts below use denominators rather than percentages.

---

## Day 1 — instrument a local extraction call

Source: `docs/day1-run.jsonl`, `docs/day1-observations.md`.

Three extraction cases from `cases/extraction.jsonl`: shortest (E12), middle (E07), and longest (E11).

| Case | Document | Input tokens | Output tokens | Latency (ms) | Stop | Error |
| --- | --- | ---: | ---: | ---: | --- | --- |
| E12 | Training agenda (not a policy) | 228 | 50 | 2233 | stop | none |
| E07 | Seasonal Business Review Policy | 243 | 102 | 4464 | stop | none |
| E11 | Family-Owned Company Review Policy | 274 | 107 | 4713 | stop | none |

E12 is the shortest input and the shortest completion. E11 is the longest input and produced more than twice as many output tokens as E12 (107 vs 50). Input size rose about 20 percent; latency more than doubled (2233 ms → 4713 ms). A short document underestimates model workload: latency scales with both prompt length and the longer completions that fuller documents tend to elicit.

---

## Day 2 — Mistral vs Qwen on summarization

Source: `docs/day2-run.jsonl`, `docs/day2-comparison.md`.

Same baseline prompt and the same 12 rows in `cases/summarization.jsonl`. Workload is tokens and wall time, not dollars.

| Metric | Mistral | Qwen |
| --- | ---: | ---: |
| Cases | 12 | 12 |
| Successful (`error_type` null) | 12/12 | 10/12 |
| Truncated (`stop_reason=length`) | 0/12 | 2/12 (S06, S10) |
| Input tokens (sum) | 2,787 | 2,427 |
| Output tokens (sum) | 1,142 | 4,806 |
| Latency median (ms) | 3,728 | 17,882 |
| Latency max (ms) | 8,659 | 23,995 |

Qwen used about four times as many output tokens and about five times the median latency as Mistral. The 512-token ceiling stopped two Qwen answers; Mistral finished every case under that cap.

### Per-case comparison

| Case | Document | Mistral in / out / ms | Qwen in / out / ms | Qwen error |
| --- | --- | ---: | ---: | --- |
| S01 | Card Dispute Intake Procedure v1.0 | 275 / 124 / 8659 | 239 / 365 / 19769 | none |
| S02 | Card Dispute Intake Procedure v2.0 | 259 / 124 / 5182 | 226 / 350 / 15828 | none |
| S03 | Lost Card Response Procedure | 236 / 91 / 3734 | 209 / 436 / 19448 | none |
| S04 | Merchant Documentation Procedure | 233 / 114 / 4714 | 206 / 345 / 15542 | none |
| S05 | Friday Operations Discussion (meeting notes) | 201 / 67 / 2811 | 179 / 340 / 15354 | none |
| S06 | Complaint Acknowledgement Procedure | 266 / 126 / 5457 | 232 / 512 / 23995 | TruncatedResponseError |
| S07 | Address Change Verification Procedure | 223 / 90 / 3663 | 192 / 454 / 21294 | none |
| S08 | Lending Inquiry Referral Procedure | 235 / 77 / 3175 | 202 / 379 / 17952 | none |
| S09 | Identity Review Procedure | 221 / 94 / 3813 | 194 / 388 / 17811 | none |
| S10 | Duplicate Payment Intake Procedure | 228 / 90 / 3721 | 197 / 512 / 23537 | TruncatedResponseError |
| S11 | Accessibility Complaint Procedure | 208 / 77 / 3162 | 178 / 367 / 16518 | none |
| S12 | Operations Monthly Newsletter | 202 / 68 / 2789 | 173 / 358 / 16121 | none |

---

## Day 3 — structured summarization and extraction

Source: `docs/day3-run.jsonl`, `docs/day3-notes.md`.

One model (`mistral:7b`). Summarization used shipped `summarize.v1.md` over all 12 summarization rows. Extraction used `extract.v2.md` over all 12 extraction rows. `document_status` below is the model output, not a gold-label score.

| Check | Result |
| --- | --- |
| Summarization schema repairs | 0/12 |
| Extraction schema repairs | 0/12 |
| Example leakage (extraction) | 0/12 |
| Citation failures (`status: "present"`) | 0/136 (summarization 0/63, extraction 0/73) |

All 12 summarization rows validated against `SummarizationOutput`. All 12 extraction rows validated against `PolicyExtraction`.

The most common validation error on the restored shipped prompt was S05: extra keys (`attendees`, `discussion`) forbidden by the schema, plus absent fields missing `value`. Those shape rules were added to the Day 3 system prompt; `complete_structured` unwraps fenced JSON; `summarize.v1.md` was left as shipped.

### Summarization cases

| Case | Document | Gold status | Model `document_status` | Input tokens | Output tokens | Latency (ms) | Schema |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| S01 | Card Dispute Intake Procedure v1.0 | superseded | valid | 1322 | 340 | 15884 | pass |
| S02 | Card Dispute Intake Procedure v2.0 | valid | valid | 1306 | 350 | 15753 | pass |
| S03 | Lost Card Response Procedure | valid | valid | 1283 | 327 | 14878 | pass |
| S04 | Merchant Documentation Procedure | contradictory | valid | 1280 | 270 | 13192 | pass |
| S05 | Friday Operations Discussion | unsupported | valid | 1248 | 205 | 9956 | pass |
| S06 | Complaint Acknowledgement Procedure | valid | valid | 1313 | 318 | 14529 | pass |
| S07 | Address Change Verification Procedure | valid | valid | 1270 | 313 | 14477 | pass |
| S08 | Lending Inquiry Referral Procedure | valid | valid | 1282 | 324 | 15010 | pass |
| S09 | Identity Review Procedure | contradictory | contradictory | 1268 | 279 | 13231 | pass |
| S10 | Duplicate Payment Intake Procedure | valid | valid | 1275 | 319 | 14592 | pass |
| S11 | Accessibility Complaint Procedure | valid | valid | 1255 | 299 | 13929 | pass |
| S12 | Operations Monthly Newsletter | unsupported | valid | 1249 | 204 | 9980 | pass |

### Extraction cases

| Case | Document | Gold status | Model `document_status` | Input tokens | Output tokens | Latency (ms) | Schema |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| E01 | Small Business Periodic KYC Review Policy v1.0 | superseded | valid | 2083 | 414 | 20851 | pass |
| E02 | Small Business Periodic KYC Review Policy v2.0 | valid | valid | 2072 | 378 | 17667 | pass |
| E03 | Community Merchant Review Policy | valid | valid | 2041 | 333 | 15706 | pass |
| E04 | Regional Retail Entity Review Policy | contradictory | valid | 2069 | 345 | 16412 | pass |
| E05 | Nonprofit Organization Review Policy | valid | valid | 2045 | 349 | 16497 | pass |
| E06 | High-Risk Business Review Policy | valid | valid | 2059 | 394 | 18459 | pass |
| E07 | Seasonal Business Review Policy | valid | valid | 2048 | 352 | 16552 | pass |
| E08 | Professional Practice Review Policy | valid | valid | 2039 | 370 | 17268 | pass |
| E09 | Microenterprise Review Policy | valid | valid | 2041 | 338 | 15943 | pass |
| E10 | Interstate Vendor Review Policy | contradictory | valid | 2062 | 343 | 17232 | pass |
| E11 | Family-Owned Company Review Policy | valid | valid | 2079 | 360 | 17717 | pass |
| E12 | Training agenda (not a policy) | unsupported | unsupported | 2033 | 259 | 12874 | pass |

---

## Day 4 — triage.v1 vs triage.v2

Source: `docs/day4-run.jsonl`, `docs/day4-scores.jsonl`, `docs/day4-notes.md`.

One model (`mistral:7b`). Both prompt versions ran all 12 rows in `cases/triage.jsonl` through `complete_structured` → `ModelAdapter` → `OllamaAdapter`. v1 validated against `TriageOutput`. v2 validated against `TriageOutputWithAnalysis`. v2 T07 needed one schema repair; token and latency totals for that case sum both attempts.

| Metric | triage.v1 | triage.v2 |
| --- | ---: | ---: |
| Queue correct | 7/12 | 8/12 |
| Escalation correct | 12/12 | 11/12 |
| Missed escalations | 0/12 | 1/12 |
| Unnecessary escalations | 0/12 | 0/12 |
| Human-boundary passes | 12/12 | 12/12 |
| Observations | 12 | 13 (12 primary + 1 repair on T07) |
| Output tokens (sum, attempts summed) | 1746 | 2356 |
| Median latency (ms) | 6358 | 8315 |
| Maximum latency (ms) | 11930 | 9893 (T07 case total including repair: 18449) |

Changed-queue count: **4/12** (T06, T07, T08, T09). Output-token difference (v2 − v1, attempts summed): **+610**.

v2 gained 1/12 queue correctness and lost 1/12 escalation correctness. A one-case movement on a 12-case set is not evidence that one prompt is universally better. The analysis field added output tokens on every case and added a repair on T07. That overhead did not earn a clear routing improvement here.

### Per-case routing

| Case | Gold queue | Gold esc. | v1 queue | v1 esc. | v2 queue | v2 esc. | Queue changed | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T01 | card_dispute | no | card_dispute | no | card_dispute | no | no | both correct |
| T02 | fraud_report | no | card_dispute | no | card_dispute | no | no | both miss queue |
| T03 | account_servicing | no | account_servicing | no | account_servicing | no | no | both correct |
| T04 | lending | no | lending | no | lending | no | no | both correct |
| T05 | complaint | no | complaint | no | complaint | no | no | both correct |
| T06 | escalate | yes | card_dispute | yes | escalate | yes | yes | v2 fixes queue; both escalate correctly |
| T07 | escalate | yes | lending | yes | complaint | no | yes | v2 misses queue and escalation; 1 repair |
| T08 | escalate | yes | escalate | yes | fraud_report | yes | yes | v1 queue correct; v2 queue miss |
| T09 | unsupported | no | lending | no | unsupported | no | yes | v2 fixes queue |
| T10 | account_servicing | no | account_servicing | no | account_servicing | no | no | both correct (prompt-injection source) |
| T11 | card_dispute | no | card_dispute | no | card_dispute | no | no | both correct (PII in source) |
| T12 | fraud_report | no | card_dispute | no | card_dispute | no | no | both miss queue (PII in source) |

### Per-case tokens and latency

v2 T07 output tokens and latency sum the failed first attempt (219 tokens, 9596 ms) and the repair (201 tokens, 8853 ms).

| Case | v1 out | v2 out | Δ out | v1 latency (ms) | v2 latency (ms) |
| --- | ---: | ---: | ---: | ---: | ---: |
| T01 | 162 | 196 | +34 | 11930 | 9445 |
| T02 | 117 | 164 | +47 | 5285 | 7210 |
| T03 | 139 | 182 | +43 | 6243 | 8651 |
| T04 | 123 | 151 | +28 | 5400 | 6852 |
| T05 | 153 | 168 | +15 | 6751 | 7461 |
| T06 | 185 | 210 | +25 | 8604 | 9893 |
| T07 | 188 | 420 | +232 | 8727 | 18449 |
| T08 | 168 | 193 | +25 | 7280 | 8629 |
| T09 | 119 | 180 | +61 | 5208 | 8315 |
| T10 | 148 | 169 | +21 | 6472 | 7882 |
| T11 | 124 | 166 | +42 | 5606 | 7374 |
| T12 | 120 | 157 | +37 | 5532 | 7491 |
| **Sum** | **1746** | **2356** | **+610** | | |
