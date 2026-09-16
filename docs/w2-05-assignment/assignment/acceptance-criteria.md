
src/promptlab/prompts/
Commit:

docs/day5-run.jsonl
docs/day5-scores.jsonl
reports/comparison.md
docs/model-decision.md
Preserve docs/model-facts.md if it already exists.

Acceptance Criteria
1. All metrics are deterministic and call no model.
2. scorer_version is incremented.
3. Scoring changes are committed separately from prompt changes.
4. select_current_version exists and tests/test_rules_contract.py passes.
5. No prompt asks the model to decide document currency.
6. run.py with no filters runs all three tasks against both configured models.
7. The full run covers 12 cases per task per model.
8. day5-run.jsonl and day5-scores.jsonl share one run_id.
9. Every score record joins to call evidence.
10. Every retry, repair, failure, and successful attempt is recorded.
11. Both models use provider="ollama" and configured model_id.
12. No model identifier literal appears outside configuration.
13. No direct Ollama handling appears outside the adapter layer.
14. No cloud credential is required or committed.
15. Every comparison row names its prompt version.
16. Prompt-transfer rows are labeled honestly.
17. Quality uses counts with denominators, not percentages.
18. Median and maximum latency are reported with observation counts.
19. No provider-dollar comparison is invented; local provider cost is $0.00.
20. Input/output token usage and repair rates are reported.
21. Extraction keeps missed and invented/unsupported evidence separate.
22. The limits section names the 12-case sample and rejects production-scale claims.
23. Recommendations name task, model, prompt version, and reopening condition.
24. The triage human boundary passes under both Mistral and Qwen.
25. Every measured prompt version remains preserved and unedited.
26. pytest, ruff check, and mypy are clean.