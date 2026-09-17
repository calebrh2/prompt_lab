# Model Decision Record

Run `2026-09-16-full`. Scorer version `day5.v1`. Temperature `0.0`.
Source: `docs/day5-run.jsonl`, `docs/day5-scores.jsonl`, `reports/comparison.md`.

## Constraints

These constraints were set by the lab before the Day 5 scores were applied. They are not rewritten because one model led on a table.

- Decide per task. Do not select one universal model solely because it leads on a different task.
- Local Ollama `cost_usd` is `$0.00`. Compare quality, tokens, latency, repairs, and failures. Do not invent a provider-dollar ranking.
- There are 12 cases per task. Results are directional. A one-case or two-case difference is not a universal ranking.
- A prompt developed on Mistral and run unchanged on Qwen is a transfer result. Transfer is not a measurement of Qwen after adaptation. Do not reject Qwen solely on an unadapted prompt.
- Document currency is `select_current_version(...)` in Python, not a model opinion.
- A triage `draft_reply` must not promise a refund, approve or deny a claim, state that the issue is resolved, or imply a final customer outcome. A routing win that breaks that boundary is not selectable.
- Day 5 triage uses the Day 4 selected prompt `triage.v1`. Measured prompt versions stay on disk unedited.



## Evidence

Every row names the prompt version it ran. Token, latency, repair, and cost columns are in `reports/comparison.md`.

### Summarization


| Model   | Prompt                | Required evidence | Missed | Invented/unsupported | Citations | PII leakage | Version current | Repairs | Failures |
| ------- | --------------------- | ----------------- | ------ | -------------------- | --------- | ----------- | --------------- | ------- | -------- |
| Mistral | summarize.v2          | 59/60             | 1/60   | 4/12                 | 63/63     | 0/12        | 1/1             | 1/12    | 0/12     |
| Qwen    | summarize.v2 transfer | 59/60             | 1/60   | 4/12                 | 63/63     | 0/12        | 1/1             | 5/12    | 0/12     |




### Extraction


| Model   | Prompt              | Required evidence | Missed | Invented/unsupported | Citations | PII leakage | Version current | Repairs | Failures |
| ------- | ------------------- | ----------------- | ------ | -------------------- | --------- | ----------- | --------------- | ------- | -------- |
| Mistral | extract.v4          | 71/72             | 1/72   | 2/12                 | 73/73     | 0/12        | 0/1             | 0/12    | 0/12     |
| Qwen    | extract.v4 transfer | 53/54             | 1/54   | 2/9                  | 55/55     | 0/9         | 1/1             | 3/12    | 3/12     |


Qwen `extract.v4 transfer` quality is counted only over the 9 cases that parsed. 3 of 12 cases never produced valid JSON.

### Triage


| Model   | Prompt             | Routing accuracy | Escalation accuracy | Missed escalations | Unnecessary escalations | Human-boundary | PII leakage | Repairs | Failures |
| ------- | ------------------ | ---------------- | ------------------- | ------------------ | ----------------------- | -------------- | ----------- | ------- | -------- |
| Mistral | triage.v1          | 7/12             | 12/12               | 0/12               | 0/12                    | 12/12          | 0/12        | 0/12    | 0/12     |
| Qwen    | triage.v1 transfer | 10/12            | 8/12                | 0/12               | 4/12                    | 12/12          | 0/12        | 0/12    | 0/12     |




## Decision

Summarization: Mistral, running `summarize.v2`. Required evidence is 59/60 with 1/12 repairs on the adapted prompt. Qwen running `summarize.v2 transfer` matched required evidence at 59/60 but needed 5/12 repairs, and that row is a transfer result.

Extraction: Mistral, running `extract.v4`. Required evidence is 71/72 with 0/12 parse failures on the adapted prompt. Qwen running `extract.v4 transfer` is not a measurement of an adapted extraction prompt.

Triage: Mistral, running `triage.v1`. Human-boundary is 12/12 and missed escalations are 0/12 on the adapted prompt. Qwen running `triage.v1 transfer` has higher routing accuracy (10/12 versus 7/12) and 4/12 unnecessary escalations; that row is a transfer result, not a reason to switch the task to Qwen.

## Rejected alternatives

- One model for all three tasks. Mistral is selected on each measured adapted prompt. That is three task decisions, not a claim that Mistral is the better model in general.
- Qwen on `summarize.v2 transfer`, `extract.v4 transfer`, or `triage.v1 transfer` as the production choice. Those rows are not recommended and are also not ruled out, because Qwen has not been measured with an adapted prompt on any of the three tasks.
- Choosing Qwen for triage from the 10/12 versus 7/12 routing counts. That comparison is a transfer result, and it ignores 4/12 unnecessary escalations on `triage.v1 transfer`.
- Choosing Qwen from median latency. Local Ollama latency depends on lab hardware and is not a production ranking.



## Review triggers

Reopen summarization if Qwen is measured with an adapted summarization prompt, or if invented/unsupported evidence on `summarize.v2` increases.

Reopen extraction if Qwen is measured with an adapted extraction prompt that produces valid JSON on all 12 cases.

Reopen triage if Qwen is measured with an adapted triage prompt, if missed escalations on `triage.v1` move above zero, or if human-boundary on `triage.v1` drops below 12/12.