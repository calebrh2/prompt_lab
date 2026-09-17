Reading a Model Comparison
Why this matters on an engagement
The comparison report is the first artifact from this kind of work that leaves your team. It gets forwarded, quoted in a slide, and read by people who will never see the harness that produced it. Whatever caveat you left out of the document will be left out of every downstream conversation, and the number you reported most prominently will become the number the engagement runs on. Writing it carelessly is how a twelve-case result turns into a production quality commitment three meetings later.

Reading one is the same skill in reverse. You will be handed comparisons produced by vendors, by client teams, and by your own colleagues, and most of them will separate quality from cost, quote a mean latency, and omit which prompt each model ran. Knowing which questions to ask of a table is what stops you inheriting someone else's conclusion.

Core concepts
Quality, cost, and latency belong in one table, per task. Reported separately, each axis produces its own winner and the reader picks whichever table they saw last. Together, in rows the reader can compare across, the trade is visible: this model is better and costs four times as much, that one is faster and misses more. One table per task, because a model that wins on extraction may lose on triage, and a combined average across tasks describes a system nobody is building.

Cost per case includes everything the case cost. Failed attempts that returned tokens, transport retries, and schema repair attempts are all billed, and they are not evenly distributed across models. A model whose output fails validation more often can look cheaper on successful calls and be more expensive per case, which is the single most common misreading in these reports. The C1 records already carry every attempt, so computing this correctly is a matter of summing the right rows rather than of collecting more data.

Latency is a distribution and twelve cases barely describe one. Report the median and the maximum, state the count, and resist the p95 that a larger sample would justify. Mean latency is the worst choice of all, because it hides the retried case that took eleven seconds inside an average that looks fine. Measure from first attempt to final result, as Day 1 established, so a model that succeeds quickly after failing twice is not reported as fast.

Quality is a set of counts, not a score, and the error types are not interchangeable. Two models that both get eight of twelve right are not equivalent if one missed four values and the other invented four. The per-field, per-error-type view from the scoring harness carries into the report unchanged. Collapsing it into a single figure for presentational neatness discards the finding that a compliance reviewer would care about most.

Every row discloses the prompt it ran, and rows with an unadapted prompt are labeled. A model running a prompt developed against a different model is being measured on transfer. That is a legitimate thing to report and it is not a model result, so it is labeled as untested rather than presented as a loss. This is the confounder that makes most published comparisons unusable, and disclosing it per row costs a column.

Twelve cases support direction, not magnitude. They support eliminating a candidate that fails a hard constraint. They support identifying a systematic failure that repeats across several cases, such as a model that never reports a document as superseded. They do not support ranking two candidates that differ by one or two cases, they do not support a percentage, and they do not support any claim about behavior at production volume. Write what the set supports and write, explicitly, what it does not, because the reader will not supply that themselves.

The report ends with a recommendation, and the recommendation names what would change it. One or two sentences per task, naming the model, the prompt version the recommendation rests on, and the condition that would reopen it. The reasoning behind the choice, the constraints it was made against, and the alternatives rejected live in the decision record from earlier in the week. The report supplies the evidence and points at that document rather than restating it.

Worked example
This is reports/comparison.md, generated from the Day 5 run.

# Model comparison: triage, summarization, extraction
Run 2026-08-08-full. 12 cases per task. Scorer version 1.2.
Temperature 0.0. Every row states the prompt version it ran.

## Triage
| Model | Prompt | Routed correctly | Missed escalations | Boundary violations | Median latency | Max latency | Cost per case |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | triage.v1 | 12 of 12 | 0 | 0 | 3.1s | 4.4s | 0.0077 |
| B | triage.v1-b | 11 of 12 | 0 | 0 | 1.4s | 2.2s | 0.0019 |

## Extraction
| Model | Prompt | Fields correct | Missed | Invented | Median latency | Max latency | Cost per case |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | extract.v2 | 61 of 72 | 8 | 3 | 5.6s | 9.1s | 0.0184 |
| B | extract.v2 (untested) | 44 of 72 | 15 | 13 | 2.9s | 5.0s | 0.0046 |

Cost per case includes transport retries and schema repair attempts.
Repair rate: A 1 case in 12, B 4 cases in 12.

## What this does not show
The set is 12 cases per task. A one-case difference is not a difference.
No claim is made about behavior at production volume or on document types
absent from the set.
Extraction on B ran the prompt developed against A and is labeled untested.
It is evidence of transfer, not of B's capability on this task.
Latency was measured from a container in one region on one afternoon.

## Recommendation
Triage on B, running triage.v1-b. One case in twelve for a quarter of the cost,
on a task where a human reads every routed case. Reopen if the missed
escalation count moves above zero on any scheduled run.
Extraction on A, running extract.v2. B is not recommended and is also not
ruled out, because it has not been measured with an adapted prompt.
Constraints, rejected alternatives, and review triggers are in
docs/model-decision.md.

Five things in that report are doing the work.

The extraction row for B is labeled untested and the recommendation says so twice. Everything in the numbers points at B being much worse, and none of it is evidence of that, because B ran a prompt written for A. The honest position is that B has not been measured, and stating it prevents someone six weeks later citing this table as the reason B was rejected.

Missed and invented are separate columns. B's thirteen inventions on extraction are the finding. A model that invents a beneficial ownership threshold is producing something a compliance analyst will act on and cannot see is wrong, and that is a different category of problem from missing a value, which is visible.

Cost per case has a line under it stating what it includes, and the repair rate is reported next to it. Without that line, a reader assumes cost per call, and B's four repairs in twelve cases are exactly what closes the apparent cost gap.

Latency is median and maximum with the count stated, and the last line of the caveats names where and when it was measured. A latency figure without those is not reproducible, and a client whose users sit in another region will experience something else.

The recommendation names the prompt version. Triage on B is only a valid recommendation while triage.v1-b is the prompt, and if someone changes the prompt without rerunning, the recommendation no longer rests on anything.

Failure modes
Three tables, three winners. Quality, cost, and latency presented in separate sections lets every reader construct the conclusion they arrived with, and it hides the trade that is the actual content of the comparison. One table per task, all three axes in it.

Cost quoted from successful calls. Excluding failures and repairs systematically favors the model that fails more, which inverts the ranking on exactly the cases where it matters. The attempt records exist. Sum all of them.

Mean latency. An average across twelve cases conceals the retried case, which is the case a client will ask about. Report the median and the maximum, and say how many observations there were.

The undisclosed prompt. A row that does not name its prompt version is not reproducible, and a row running an unadapted prompt presented as a result is a measurement of transfer wearing the label of a capability. Both are recoverable with one column and one word.

Twelve cases quoted as a quality figure. A percentage from a small set travels further than any caveat attached to it, and it will be repeated to a client as a commitment. Report counts, state the denominator, and write the limits section as though the reader will read nothing else.

Checklist
[ ] One table per task, carrying quality, cost, and latency in the same rows.

[ ] Cost per case includes failed attempts, transport retries, and schema repairs, and the table says so.

[ ] The repair rate is reported alongside cost.

[ ] Latency is reported as median and maximum with the observation count, never as a mean.

[ ] Quality is reported as counts with the denominator, and missed values are separated from invented ones.

[ ] Every row names the prompt version it ran.

[ ] Any row running a prompt developed against a different model is labeled untested.

[ ] A limits section states what the set does not support, including production volume and unseen document types.

[ ] The recommendation names the task, the model, the prompt version, and the condition that would reopen it.

[ ] The report points at the decision record rather than restating the reasoning.