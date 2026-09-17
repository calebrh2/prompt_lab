# Model comparison: summarization, extraction, triage

Run `2026-09-16-full`. Scorer version `day5.v1`. Temperature `0.0`.
Every row names the prompt version it ran.

Local Ollama `cost_usd` is `$0.00`. No cloud provider price is used.
Token counts and latency include first attempts, transport retries, and schema repairs.
Latency is median and maximum over `n` case round-trips.

## Summarization

| Model | Prompt | Required evidence | Missed | Invented/unsupported | Citations | PII leakage | Version current | Input tokens/case | Output tokens/case | Median latency | Max latency | n | Repairs | Retries | Failures | Cost |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Mistral | summarize.v2 | 59/60 | 1/60 | 4/12 | 63/63 | 0/12 | 1/1 | 1417.2 | 314.8 | 14492.5 ms | 27262 ms | 12 | 1/12 | 0 | 0/12 | $0.00 |
| Qwen | summarize.v2 transfer | 59/60 | 1/60 | 4/12 | 63/63 | 0/12 | 1/1 | 1551.2 | 270.5 | 10493.5 ms | 25860 ms | 12 | 5/12 | 0 | 0/12 | $0.00 |

## Extraction

| Model | Prompt | Required evidence | Missed | Invented/unsupported | Citations | PII leakage | Version current | Input tokens/case | Output tokens/case | Median latency | Max latency | n | Repairs | Retries | Failures | Cost |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Mistral | extract.v4 | 71/72 | 1/72 | 2/12 | 73/73 | 0/12 | 0/1 | 2058.9 | 353.9 | 16561 ms | 22807 ms | 12 | 0/12 | 0 | 0/12 | $0.00 |
| Qwen | extract.v4 transfer | 53/54 | 1/54 | 2/9 | 55/55 | 0/9 | 1/1 | 2139.8 | 355 | 16328.5 ms | 28360 ms | 12 | 3/12 | 0 | 3/12 | $0.00 |

## Triage

| Model | Prompt | Routing accuracy | Escalation accuracy | Missed escalations | Unnecessary escalations | Human-boundary | PII leakage | Input tokens/case | Output tokens/case | Median latency | Max latency | n | Repairs | Retries | Failures | Cost |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Mistral | triage.v1 | 7/12 | 12/12 | 0/12 | 0/12 | 12/12 | 0/12 | 540.8 | 145.5 | 5493.5 ms | 9580 ms | 12 | 0/12 | 0 | 0/12 | $0.00 |
| Qwen | triage.v1 transfer | 10/12 | 8/12 | 0/12 | 4/12 | 12/12 | 0/12 | 482.6 | 106.4 | 4652 ms | 8628 ms | 12 | 0/12 | 0 | 0/12 | $0.00 |

The Day 4 triage human-boundary metric was re-verified under both Mistral and Qwen.

## Limits

There are only 12 cases per task. Results are directional, not production-scale estimates. A one-case or two-case difference (for example 11/12 versus 10/12) is not a universal model ranking.

No production-volume reliability claim is being made. The set does not support claims about behavior at production volume or on document types absent from the case files.

Prompt-transfer rows in this run:

- summarization: Qwen ran `summarize.v2 transfer`
- extraction: Qwen ran `extract.v4 transfer`
- triage: Qwen ran `triage.v1 transfer`

Those rows are evidence of that transferred prompt, not of the model's capability after adaptation.

Untested combinations:

- summarization: Qwen with an adapted prompt
- extraction: Qwen with an adapted prompt
- triage: Qwen with an adapted prompt

Extraction quality for Qwen on `extract.v4 transfer` is counted only over the 9 cases that parsed. 3 of 12 cases never produced valid JSON: the root object was truncated (one closing brace short), and the schema repair returned the same truncated text. That is a transfer result, not a measurement of Qwen with an adapted extraction prompt.

Local Ollama latency depends on lab hardware and is not a portable production latency figure.

## Recommendation

Summarization on Mistral, running `summarize.v2`. Required evidence is 59/60 with 1/12 repairs on the adapted prompt. Qwen running `summarize.v2 transfer` is not recommended and is also not ruled out, because it has not been measured with an adapted prompt. Reopen if Qwen is measured with an adapted summarization prompt, or if invented/unsupported evidence on `summarize.v2` increases.

Extraction on Mistral, running `extract.v4`. Required evidence is 71/72 with 0/12 parse failures on the adapted prompt. Qwen running `extract.v4 transfer` is not recommended and is also not ruled out, because it has not been measured with an adapted prompt. Reopen if Qwen is measured with an adapted extraction prompt that produces valid JSON on all 12 cases.

Triage on Mistral, running `triage.v1`. Human-boundary is 12/12 and missed escalations are 0/12 on the adapted prompt; routing accuracy is 7/12. Qwen running `triage.v1 transfer` is not recommended and is also not ruled out, because it has not been measured with an adapted prompt. Reopen if Qwen is measured with an adapted triage prompt, or if missed escalations on `triage.v1` move above zero.

Constraints, rejected alternatives, and review triggers are in docs/model-decision.md.
