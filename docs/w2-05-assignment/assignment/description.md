**Assignment**: Prompt Portfolio and Local Model Comparison (Ollama Version)
Objective
Integrate the work from Days 1-4 into one reproducible evaluation harness.

By the end of the lab, one command should:

run summarization, extraction, and triage
run all three tasks against both configured local models: Mistral and Qwen
validate structured outputs
record every model-call attempt
score outputs deterministically against the gold labels
compare quality, token usage, latency, repairs, and failures
produce reports/comparison.md and a model recommendation
This is the integration day. Do not rebuild the adapter, schema, or prompt architecture.

Local Lab Environment
Use the local stack already established:

application
  -> ModelAdapter
  -> OllamaAdapter
  -> Mistral or Qwen
For both models:

provider = "ollama"
cost_usd = 0.0
Model identity must come from configuration through model_id.

Do not add Anthropic, Azure OpenAI, or other cloud credentials. Do not invent commercial token prices for the local models.

For this lab, compare:

quality
input tokens
output tokens
median latency
maximum latency
repair rate
failed attempts / retries
rather than provider-dollar cost.

Prerequisites
Day 4 must be merged, or these components must already work:

C1: CallRecord and append-only run recording
C2: ModelAdapter and OllamaAdapter
C3: schemas, prompts, and complete_structured
C4: TriageDecision
C5: scoring records and Day 4 metrics
Ollama must be running and both Mistral and Qwen must be available from inside the devcontainer.

Case Sets
Use the current local corpus layout:

cases/
├── extraction.jsonl
├── summarization.jsonl
├── triage.jsonl
└── gold/
Each corpus contains 12 cases.

The gold/ directory contains instructor-authored expected labels. Do not edit the gold labels and do not use them as prompt examples.

Prompt Versions
Preserve every measured prompt version.

The expected Day 5 task prompts are:

summarization -> summarize.v1
extraction    -> extract.v2
triage        -> the Day 4 version selected for final evaluation
baseline.v0.md remains historical evidence from Days 1-2. Do not use it as the final Day 5 task prompt.

Never edit a prompt version after it has produced recorded results.

**What Day 5 Is Doing**

run.py
  -> three tasks
  -> versioned prompts
  -> complete_structured()
  -> ModelAdapter
  -> OllamaAdapter
  -> Mistral / Qwen
  -> validated objects
  -> deterministic scoring
  -> gold labels
  -> reports/comparison.md
  -> model recommendation
The model produces candidate outputs. The application validates them, deterministic code scores them, and the evidence drives the recommendation.

