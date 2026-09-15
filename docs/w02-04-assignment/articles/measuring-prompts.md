Measuring a Prompt
Why this matters on an engagement
The question that ends a prompt discussion is how you know. Two engineers will disagree about whether a change improved things, both will have read outputs, and both will be sure. Without a number neither can be shown to be wrong, so the argument resolves by seniority and the system gets worse in small increments that nobody can point at. A twelve-case scored set turns that into a five minute check, and the five minutes is the cheapest thing you will do this week.

It also matters because a client will eventually ask you to state a quality figure, and the number you give will be repeated in rooms you are not in. If it came from reading twenty outputs and forming an impression, you will not be able to defend it, reproduce it, or say what would change it. If it came from a fixed case set with written labels, you can say exactly what it measures, exactly what it does not, and how much of it is noise.

Core concepts
A measurement needs a fixed case set and gold labels written before you measure. The cases are frozen: the same twelve, in the same form, for the life of the comparison. The labels are what a competent human says the correct output is, written by reading the source document rather than by reading the system's answer. Where two people disagree about a label, the disagreement is resolved and the reason recorded, because a case whose correct answer is contested is a case that will produce an argument every time the number moves. Cases are added over time as new failures are found, and adding a case resets the comparison rather than continuing it.

Score with code, not with judgment. Everything you measure this week is a deterministic comparison between the parsed output object and the gold object. Exact match on an enum. Set comparison on a list. Presence of a citation. A pattern search for content that should not appear. This is narrower than what evaluation eventually becomes, and it buys three things worth having: the score is reproducible, it costs nothing to run, and it can run on every change rather than when someone remembers. Evaluation frameworks, human-in-the-loop scoring, and using a model to judge another model's output are Week 9. Do not reach for them now.

The families you measure are set by the work, not by what is easy. Across the three use cases this program builds toward, the same families recur: required-evidence recall, correct version selection, evidence grounding and citation correctness, routing and escalation accuracy, and leakage of personal data. Two more, tool-call correctness and idempotency, arrive when agents do. Name them the same way every time. An Associate who meets required-evidence recall in Week 2 and again in Week 9 has learned one thing twice rather than two things once.

Score per field, then aggregate. Whole-object exact match is a tempting metric and an almost useless one, because a twelve-field object is rarely entirely correct and a single number tells you nothing about which field failed. Score each field independently, aggregate to a per-case result, and report per field. The per-field view is what tells you that accuracy fell because the effective date field broke, which is a fifteen minute fix, rather than that accuracy fell, which is an afternoon of reading outputs.

Absence and ambiguity are scored, and the two errors are not the same. A field the document does not state has a gold label of absent, and a system that returns a plausible value there has invented one. A field the document does state, returned as absent, has been missed. Both are wrong and they have different causes and different consequences, so count them separately. Invention on a field a compliance analyst will act on is considerably worse than a miss, because a miss is visible and an invention is not. The same applies to ambiguity: a document that contradicts itself has a gold label of ambiguous, and a system that confidently picks one reading has failed even though it produced a value that appears in the document.

Twelve cases is a small number, and the honest way to report it is counts. One case is more than eight percentage points. A prompt that scores eleven out of twelve is not measurably better than one that scores ten, and presenting those as ninety-two percent against eighty-three percent invents a precision the set cannot support. Report the counts, name the denominator, and treat a one-case difference as no difference. When a change matters, it will move several cases or it will move the same case consistently across repeated runs, and the way to tell is to run it more than once, which the sampling article already established.

The scorer is versioned, and it does not change in the same commit as the prompt. A score record joins to a call record on run, case, model, and prompt version, which is what lets you pivot the same measurement by any of them on Friday. That join only means something if the scoring logic was constant across the runs being compared. Changing the metric and the prompt together produces an improvement that lives in the scorer, and nothing in the output distinguishes it from a real one. Land scorer changes separately, and rescore prior runs when the metric moves so that old numbers and new numbers are still comparable.

Worked example
The score record and the metric shapes, from src/promptlab/scoring.py.

class MetricResult(BaseModel):
    metric: str
    field: str | None
    passed: bool
    detail: str | None = None


class ScoreRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    case_id: str
    task: Literal["triage", "summarize", "extract"]
    model_id: str
    prompt_id: str
    prompt_version: str
    scorer_version: str
    results: list[MetricResult]


Metric = Callable[[BaseModel, BaseModel], list[MetricResult]]

Every metric takes the parsed output and the gold object and returns one result per field it examined. The signature is deliberately narrow. A metric that needs the raw response text, the token counts, or a second model call is not a metric of the kind this week measures.

Here is the extraction scoreboard for one prompt version against one model, twelve cases.

Field

Correct

Missed

Invented

Ambiguity called correctly

document_version

12

0

0

n/a

effective_date

11

1

0

n/a

superseded_by

9

3

0

n/a

beneficial_ownership_threshold_percent

8

1

3

n/a

jurisdictions

10

0

0

1 of 2

required_documents

11

1

0

n/a

Read what that table says, because a single accuracy figure would have said none of it.

The threshold field has three inventions. Three documents do not state a threshold and the system supplied one anyway, which is the exact failure the absent status exists to prevent and the exact failure a compliance analyst would not catch. That is the finding. Everything else on this board is secondary to it, and it is invisible in an aggregate score of fifty-one out of sixty.

The superseded_by misses are a different problem with a different fix. Three documents indicate they have been superseded and the system did not report it, which is version selection, one of the recurring families and one of the named failure archetypes. The fix is likely in the prompt rather than in the model.

The jurisdictions row shows one of two ambiguous cases called correctly. Two cases is not a measurement. It is a note that says look at this again when the case set is larger, and reporting it as fifty percent would be dishonest.

The effective_date miss is one case. It might be a defect and it might be noise, and the way to find out is to run the same version again rather than to change something.

The scoreboard is generated from score records joined to call records, so the same twelve cases can be pivoted by model on Friday without rescoring anything, provided scorer_version is unchanged across the runs being compared.

Failure modes
The case set that moved. Cases added, removed, or edited between runs make two numbers incomparable while leaving them looking like a before and after. Freeze the set for the duration of a comparison, and when you add a case, rescore everything or start the comparison again.

Whole-object accuracy. One figure for a twelve-field object hides which field broke and makes every regression an investigation. It also punishes a change that fixed two fields and broke one, giving no signal about the trade. Score per field and aggregate afterward.

Percentages on twelve cases. Reporting 91.7 percent from eleven of twelve claims a precision the set does not have, and it invites comparison against a figure that differs by one case. Report counts and the denominator, and treat single-case movements as noise until they repeat.

Gold labels written from system output. Labeling by correcting what the system produced, rather than by reading the source, drifts the labels toward the system's habits. The measurement then confirms the system and the error is unrecoverable, because there is no record of what the labels would have been. Labels come from the document.

The scorer changed with the prompt. An improvement produced by a metric that became more lenient looks identical to an improvement produced by a better prompt. Separate the commits, version the scorer, and rescore old runs when the metric changes.

Checklist
[ ] The case set is fixed and its contents are unchanged for the duration of the comparison.

[ ] Gold labels were written by reading the source documents, not by correcting system output.

[ ] Every metric is a deterministic comparison between the parsed output and the gold object.

[ ] No metric calls a model, and no score depends on a human reading an output.

[ ] Metrics are named with the standing families: required-evidence recall, version selection, citation correctness, routing accuracy, escalation accuracy, and personal data leakage.

[ ] Scoring is per field, with per-case and per-field aggregates both available.

[ ] Missed values and invented values are counted separately.

[ ] Fields whose gold label is absent or ambiguous are scored rather than skipped.

[ ] Results are reported as counts with the denominator stated.

[ ] scorer_version is recorded on every score record, and scorer changes land in their own commit.