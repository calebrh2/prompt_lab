from __future__ import annotations

from promptlab.records import ScoreRecord
from promptlab.schemas import TriageOutput
from promptlab.scoring import SCORER_VERSION, human_boundary_pass, score_triage


def _gold(*, queue: str, escalation: bool) -> dict[str, object]:
    return {
        "id": "T01",
        "task": "triage",
        "expected_queue": queue,
        "expected_escalation": escalation,
        "human_review_required": True,
    }


def _output(
    *,
    queue: str,
    escalation: bool,
    draft: str = "A specialist will review this.",
) -> dict[str, object]:
    return TriageOutput(
        queue=queue,  # type: ignore[arg-type]
        escalation_required=escalation,
        confidence=0.7,
        rationale="routing",
        draft_reply=draft,
        human_review_required=True,
        customer_outcome=None,
    ).model_dump()


def test_queue_accuracy_uses_expected_queue() -> None:
    records = score_triage(
        run_id="r1",
        task="triage",
        case_id="T01",
        model_name="mistral",
        prompt_version="v1",
        gold=_gold(queue="card_dispute", escalation=False),
        output=_output(queue="fraud_report", escalation=False),
    )
    queue = next(row for row in records if row.metric == "queue_accuracy")
    assert queue.numerator == 0
    assert queue.denominator == 1
    assert "card_dispute" in (queue.detail or "")


def test_escalation_uses_escalation_required_not_human_review() -> None:
    gold = _gold(queue="escalate", escalation=True)
    output = _output(queue="escalate", escalation=False)
    output["human_review_required"] = True
    records = score_triage(
        run_id="r1",
        task="triage",
        case_id="T06",
        model_name="mistral",
        prompt_version="v1",
        gold=gold,
        output=output,
    )
    escalation = next(row for row in records if row.metric == "escalation_accuracy")
    missed = next(row for row in records if row.metric == "missed_escalation")
    unnecessary = next(row for row in records if row.metric == "unnecessary_escalation")
    assert escalation.numerator == 0
    assert missed.numerator == 1
    assert missed.lower_is_better is True
    assert unnecessary.numerator == 0


def test_unnecessary_escalation_is_separate_from_missed() -> None:
    records = score_triage(
        run_id="r1",
        task="triage",
        case_id="T01",
        model_name="mistral",
        prompt_version="v1",
        gold=_gold(queue="card_dispute", escalation=False),
        output=_output(queue="card_dispute", escalation=True),
    )
    missed = next(row for row in records if row.metric == "missed_escalation")
    unnecessary = next(row for row in records if row.metric == "unnecessary_escalation")
    assert missed.numerator == 0
    assert unnecessary.numerator == 1
    assert unnecessary.lower_is_better is True


def test_human_boundary_is_deterministic_and_uses_existing_score_record() -> None:
    crossing = _output(
        queue="card_dispute",
        escalation=False,
        draft="Your dispute has been approved and the funds will be refunded.",
    )
    assert human_boundary_pass(crossing) is False
    records = score_triage(
        run_id="r1",
        task="triage",
        case_id="T01",
        model_name="mistral",
        prompt_version="v1",
        gold=_gold(queue="card_dispute", escalation=False),
        output=crossing,
    )
    boundary = next(row for row in records if row.metric == "human_boundary")
    assert boundary.numerator == 0
    assert isinstance(records[0], ScoreRecord)
    assert records[0].scorer_version == SCORER_VERSION


def test_human_boundary_passes_neutral_draft() -> None:
    output = _output(queue="card_dispute", escalation=False)
    assert human_boundary_pass(output) is True


def test_scoring_module_does_not_define_a_second_score_record() -> None:
    import inspect

    import promptlab.scoring as scoring

    assert "class ScoreRecord" not in inspect.getsource(scoring)
    records = score_triage(
        run_id="r1",
        task="triage",
        case_id="T01",
        model_name="mistral",
        prompt_version="v1",
        gold=_gold(queue="card_dispute", escalation=False),
        output=_output(queue="card_dispute", escalation=False),
    )
    assert isinstance(records[0], ScoreRecord)
