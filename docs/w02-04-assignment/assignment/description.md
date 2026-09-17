Day 2 Assignment: A Routing Decision You Can Measure (Local Ollama Version)
Objective
Build a measurable triage workflow using the contracts already established in the Week 2 repository.

By the end of the lab:

all 12 triage cases return structured output validated against the existing TriageOutput schema
customer content is kept separate from standing model instructions
prompt rendering is centralized through the prompt registry
two prompt versions are compared under the same local model and run conditions
routing, escalation, and human-boundary behavior are scored deterministically
results are recorded in reproducible run and score artifacts
This lab continues the architecture built on Days 1–3:

Day 4 code
    ↓
complete_structured(...)
    ↓
ModelAdapter
    ↓
OllamaAdapter
    ↓
configured Mistral or Qwen model
For the local lab:

provider = "ollama"
cost_usd = 0.0
Do not add cloud credentials and do not invent token prices for the local models.

Contracts Consumed from Earlier Days
C1: Call recording
Continue using the existing Day 1 call-recording contract.

Every actual model attempt must remain traceable through the run evidence, including:

first attempts
adapter retries
structured-output repair attempts
final failures
Do not replace the existing usage/call-record contract.

C2: Adapter contract
The Day 2 request vocabulary remains:

Literal["triage", "summarization", "extraction"]
Day 4 requests use:

task="triage"
Do not change the adapter interface and do not introduce "summarize" or "extract" as task values.

C3: Structured completion
Continue using the Day 3 structured-output path.

Day 4 model calls must still flow through:

complete_structured(...)
Schema/content repair belongs in the structured-completion layer.

Transport retry behavior remains the adapter's responsibility.

Source of Truth for the Triage Output
The existing model in:

src/promptlab/schemas.py
is the source of truth.

Use the shipped:

TriageOutput
Do not create a competing TriageDecision model.

The current TriageOutput contract includes these existing fields:

queue
escalation_required
confidence
rationale
draft_reply
human_review_required
customer_outcome
Do not rename those fields to match older versions of the curriculum.

In particular:

escalation_required
is the field used for escalation scoring against the gold label.

Do not replace it with:

requires_human_review
and do not substitute:

human_review_required
for the gold-label escalation decision.

Prompt Locations
The repository uses two different prompt-related locations.

Python prompt-registry code lives here:

src/promptlab/prompts.py
Markdown prompt files live here:

src/prompts/
These are different things.

By the end of Day 4, the prompt directory should contain:

src/prompts/
├── baseline.v0.md
├── summarize.v1.md
├── extract.v1.md
├── extract.v2.md
├── triage.v1.md
└── triage.v2.md
Do not put the Markdown prompt files under src/promptlab/.

Shipped Starter Material
The Day 4 starter should already contain:

cases/triage.jsonl
cases/gold/
src/promptlab/config.py
src/promptlab/records.py
src/promptlab/schemas.py
src/promptlab/structured.py
src/promptlab/prompts.py
tests/test_prompt_registry_contract.py
src/promptlab/prompts.py is starter code for Day 4. It provides the prompt-registry structure and leaves render_user(...) as student work.

Do not replace:

src/promptlab/schemas.py
src/promptlab/records.py
with new parallel contracts.

The Human Boundary
The triage component may:

choose a routing queue
set the existing escalation field
provide a confidence value
provide a concise routing rationale
draft a neutral reply for a human employee to review
The triage component may not:

send the message
close or resolve the case
approve or deny a claim
promise a refund or reimbursement
state that a final customer outcome has already been decided
For example, this crosses the boundary:

Your dispute has been approved and the funds will be refunded.
A routing decision can be correct and still fail the human-boundary requirement.