# Day 4 notes

Source: `docs/day4-run.jsonl` and `docs/day4-scores.jsonl` (`run_id` `339e7675-a30d-40eb-af1b-919d9c45e24c`). One configured Ollama model (`mistral:7b`) at temperature `0.0` with `max_output_tokens` `512`. Both prompt versions ran all 12 rows in `cases/triage.jsonl` through `complete_structured` → `ModelAdapter` → `OllamaAdapter`. `triage.v1` validated against `TriageOutput`. `triage.v2` validated against `TriageOutputWithAnalysis`.

provider/API cost = $0.00

## triage.v1

- queue correct: 7/12
- escalation correct: 12/12
- missed escalations: 0
- unnecessary escalations: 0
- human-boundary passes: 12/12
- observation count: 12
- output tokens per case: T01 162, T02 117, T03 139, T04 123, T05 153, T06 185, T07 188, T08 168, T09 119, T10 148, T11 124, T12 120 (sum 1746)
- median latency: 6358 ms
- maximum latency: 11930 ms

## triage.v2

- queue correct: 8/12
- escalation correct: 11/12
- missed escalations: 1
- unnecessary escalations: 0
- human-boundary passes: 12/12
- observation count: 13 (12 primary calls plus 1 schema repair on T07)
- output tokens per case (attempts summed): T01 196, T02 164, T03 182, T04 151, T05 168, T06 210, T07 420, T08 193, T09 180, T10 169, T11 166, T12 157 (sum 2356)
- median latency: 8315 ms
- maximum latency: 9893 ms (T07 case total including repair: 18449 ms)

## Comparison

- changed-queue count: 4/12 (T06, T07, T08, T09)
- output-token difference (v2 − v1, attempts summed): +610
- per-case token difference: T01 +34, T02 +47, T03 +43, T04 +28, T05 +15, T06 +25, T07 +232, T08 +25, T09 +61, T10 +21, T11 +42, T12 +37
- latency: v2 median 8315 ms vs v1 median 6358 ms; v2 added one repair observation

v2 gained 1/12 queue correctness and lost 1/12 escalation correctness. A one-case movement on a 12-case set is not evidence that one prompt is universally better. The analysis field added output tokens on every case and added a repair on T07. That overhead did not earn a clear routing improvement here.
