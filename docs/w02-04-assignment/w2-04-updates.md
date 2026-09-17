# w02-04 progress log

Working tracker of files created or changed while implementing Day 4. This log is not assignment authority.

| File | What was built | Instruction / AC |
| --- | --- | --- |
| `.cursor/agents/w02-04-acceptance-criteria.md` | Binary gate that checks every instruction and all 32 acceptance criteria. | Plan graders; AC 1–32 |
| `.cursor/agents/w02-04-ac-schema-contract.md` | Cluster grader for schema and task-vocabulary criteria. | Plan graders; AC 1–5 |
| `.cursor/agents/w02-04-ac-prompt-rendering.md` | Cluster grader for `render_user` and prompt-registry location. | Plan graders; AC 6–10 |
| `.cursor/agents/w02-04-ac-triage-prompts.md` | Cluster grader for triage.v1 / triage.v2 prompt files. | Plan graders; AC 11–14 |
| `.cursor/agents/w02-04-ac-run-protocol.md` | Cluster grader for the controlled 12-case dual-prompt run. | Plan graders; AC 15–20 |
| `.cursor/agents/w02-04-ac-scoring.md` | Cluster grader for deterministic scoring and human-boundary outputs. | Plan graders; AC 21–27 |
| `.cursor/agents/w02-04-ac-evidence-and-tooling.md` | Cluster grader for committed evidence, counts, cost, secrets, and tooling. | Plan graders; AC 28–32 |
| `docs/w02-04-assignment/w2-04-updates.md` | Progress table updated as Day 4 files land. | Plan progress log |
| `src/promptlab/schemas.py` | Added `TriageOutputWithAnalysis` with only an `analysis` field on the existing `TriageOutput`. | Inst 1–2; AC 1–3 |
| `src/promptlab/prompts.py` | Implemented `render_user` with missing-variable errors, marker escaping, and no `str.format()`. | Inst 3; AC 6–9 |
| `src/promptlab/config.py` | Added `BOUNDARY_LANGUAGE_PATTERNS` for deterministic human-boundary scoring. | Inst 7; AC 25–26 |
| `src/promptlab/scoring.py` | Deterministic queue, escalation, missed/unnecessary, and human-boundary metrics on existing `ScoreRecord`. | Inst 7; AC 21–25, 27 |
| `tests/test_scoring.py` | Unit tests for gold-field scoring, separate escalation failures, and boundary language. | Inst 7; AC 21–25, 27 |
| `src/prompts/triage.v1.md` | Layered v1 triage prompt that validates against `TriageOutput` and does not request `analysis`. | Inst 4; AC 10–12 |
| `src/prompts/triage.v2.md` | v1 plus a short `analysis` field for `TriageOutputWithAnalysis`. | Inst 5; AC 10, 13 |
| `src/promptlab/day4.py` | Controlled v1/v2 run through `complete_structured` and the prompt registry. | Inst 3, 6, 8–10; AC 4, 9, 15–20 |
| `tests/test_day4.py` | Protocol tests for 12 cases, one model, temperature 0.0, shared `run_id`, and prompt versions. | Inst 6, 8–10; AC 15–19 |
| `docs/day4-run.jsonl` | Call records for the shared `run_id` covering both prompt versions. | Inst 8–10; AC 15–20, 28 |
| `docs/day4-scores.jsonl` | Existing `ScoreRecord` lines joined by run, case, model, and prompt version. | Inst 7, 10; AC 21–25, 27–28 |
| `docs/day4-notes.md` | Count-with-denominator comparison of v1 vs v2, including tokens, latency, and $0.00 cost. | Inst 11–12; AC 28–30 |
