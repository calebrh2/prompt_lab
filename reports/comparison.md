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
