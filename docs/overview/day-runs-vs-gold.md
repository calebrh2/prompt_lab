# Day runs vs gold labels

Side-by-side comparison of committed `docs/dayN-run.jsonl` outputs against `cases/gold/*.jsonl`.

- **Primary:** triage `queue`, or extraction/summarization `document_status`
- **Secondary:** triage `escalation_required`, or presence of gold `recoverable_fields`
- **Both match:** primary and secondary both agree with gold
- Day 5 has no committed run records
- Day 1–2 outputs are unstructured; status is inferred from free text
- Day 2 used a KYC extraction prompt on summarization cases, so `purpose` / `required_steps` / `exceptions` are usually missing even when title and version were found



## Summary


| Day   | Task          | Prompt       | Model      | Both match | Primary (queue/status) | Secondary (escalation/fields) |
| ----- | ------------- | ------------ | ---------- | ---------- | ---------------------- | ----------------------------- |
| Day 1 | extraction    | baseline v0  | mistral:7b | 2/3        | 2/3                    | 3/3                           |
| Day 2 | summarization | baseline v0  | mistral:7b | 0/12       | 8/12                   | 0/12                          |
| Day 2 | summarization | baseline v0  | qwen3:8b   | 0/12       | 9/12                   | 0/12                          |
| Day 3 | summarization | summarize v1 | mistral:7b | 8/12       | 8/12                   | 11/12                         |
| Day 3 | extraction    | extract v2   | mistral:7b | 8/12       | 9/12                   | 11/12                         |
| Day 4 | triage        | triage v1    | mistral:7b | 7/12       | 7/12                   | 12/12                         |
| Day 4 | triage        | triage v2    | mistral:7b | 8/13       | 8/13                   | 12/13                         |




## Day 1


| Case                                       | Task       | Prompt      | Model      | Gold status   | Predicted status | Status | Recoverable present | Missing recoverable | Extra present | Both  |
| ------------------------------------------ | ---------- | ----------- | ---------- | ------------- | ---------------- | ------ | ------------------- | ------------------- | ------------- | ----- |
| E12 (unstructured output; status inferred) | extraction | baseline v0 | mistral:7b | `unsupported` | `unsupported`    | match  | 0/0                 | —                   | —             | match |
| E07 (unstructured output; status inferred) | extraction | baseline v0 | mistral:7b | `valid`       | `valid`          | match  | 6/6                 | —                   | —             | match |
| E11 (unstructured output; status inferred) | extraction | baseline v0 | mistral:7b | `valid`       | `contradictory`  | miss   | 7/7                 | —                   | —             | miss  |




## Day 2

Baseline v0 asked for KYC extraction fields on summarization gold (title, purpose, required_steps, exceptions). Field recall is expected to be low. Qwen S01 refused the KYC framing; S10 returned empty (truncated).


| Case                                       | Task          | Prompt      | Model      | Gold status     | Predicted status | Status | Recoverable present | Missing recoverable                                                 | Extra present      | Both |
| ------------------------------------------ | ------------- | ----------- | ---------- | --------------- | ---------------- | ------ | ------------------- | ------------------------------------------------------------------- | ------------------ | ---- |
| S01 (unstructured output; status inferred) | summarization | baseline v0 | mistral:7b | `superseded`    | `contradictory`  | miss   | 2/6                 | title, purpose, required_steps, exceptions                          | —                  | miss |
| S02 (unstructured output; status inferred) | summarization | baseline v0 | mistral:7b | `valid`         | `contradictory`  | miss   | 1/6                 | version, effective_date, purpose, required_steps, exceptions        | —                  | miss |
| S03 (unstructured output; status inferred) | summarization | baseline v0 | mistral:7b | `valid`         | `valid`          | match  | 3/6                 | purpose, required_steps, exceptions                                 | —                  | miss |
| S04 (unstructured output; status inferred) | summarization | baseline v0 | mistral:7b | `contradictory` | `contradictory`  | match  | 3/5                 | purpose, exceptions                                                 | —                  | miss |
| S05 (unstructured output; status inferred) | summarization | baseline v0 | mistral:7b | `unsupported`   | `unsupported`    | match  | 0/1                 | title                                                               | —                  | miss |
| S06 (unstructured output; status inferred) | summarization | baseline v0 | mistral:7b | `valid`         | `contradictory`  | miss   | 3/6                 | purpose, required_steps, exceptions                                 | required_documents | miss |
| S07 (unstructured output; status inferred) | summarization | baseline v0 | mistral:7b | `valid`         | `valid`          | match  | 3/6                 | purpose, required_steps, exceptions                                 | —                  | miss |
| S08 (unstructured output; status inferred) | summarization | baseline v0 | mistral:7b | `valid`         | `contradictory`  | miss   | 1/6                 | version, effective_date, purpose, required_steps, exceptions        | —                  | miss |
| S09 (unstructured output; status inferred) | summarization | baseline v0 | mistral:7b | `contradictory` | `contradictory`  | match  | 3/5                 | purpose, exceptions                                                 | required_documents | miss |
| S10 (unstructured output; status inferred) | summarization | baseline v0 | mistral:7b | `valid`         | `valid`          | match  | 1/6                 | version, effective_date, purpose, required_steps, exceptions        | —                  | miss |
| S11 (unstructured output; status inferred) | summarization | baseline v0 | mistral:7b | `valid`         | `valid`          | match  | 1/6                 | version, effective_date, purpose, required_steps, exceptions        | —                  | miss |
| S12 (unstructured output; status inferred) | summarization | baseline v0 | mistral:7b | `unsupported`   | `unsupported`    | match  | 0/1                 | title                                                               | —                  | miss |
| S01 (unstructured output; status inferred) | summarization | baseline v0 | qwen3:8b   | `superseded`    | `unparsed`       | miss   | 0/6                 | title, version, effective_date, purpose, required_steps, exceptions | —                  | miss |
| S02 (unstructured output; status inferred) | summarization | baseline v0 | qwen3:8b   | `valid`         | `valid`          | match  | 3/6                 | purpose, required_steps, exceptions                                 | —                  | miss |
| S03 (unstructured output; status inferred) | summarization | baseline v0 | qwen3:8b   | `valid`         | `valid`          | match  | 1/6                 | version, effective_date, purpose, required_steps, exceptions        | —                  | miss |
| S04 (unstructured output; status inferred) | summarization | baseline v0 | qwen3:8b   | `contradictory` | `contradictory`  | match  | 3/5                 | purpose, exceptions                                                 | —                  | miss |
| S05 (unstructured output; status inferred) | summarization | baseline v0 | qwen3:8b   | `unsupported`   | `unsupported`    | match  | 0/1                 | title                                                               | —                  | miss |
| S06 (unstructured output; status inferred) | summarization | baseline v0 | qwen3:8b   | `valid`         | `valid`          | match  | 3/6                 | purpose, required_steps, exceptions                                 | review_frequency   | miss |
| S07 (unstructured output; status inferred) | summarization | baseline v0 | qwen3:8b   | `valid`         | `valid`          | match  | 1/6                 | version, effective_date, purpose, required_steps, exceptions        | —                  | miss |
| S08 (unstructured output; status inferred) | summarization | baseline v0 | qwen3:8b   | `valid`         | `unsupported`    | miss   | 0/6                 | title, version, effective_date, purpose, required_steps, exceptions | —                  | miss |
| S09 (unstructured output; status inferred) | summarization | baseline v0 | qwen3:8b   | `contradictory` | `contradictory`  | match  | 3/5                 | purpose, exceptions                                                 | required_documents | miss |
| S10 (unstructured output; status inferred) | summarization | baseline v0 | qwen3:8b   | `valid`         | `unparsed`       | miss   | 0/6                 | title, version, effective_date, purpose, required_steps, exceptions | —                  | miss |
| S11 (unstructured output; status inferred) | summarization | baseline v0 | qwen3:8b   | `valid`         | `valid`          | match  | 1/6                 | version, effective_date, purpose, required_steps, exceptions        | —                  | miss |
| S12 (unstructured output; status inferred) | summarization | baseline v0 | qwen3:8b   | `unsupported`   | `unsupported`    | match  | 0/1                 | title                                                               | —                  | miss |




## Day 3


| Case | Task          | Prompt       | Model      | Gold status     | Predicted status | Status | Recoverable present | Missing recoverable            | Extra present  | Both  |
| ---- | ------------- | ------------ | ---------- | --------------- | ---------------- | ------ | ------------------- | ------------------------------ | -------------- | ----- |
| S01  | summarization | summarize v1 | mistral:7b | `superseded`    | `valid`          | miss   | 6/6                 | —                              | —              | miss  |
| S02  | summarization | summarize v1 | mistral:7b | `valid`         | `valid`          | match  | 6/6                 | —                              | —              | match |
| S03  | summarization | summarize v1 | mistral:7b | `valid`         | `valid`          | match  | 6/6                 | —                              | —              | match |
| S04  | summarization | summarize v1 | mistral:7b | `contradictory` | `valid`          | miss   | 4/5                 | exceptions                     | required_steps | miss  |
| S05  | summarization | summarize v1 | mistral:7b | `unsupported`   | `valid`          | miss   | 1/1                 | —                              | effective_date | miss  |
| S06  | summarization | summarize v1 | mistral:7b | `valid`         | `valid`          | match  | 6/6                 | —                              | —              | match |
| S07  | summarization | summarize v1 | mistral:7b | `valid`         | `valid`          | match  | 6/6                 | —                              | —              | match |
| S08  | summarization | summarize v1 | mistral:7b | `valid`         | `valid`          | match  | 6/6                 | —                              | —              | match |
| S09  | summarization | summarize v1 | mistral:7b | `contradictory` | `contradictory`  | match  | 5/5                 | —                              | required_steps | match |
| S10  | summarization | summarize v1 | mistral:7b | `valid`         | `valid`          | match  | 6/6                 | —                              | —              | match |
| S11  | summarization | summarize v1 | mistral:7b | `valid`         | `valid`          | match  | 6/6                 | —                              | —              | match |
| S12  | summarization | summarize v1 | mistral:7b | `unsupported`   | `valid`          | miss   | 1/1                 | —                              | effective_date | miss  |
| E01  | extraction    | extract v2   | mistral:7b | `superseded`    | `valid`          | miss   | 7/7                 | —                              | —              | miss  |
| E02  | extraction    | extract v2   | mistral:7b | `valid`         | `valid`          | match  | 7/7                 | —                              | —              | match |
| E03  | extraction    | extract v2   | mistral:7b | `valid`         | `valid`          | match  | 6/6                 | —                              | —              | match |
| E04  | extraction    | extract v2   | mistral:7b | `contradictory` | `valid`          | miss   | 6/6                 | —                              | jurisdictions  | miss  |
| E05  | extraction    | extract v2   | mistral:7b | `valid`         | `valid`          | match  | 6/7                 | beneficial_ownership_threshold | —              | miss  |
| E06  | extraction    | extract v2   | mistral:7b | `valid`         | `valid`          | match  | 7/7                 | —                              | —              | match |
| E07  | extraction    | extract v2   | mistral:7b | `valid`         | `valid`          | match  | 6/6                 | —                              | —              | match |
| E08  | extraction    | extract v2   | mistral:7b | `valid`         | `valid`          | match  | 7/7                 | —                              | —              | match |
| E09  | extraction    | extract v2   | mistral:7b | `valid`         | `valid`          | match  | 6/6                 | —                              | —              | match |
| E10  | extraction    | extract v2   | mistral:7b | `contradictory` | `valid`          | miss   | 6/6                 | —                              | jurisdictions  | miss  |
| E11  | extraction    | extract v2   | mistral:7b | `valid`         | `valid`          | match  | 7/7                 | —                              | —              | match |
| E12  | extraction    | extract v2   | mistral:7b | `unsupported`   | `unsupported`    | match  | 0/0                 | —                              | —              | match |




## Day 4

T07 v2 appears twice: first attempt returned invalid `lending,complaint`; the repair then predicted `complaint` and dropped escalation.

### triage v1


| Case | Prompt    | Model      | Gold queue          | Predicted queue     | Queue | Gold esc | Predicted esc | Escalation | Both  |
| ---- | --------- | ---------- | ------------------- | ------------------- | ----- | -------- | ------------- | ---------- | ----- |
| T01  | triage v1 | mistral:7b | `card_dispute`      | `card_dispute`      | match | `False`  | `False`       | match      | match |
| T02  | triage v1 | mistral:7b | `fraud_report`      | `card_dispute`      | miss  | `False`  | `False`       | match      | miss  |
| T03  | triage v1 | mistral:7b | `account_servicing` | `account_servicing` | match | `False`  | `False`       | match      | match |
| T04  | triage v1 | mistral:7b | `lending`           | `lending`           | match | `False`  | `False`       | match      | match |
| T05  | triage v1 | mistral:7b | `complaint`         | `complaint`         | match | `False`  | `False`       | match      | match |
| T06  | triage v1 | mistral:7b | `escalate`          | `card_dispute`      | miss  | `True`   | `True`        | match      | miss  |
| T07  | triage v1 | mistral:7b | `escalate`          | `lending`           | miss  | `True`   | `True`        | match      | miss  |
| T08  | triage v1 | mistral:7b | `escalate`          | `escalate`          | match | `True`   | `True`        | match      | match |
| T09  | triage v1 | mistral:7b | `unsupported`       | `lending`           | miss  | `False`  | `False`       | match      | miss  |
| T10  | triage v1 | mistral:7b | `account_servicing` | `account_servicing` | match | `False`  | `False`       | match      | match |
| T11  | triage v1 | mistral:7b | `card_dispute`      | `card_dispute`      | match | `False`  | `False`       | match      | match |
| T12  | triage v1 | mistral:7b | `fraud_report`      | `card_dispute`      | miss  | `False`  | `False`       | match      | miss  |




### triage v2


| Case           | Prompt    | Model      | Gold queue          | Predicted queue     | Queue   | Gold esc | Predicted esc | Escalation | Both  |
| -------------- | --------- | ---------- | ------------------- | ------------------- | ------- | -------- | ------------- | ---------- | ----- |
| T01            | triage v2 | mistral:7b | `card_dispute`      | `card_dispute`      | matchci | `False`  | `False`       | match      | match |
| T02            | triage v2 | mistral:7b | `fraud_report`      | `card_dispute`      | miss    | `False`  | `False`       | match      | miss  |
| T03            | triage v2 | mistral:7b | `account_servicing` | `account_servicing` | match   | `False`  | `False`       | match      | match |
| T04            | triage v2 | mistral:7b | `lending`           | `lending`           | match   | `False`  | `False`       | match      | match |
| T05            | triage v2 | mistral:7b | `complaint`         | `complaint`         | match   | `False`  | `False`       | match      | match |
| T06            | triage v2 | mistral:7b | `escalate`          | `escalate`          | match   | `True`   | `True`        | match      | match |
| T07            | triage v2 | mistral:7b | `escalate`          | `lending,complaint` | miss    | `True`   | `True`        | match      | miss  |
| T07 (repair 1) | triage v2 | mistral:7b | `escalate`          | `complaint`         | miss    | `True`   | `False`       | miss       | miss  |
| T08            | triage v2 | mistral:7b | `escalate`          | `fraud_report`      | miss    | `True`   | `True`        | match      | miss  |
| T09            | triage v2 | mistral:7b | `unsupported`       | `unsupported`       | match   | `False`  | `False`       | match      | match |
| T10            | triage v2 | mistral:7b | `account_servicing` | `account_servicing` | match   | `False`  | `False`       | match      | match |
| T11            | triage v2 | mistral:7b | `card_dispute`      | `card_dispute`      | match   | `False`  | `False`       | match      | match |
| T12            | triage v2 | mistral:7b | `fraud_report`      | `card_dispute`      | miss    | `False`  | `False`       | match      | miss  |


