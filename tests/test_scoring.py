from __future__ import annotations

from datetime import date

import pytest

from promptlab.corpus import GoldLabel
from promptlab.records import ScoreRecord
from promptlab.rules import VersionCandidate, select_current_version
from promptlab.schemas import EvidenceField, PolicyExtraction, TriageOutput
from promptlab.scoring import (
    SCORER_VERSION,
    human_boundary_pass,
    score_output,
    score_triage,
    score_version_selection,
    source_sections,
)


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
        model_id="fixture-model",
        prompt_id="triage",
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
        model_id="fixture-model",
        prompt_id="triage",
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
        model_id="fixture-model",
        prompt_id="triage",
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
        model_id="fixture-model",
        prompt_id="triage",
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
        model_id="fixture-model",
        prompt_id="triage",
        prompt_version="v1",
        gold=_gold(queue="card_dispute", escalation=False),
        output=_output(queue="card_dispute", escalation=False),
    )
    assert isinstance(records[0], ScoreRecord)


def test_source_sections_reads_numbered_headings() -> None:
    assert source_sections("1. Document Control\nBody\n2. Scope\nText") == {
        "1. document control",
        "2. scope",
    }


def test_evidence_recall_citations_and_unsupported_avoidance() -> None:
    output = PolicyExtraction(
        document_status="valid",
        policy_name=EvidenceField(
            value="Test Policy", status="present", citation="1. Document Control"
        ),
        version=EvidenceField(value="1.0", status="present", citation="1. Document Control"),
        effective_date=EvidenceField(value=None, status="absent"),
        jurisdictions=EvidenceField(value="Pennsylvania", status="present", citation="2. Scope"),
        beneficial_ownership_threshold=EvidenceField(value=None, status="absent"),
        review_frequency=EvidenceField(value="12 months", status="present", citation="4. Review"),
        required_documents=EvidenceField(value=None, status="absent"),
    )
    gold = GoldLabel(
        id="E00",
        task="extraction",
        expected_status="valid",
        recoverable_fields=["policy_name", "version", "jurisdictions", "review_frequency"],
    )
    scores = score_output(
        run_id="test",
        task="extraction",
        case_id="E00",
        model_name="test",
        model_id="fixture-model",
        prompt_id="extract",
        prompt_version="v1",
        output=output,
        gold=gold,
        source=(
            "1. Document Control\nTest Policy 1.0\n2. Scope\nPennsylvania\n"
            "4. Review\n12 months"
        ),
    )
    by_metric = {score.metric: score for score in scores}
    assert by_metric["required_evidence_recall"].numerator == 4
    assert by_metric["required_evidence_recall"].denominator == 4
    assert by_metric["citation_correctness"].numerator == 4
    assert by_metric["citation_correctness"].denominator == 4
    assert by_metric["unsupported_field_avoidance"].numerator == 3
    assert by_metric["unsupported_field_avoidance"].denominator == 3
    assert "%" not in (by_metric["required_evidence_recall"].detail or "")


def test_citation_correctness_requires_heading_in_source() -> None:
    output = PolicyExtraction(
        document_status="valid",
        policy_name=EvidenceField(
            value="Test Policy", status="present", citation="9. Invented Heading"
        ),
        version=EvidenceField(value=None, status="absent"),
        effective_date=EvidenceField(value=None, status="absent"),
        jurisdictions=EvidenceField(value=None, status="absent"),
        beneficial_ownership_threshold=EvidenceField(value=None, status="absent"),
        review_frequency=EvidenceField(value=None, status="absent"),
        required_documents=EvidenceField(value=None, status="absent"),
    )
    gold = GoldLabel(
        id="E00",
        task="extraction",
        recoverable_fields=["policy_name"],
    )
    scores = score_output(
        run_id="test",
        task="extraction",
        case_id="E00",
        model_name="test",
        model_id="fixture-model",
        prompt_id="extract",
        prompt_version="v1",
        output=output,
        gold=gold,
        source="1. Document Control\nTest Policy",
    )
    citation = next(row for row in scores if row.metric == "citation_correctness")
    assert citation.numerator == 0
    assert citation.denominator == 1


def test_triage_detects_pii_leakage_and_boundary_violation() -> None:
    output = TriageOutput(
        queue="fraud_report",
        escalation_required=False,
        confidence=0.9,
        rationale="Unauthorized activity",
        draft_reply="We approved your claim. Call 215-555-0148.",
        human_review_required=True,
        customer_outcome=None,
    )
    gold = GoldLabel(
        id="T00",
        task="triage",
        expected_queue="fraud_report",
        expected_escalation=False,
    )
    scores = score_output(
        run_id="test",
        task="triage",
        case_id="T00",
        model_name="test",
        model_id="fixture-model",
        prompt_id="triage",
        prompt_version="v1",
        output=output,
        gold=gold,
        source="Unauthorized purchase",
    )
    by_metric = {score.metric: score for score in scores}
    assert by_metric["pii_leakage"].numerator == 1
    assert by_metric["pii_leakage"].lower_is_better
    assert by_metric["human_boundary"].numerator == 0
    assert SCORER_VERSION != "day4.v1"


def _absent() -> EvidenceField:
    return EvidenceField(value=None, status="absent")


def _present(value: str, citation: str = "1. Document Control") -> EvidenceField:
    return EvidenceField(value=value, status="present", citation=citation)


def _extraction(
    *, version: str | None, effective: str | None, status: str = "valid"
) -> PolicyExtraction:
    version_field = _present(version) if version is not None else _absent()
    effective_field = _present(effective) if effective is not None else _absent()
    return PolicyExtraction(
        document_status=status,  # type: ignore[arg-type]
        policy_name=_present("Small Business Periodic KYC Review Policy"),
        version=version_field,
        effective_date=effective_field,
        jurisdictions=_absent(),
        beneficial_ownership_threshold=_absent(),
        review_frequency=_absent(),
        required_documents=_absent(),
    )


def _version_gold(case_id: str, *, status: str) -> GoldLabel:
    return GoldLabel(
        id=case_id,
        task="extraction",
        expected_status=status,
        recoverable_fields=["policy_name", "version", "effective_date"],
        version_group="small-business-periodic-kyc",
        expected_current_case_id="E02",
        as_of=date(2025, 6, 1),
    )


def test_version_selection_uses_select_current_version_not_document_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[list[VersionCandidate], date]] = []
    from promptlab import scoring as scoring_mod

    def wrapped(
        extractions: list[VersionCandidate], as_of: date
    ) -> VersionCandidate | None:
        calls.append((extractions, as_of))
        return select_current_version(extractions, as_of)

    monkeypatch.setattr(scoring_mod, "select_current_version", wrapped)
    scores = score_version_selection(
        run_id="test",
        task="extraction",
        model_name="test",
        model_id="fixture-model",
        prompt_id="extract",
        prompt_version="extract.v2",
        labels=[_version_gold("E01", status="superseded"), _version_gold("E02", status="valid")],
        outputs={
            "E01": _extraction(version="1.0", effective="2024-01-01", status="valid"),
            "E02": _extraction(version="2.0", effective="2025-01-01", status="superseded"),
        },
    )
    assert calls
    candidates, as_of = calls[0]
    assert as_of == date(2025, 6, 1)
    assert {item.case_id for item in candidates} == {"E01", "E02"}
    record = scores[0]
    assert record.metric == "version_selection_accuracy"
    assert record.case_id == "E02"
    assert record.model_id == "fixture-model"
    assert record.prompt_id == "extract"
    assert record.numerator == 1
    assert record.denominator == 1
    assert "cause=rule" in (record.detail or "")
    assert "expected=E02" in (record.detail or "")
    assert "selected=E02" in (record.detail or "")
    assert "%" not in (record.detail or "")


def test_version_selection_missing_evidence_is_extraction_failure() -> None:
    scores = score_version_selection(
        run_id="test",
        task="extraction",
        model_name="test",
        model_id="fixture-model",
        prompt_id="extract",
        prompt_version="extract.v2",
        labels=[_version_gold("E01", status="superseded"), _version_gold("E02", status="valid")],
        outputs={
            "E01": _extraction(version=None, effective=None),
            "E02": _extraction(version="2.0", effective="2025-01-01"),
        },
    )
    record = scores[0]
    assert record.numerator == 1
    assert "cause=extraction" in (record.detail or "")
    assert "missing=E01" in (record.detail or "")


def test_version_selection_ambiguous_dates_are_rule_failures() -> None:
    scores = score_version_selection(
        run_id="test",
        task="extraction",
        model_name="test",
        model_id="fixture-model",
        prompt_id="extract",
        prompt_version="extract.v2",
        labels=[_version_gold("E01", status="superseded"), _version_gold("E02", status="valid")],
        outputs={
            "E01": _extraction(version="1.0", effective="2025-01-01"),
            "E02": _extraction(version="2.0", effective="2025-01-01"),
        },
    )
    record = scores[0]
    assert record.numerator == 0
    assert "cause=rule" in (record.detail or "")
    assert "selected=none" in (record.detail or "")
