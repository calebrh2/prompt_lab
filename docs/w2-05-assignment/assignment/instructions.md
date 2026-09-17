Instructions
1. Finish the Remaining Deterministic Metrics
Extend src/promptlab/scoring.py using the C5 interface from Day 4.

Implement:

Required-evidence recall

Compare fields the gold label says are recoverable with fields the model returned as present.

Report counts with denominators, for example:

required evidence found: 6/8
Do not report percentages.

Citation correctness

For each field with:

status = "present"
confirm that its section actually appears in the source document.

A citation merely being present is not enough.

Personal-data leakage

Use the supplied PII_PATTERNS from config.py to check free-text outputs for the synthetic account-number, national-ID, email, and telephone formats used by the corpus.

This scoring is deterministic. It must not call an LLM.

Increment scorer_version and commit the scoring change separately from prompt changes.

2. Implement the Deterministic Version Rule
Create or complete:

src/promptlab/rules.py
Implement:

select_current_version(extractions, as_of)
The rule decides which extracted document version is current as of a supplied date.

The architecture should be:

document
  -> LLM extracts version/effective-date evidence
  -> validated PolicyExtraction
  -> select_current_version(...)
  -> deterministic result
Do not ask Mistral or Qwen which document is current. That is a deterministic business rule and belongs in Python.

Run tests/test_rules_contract.py, including the equal-effective-date boundary case.

3. Score Version Selection Through rules.py
If version currency is part of the final score, score the result produced by select_current_version(...), not a free-text model opinion.

This keeps failures attributable to either:

bad extraction
or
bad deterministic rule
4. Build src/promptlab/run.py
Create the final evaluation runner.

It must accept:

a run identifier
optional task selection
optional model selection
With no task/model selection, one command runs:

3 tasks
x 2 models
x 12 cases
= 72 normal task/model/case evaluations
Repairs and transport retries may create additional CallRecord attempts.

All calls must follow:

run.py
  -> prompt registry
  -> complete_structured(...)
  -> ModelAdapter
  -> OllamaAdapter
  -> configured Mistral/Qwen
Do not make direct Ollama HTTP calls from run.py.

5. Keep Model Selection in Configuration
No model identifier literal should be scattered through the application.

Do not do:

model = "mistral:7b"
at call sites.

Resolve the configured model and record its model_id.

Both models use:

provider = "ollama"
and are distinguished by model_id.

6. Handle Prompt Transfer Honestly
A prompt developed while working with one model may not be equally tuned for the other.

For each task, choose one of these approaches.

Transfer test: Run the exact same prompt on the second model and label the result as a prompt-transfer result.

Do not turn that into an unsupported claim such as:

Qwen is worse at extraction.

What you measured was Qwen running that specific prompt.

Adapted prompt: If you tune the prompt for the second model, create a new prompt version. Preserve the old version and record the actual version in every result.

Every row in the final report must state the prompt version it ran.

7. Execute the Full Run
Use:

temperature = 0.0
Run all three tasks against both models under one shared run_id.

summarization: 12 Mistral + 12 Qwen
extraction:    12 Mistral + 12 Qwen
triage:        12 Mistral + 12 Qwen
Record every attempt, including:

successful first attempts
transport retries
structured-output repairs
final failures
Commit the evidence as:

docs/day5-run.jsonl
docs/day5-scores.jsonl
Both files must share the same run_id.

8. Make Run Records and Score Records Join
Every score record must be traceable to its model-call evidence.

At minimum, the join must use:

run_id
case_id
task
model_id
prompt_id
prompt_version
You should be able to take a score record and find the exact call record that produced it without guessing.

9. Produce reports/comparison.md
Create one comparison table per task.

Keep quality, token usage, latency, and repairs in the same table.

Example:

Model	Prompt	Quality	Input tokens/case	Output tokens/case	Median latency	Max latency	Repairs
Mistral	summarize.v1	10/12	...	...	...	...	2/12
Qwen	summarize.v1 transfer	11/12	...	...	...	...	1/12
Use task-appropriate quality metrics.

For extraction, keep missed values and invented/unsupported values separate.

For triage, include routing accuracy, escalation accuracy, missed escalations, unnecessary escalations, human-boundary compliance, and PII leakage where applicable.

10. Report Local Measurements Correctly
Do not invent cloud cost.

For Ollama:

cost_usd = 0.0
Report instead:

input tokens
output tokens
median latency
maximum latency
observation count
repair rate
retry/failure count
Do not use mean latency as the headline number.

11. Write the Limits Section
State explicitly:

there are only 12 cases per task
results are directional, not production-scale estimates
prompt-transfer rows are identified
untested combinations are identified
no production-volume reliability claim is being made
local Ollama latency depends on lab hardware
Do not turn 11/12 versus 10/12 into a universal model ranking.

12. Write the Recommendation
For each task, name:

task
model
prompt version
reason
condition that would reopen the decision
The recommendation must be based on the measured evidence.

13. Complete docs/model-decision.md
Fill in:

evidence
decision
rejected alternatives
review triggers
Every evidence row must name the prompt version used.

Do not rewrite earlier decision constraints after seeing the results.

14. Re-Verify the Day 4 Human Boundary Under Both Models
Run the triage boundary metric against both Mistral and Qwen.

No committed draft_reply may promise a refund, approve/deny a claim, state that the issue is resolved, or imply a final customer outcome.

State in the report which models were tested.

15. Run Engineering Checks
Run:

pytest
ruff check
mypy
until clean.

Open the final pull request. Keep deterministic scoring changes separate from prompt changes in Git history.

Final Deliverable
The final repository should contain:

src/promptlab/
├── usage.py
├── config.py
├── errors.py
├── adapters/
├── schemas.py
├── prompts.py
├── structured.py
├── scoring.py
├── rules.py
└── run.py
Preserve all measured files under:

src/promptlab/prompts/
Commit:

docs/day5-run.jsonl
docs/day5-scores.jsonl
reports/comparison.md
docs/model-decision.md
Preserve docs/model-facts.md if it already exists.