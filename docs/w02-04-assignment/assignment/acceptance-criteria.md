Acceptance Criteria
1. The existing TriageOutput remains the base Day 4 triage schema.
2. No competing TriageDecision model is introduced.
3. TriageOutputWithAnalysis extends the existing contract with only the additional analysis field.
4. Day 4 requests use task="triage".
5. The Day 2 task vocabulary remains triage, summarization, and extraction.
6. render_user(...) raises MissingPromptVariableError when a required value is absent.
7. render_user(...) prevents untrusted customer text from closing its marker early.
8. Literal JSON braces in a prompt do not break rendering.
9. Python prompt-registry code lives in src/promptlab/prompts.py.
10. Markdown prompt files live in src/prompts/.
11. triage.v1.md validates against TriageOutput.
12. triage.v1.md does not request the additional analysis field.
13. triage.v2.md validates against TriageOutputWithAnalysis.
14. triage.v1.md is not edited after v1 results are recorded.
15. Both prompt versions run all 12 triage cases.
16. Both prompt versions use the same configured Ollama model.
17. Both prompt versions use temperature 0.0.
18. Both prompt versions run under one shared run_id.
19. All model calls continue through the existing adapter and structured-completion layers.
20. No direct Ollama HTTP handling is added outside the adapter layer.
21. Queue scoring compares TriageOutput.queue with the gold expected queue.
22. Escalation scoring compares TriageOutput.escalation_required with the gold expected escalation value.
23. human_review_required is not substituted for the gold escalation field.
24. Missed escalations and unnecessary escalations are reported separately.
25. Human-boundary scoring is deterministic and calls no model.
26. No committed draft_reply states approval, denial, refund, reimbursement, or final resolution.
27. Day 4 uses the repository's existing record contracts rather than defining a conflicting ScoreRecord.
28. docs/day4-run.jsonl, docs/day4-scores.jsonl, and docs/day4-notes.md are committed.
29. Results are reported as counts with denominators rather than percentages.
30. Local provider/API cost is reported as $0.00; token and latency overhead are still measured.
31. No cloud credential, key, or populated .env file appears in the diff.
32. pytest, ruff, and mypy pass.
