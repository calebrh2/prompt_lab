When Not to Use an LLM
Why this matters on an engagement
The fastest way to lose credibility with a client engineering team is to put a model in front of a problem their existing system already solves correctly. They will notice, they will not say anything in the meeting, and they will decide that the AI team does not understand the domain. The reverse is also true: the fastest way to gain credibility is to point at a step in your own design and say that one should be code, before anyone else does.

There is a harder version of this coming. When a model risk or change control function reviews what you built, they will ask which parts of the behavior are specified and which are learned. Every rule you encoded in a prompt is in the second category, which means you cannot show them a test that proves it holds. Every rule you encoded in code is in the first, and the conversation takes minutes instead of weeks. Deciding where that line falls is architecture, and it is decided early or not at all.

Core concepts
The test is whether the input determines the output. If a competent person given the same facts and the same written procedure would always produce the same answer, the answer is determined, and determined answers belong in code. A model asked for a determined answer will usually produce it and will occasionally produce something else, which is strictly worse than a function that produces it every time. Where the answer genuinely depends on reading, weighing, or interpreting, you are in the model's territory. Most real workflows contain both, and the useful work is separating them rather than choosing one.

Arithmetic and dates are never the model's job. Procedural deadlines, business day counts, policy period boundaries, threshold comparisons, and anything involving a holiday calendar are computations. A model will get them right most of the time, which is the property that makes this failure dangerous rather than obvious: it survives a demo, it survives a test set of twelve, and it fails on the case with a bank holiday in it. The card dispute workflow this program builds toward states this outright, requiring procedural deadlines to be calculated deterministically. Treat that as the general rule and not a peculiarity of that use case.

A lookup belongs to the system that owns the record. Policy status, transaction detail, customer master data, and sanctions list entries have an authoritative source, and a model producing a value that resembles the right one is not a lookup, it is a recollection. This holds even when the model has seen the value earlier in the same request, because there is no guarantee it reproduces it unchanged. How a system of record gets called is Week 4's subject and how documents get retrieved is Week 3's. Today's point is narrower and applies before either: if there is an owner for a fact, the fact comes from the owner.

Every deterministic step moved into code is removed from the bill and from the clock. A rule applied in Python costs microseconds and nothing per case. The same rule applied in a prompt costs input tokens on every request, output tokens to state its conclusion, and a network round trip. Day 1's cost model makes this concrete: the savings are not a rounding error at forty thousand cases a month, and they compound with every case volume increase rather than being renegotiated.

Code can be proven to have been applied. A prompt cannot. A rule in a function has a diff, a test, a reviewer, and a release. You can show a change control function the commit that changed the threshold, the test that pins the boundary case, and the date it shipped. A rule in a prompt is text that influences a probabilistic process, and the honest answer to whether it was applied on a given case is that it usually is. In a regulated function that difference decides whether a feature ships. It also decides how a defect gets fixed: a wrong rule in code is a one line change with a regression test, and a wrong rule in a prompt is an experiment.

The shape that works is the model reads and the code decides. The model turns unstructured input into a structured, cited object. Code applies the rules to that object and produces the decision. This gives you the strengths of both: the model does the part that requires reading messy human text, and the decision is deterministic, testable, and explicable. It also localizes failure, because a wrong outcome is either a bad extraction, visible against the cited source, or a bad rule, visible in a unit test. All three systems this program builds toward have this shape, and so does every one of them that survives a compliance review.

The model is the right tool where reading and judgment are the work. Turning a rambling customer narrative into structured facts. Recognizing that a document contradicts itself. Deciding whether a discrepancy is substantive or a wording difference. Summarizing for a human who will act on it. Drafting text a person will review and send. These are the tasks where no rule exists to encode, and declining to use a model on them in the name of determinism produces a system nobody can build. The skill is not skepticism, it is placement.

Worked example
Here is a triage step as it is usually first written, and then as it should be split.

The single prompt asks the model to classify the dispute, compute the regulatory response deadline from the transaction date, decide whether the case is urgent, and draft a reply. On twelve cases it classifies eleven correctly and computes eleven deadlines correctly. The one it gets wrong falls on a weekend.

Split, the model produces facts only:

class DisputeFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dispute_type: DisputeType
    transaction_date: Evidence[date]
    amount: Evidence[Decimal]
    customer_claims_unauthorized: Evidence[bool]
    prior_merchant_relationship: Evidence[bool]

And code makes the decisions:

RESPONSE_DAYS: dict[DisputeType, int] = {
    DisputeType.UNAUTHORIZED: 10,
    DisputeType.DUPLICATE_CHARGE: 15,
    DisputeType.SERVICE_NOT_RECEIVED: 30,
}


def response_deadline(facts: DisputeFacts, calendar: BusinessCalendar) -> date:
    """Deadline in business days from the transaction date."""
    start = facts.transaction_date.value
    return calendar.add_business_days(start, RESPONSE_DAYS[facts.dispute_type])


def route(facts: DisputeFacts, deadline: date, today: date) -> Queue:
    if facts.customer_claims_unauthorized.value and not facts.prior_merchant_relationship.value:
        return Queue.FRAUD_REPORT
    if calendar_days_until(deadline, today) <= 2:
        return Queue.URGENT_DISPUTE
    return Queue.CARD_DISPUTE

Four things changed, and only one of them is about accuracy.

The deadline is now correct twelve times out of twelve, and it will be correct on the bank holiday case that is not in the set, because BusinessCalendar knows about holidays and the model was guessing. More importantly, the weekend case is now testable. You can write a unit test that pins it, and that test will fail if someone changes the calendar. Nothing equivalent exists for a rule expressed as a sentence in a prompt.

The routing rule is legible to a domain expert. A dispute manager can read route and tell you it is wrong, which is a conversation you want to have in week two of an engagement rather than in production. They cannot do that with a paragraph of instruction whose effect is probabilistic.

The output tokens fell, because the model is no longer explaining a deadline or justifying a routing choice. The input tokens fell too, because the rules that used to be stated in the prompt are no longer sent on every request. This is the cost lever from Day 1, applied.

The failure surface split cleanly. If the routing is wrong, either prior_merchant_relationship was extracted incorrectly, which you can check against its citation, or route encodes the wrong rule, which you can check against the procedure. Before the split there was one failure called the model got it wrong.

Note what stayed with the model. Reading the narrative, deciding the dispute type, judging whether a prior relationship exists from inconsistent evidence, and drafting the reply. Those are the parts with no rule to encode.

Failure modes
The rule that lives in the prompt. A threshold, a deadline, a routing table, or an eligibility condition expressed as instruction. It cannot be unit tested, it cannot be shown to have been applied, and it changes behavior in ways a diff does not predict. When a rule has a written source, encode the source.

Date arithmetic delegated to the model. Correct on most cases and wrong on the ones involving weekends, holidays, month ends, and time zones. The high hit rate is what allows it through review. Any computation over dates belongs in a function with a calendar and a test.

The model used as a database. A value recalled rather than retrieved, presented with the same confidence as a real lookup, and indistinguishable from one in the output. If a fact has an owning system, the fact comes from that system, and the fact is cited to it.

The deterministic step left in for convenience. Keeping a computation in the prompt because splitting it out is a refactor means paying tokens and latency for it on every case for the life of the engagement, and carrying an untestable rule into every future review. The refactor gets cheaper the earlier it happens.

Two implementations of one rule. A rule encoded in code and also stated in the prompt will eventually disagree, and nothing in the output says which one produced the answer. Pick the owner, remove the other, and if the prompt needs to mention the rule at all, have it mention that code applies it.

Checklist
[ ] Every step in the pipeline has been asked whether the input determines the output.

[ ] No arithmetic, date computation, or threshold comparison is performed by the model.

[ ] Every fact with an owning system comes from that system rather than from generation.

[ ] Rules with a written source are encoded in code, with a test pinning at least one boundary case.

[ ] The model produces a structured, cited object and code produces the decision.

[ ] No rule is implemented in both the prompt and the code.

[ ] A domain expert could read the decision logic and say whether it is right.

[ ] The tasks left with the model are ones where reading or judgment is genuinely required.

