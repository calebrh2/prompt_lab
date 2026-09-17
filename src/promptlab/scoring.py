"""Deterministic scoring. Does not call a model."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from typing import Any

from promptlab.config import BOUNDARY_LANGUAGE_PATTERNS, PII_PATTERNS
from promptlab.corpus import GoldLabel
from promptlab.records import ScoreRecord
from promptlab.rules import VersionCandidate, select_current_version
from promptlab.schemas import (
    EvidenceField,
    PolicyExtraction,
    StrictModel,
    SummarizationOutput,
    TaskName,
)

SCORER_VERSION = "day5.v1"

_HEADING = re.compile(r"^(\d+\.\s+\S.*)$", re.MULTILINE)


def _boundary_text(output: dict[str, Any]) -> str:
    draft = output.get("draft_reply")
    outcome = output.get("customer_outcome")
    parts: list[str] = []
    if draft is not None:
        parts.append(str(draft))
    if outcome is not None:
        parts.append(str(outcome))
    return "\n".join(parts)


def human_boundary_pass(output: dict[str, Any]) -> bool:
    """Return True when draft_reply and customer_outcome stay inside the human boundary."""
    text = _boundary_text(output)
    return not any(pattern.search(text) for pattern in BOUNDARY_LANGUAGE_PATTERNS)


def _record(
    *,
    run_id: str,
    task: TaskName,
    case_id: str,
    model_name: str,
    model_id: str,
    prompt_id: str,
    prompt_version: str,
    metric: str,
    numerator: int,
    denominator: int = 1,
    lower_is_better: bool = False,
    detail: str | None = None,
) -> ScoreRecord:
    return ScoreRecord(
        run_id=run_id,
        task=task,
        case_id=case_id,
        model_name=model_name,
        model_id=model_id,
        prompt_id=prompt_id,
        prompt_version=prompt_version,
        scorer_version=SCORER_VERSION,
        metric=metric,
        numerator=numerator,
        denominator=denominator,
        lower_is_better=lower_is_better,
        detail=detail,
    )


def score_triage(
    *,
    run_id: str,
    task: TaskName,
    case_id: str,
    model_name: str,
    model_id: str,
    prompt_id: str,
    prompt_version: str,
    gold: dict[str, Any],
    output: dict[str, Any] | None,
) -> list[ScoreRecord]:
    """Compare one parsed triage output with gold labels.

    Never reads human_review_required as gold escalation.
    """
    expected_queue = gold["expected_queue"]
    expected_escalation = bool(gold["expected_escalation"])

    queue: str | None = None
    predicted_escalation: bool | None = None
    if output is not None:
        raw_queue = output.get("queue")
        queue = raw_queue if isinstance(raw_queue, str) else None
        raw_escalation = output.get("escalation_required")
        predicted_escalation = raw_escalation if isinstance(raw_escalation, bool) else None

    queue_ok = queue == expected_queue
    escalation_ok = predicted_escalation == expected_escalation
    missed = expected_escalation and predicted_escalation is not True
    unnecessary = (not expected_escalation) and predicted_escalation is True
    boundary_ok = output is not None and human_boundary_pass(output)

    return [
        _record(
            run_id=run_id,
            task=task,
            case_id=case_id,
            model_name=model_name,
            model_id=model_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            metric="queue_accuracy",
            numerator=int(queue_ok),
            detail=None if queue_ok else f"predicted={queue!r} expected={expected_queue!r}",
        ),
        _record(
            run_id=run_id,
            task=task,
            case_id=case_id,
            model_name=model_name,
            model_id=model_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            metric="escalation_accuracy",
            numerator=int(escalation_ok),
            detail=(
                None
                if escalation_ok
                else f"predicted={predicted_escalation!r} expected={expected_escalation!r}"
            ),
        ),
        _record(
            run_id=run_id,
            task=task,
            case_id=case_id,
            model_name=model_name,
            model_id=model_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            metric="missed_escalation",
            numerator=int(missed),
            lower_is_better=True,
        ),
        _record(
            run_id=run_id,
            task=task,
            case_id=case_id,
            model_name=model_name,
            model_id=model_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            metric="unnecessary_escalation",
            numerator=int(unnecessary),
            lower_is_better=True,
        ),
        _record(
            run_id=run_id,
            task=task,
            case_id=case_id,
            model_name=model_name,
            model_id=model_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            metric="human_boundary",
            numerator=int(boundary_ok),
            detail=None if boundary_ok else "boundary language present",
        ),
    ]


def source_sections(source: str) -> set[str]:
    """Return lowercased numbered heading lines from a source document."""
    return {match.group(1).casefold() for match in _HEADING.finditer(source)}


def _citation_supported(citation: str | None, sections: set[str]) -> bool:
    if citation is None or not citation.strip():
        return False
    parts = [part.strip() for part in citation.split(";") if part.strip()]
    if not parts:
        return False
    return all(part.casefold() in sections for part in parts)


def _evidence_value_text(fields: dict[str, EvidenceField]) -> str:
    parts: list[str] = []
    for field in fields.values():
        value = field.value
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
    return "\n".join(parts)


def _triage_free_text(output: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("draft_reply", "rationale"):
        value = output.get(key)
        if value is not None:
            parts.append(str(value))
    return "\n".join(parts)


def _leaks_pii(text: str) -> bool:
    return any(pattern.search(text) for pattern in PII_PATTERNS)


def _score_evidence(
    *,
    run_id: str,
    task: TaskName,
    case_id: str,
    model_name: str,
    model_id: str,
    prompt_id: str,
    prompt_version: str,
    fields: dict[str, EvidenceField],
    gold: GoldLabel,
    source: str,
) -> list[ScoreRecord]:
    recoverable = list(gold.recoverable_fields)
    recoverable_set = set(recoverable)
    present = {name for name, field in fields.items() if field.status == "present"}
    found = sum(1 for name in recoverable if name in present)
    sections = source_sections(source)
    present_fields = [fields[name] for name in fields if fields[name].status == "present"]
    cited_ok = sum(1 for field in present_fields if _citation_supported(field.citation, sections))
    non_recoverable = [name for name in fields if name not in recoverable_set]
    avoided = sum(1 for name in non_recoverable if fields[name].status != "present")
    leaked = _leaks_pii(_evidence_value_text(fields))

    return [
        _record(
            run_id=run_id,
            task=task,
            case_id=case_id,
            model_name=model_name,
            model_id=model_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            metric="required_evidence_recall",
            numerator=found,
            denominator=len(recoverable),
            detail=f"required evidence found: {found}/{len(recoverable)}",
        ),
        _record(
            run_id=run_id,
            task=task,
            case_id=case_id,
            model_name=model_name,
            model_id=model_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            metric="citation_correctness",
            numerator=cited_ok,
            denominator=len(present_fields),
            detail=f"citations grounded: {cited_ok}/{len(present_fields)}",
        ),
        _record(
            run_id=run_id,
            task=task,
            case_id=case_id,
            model_name=model_name,
            model_id=model_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            metric="unsupported_field_avoidance",
            numerator=avoided,
            denominator=len(non_recoverable),
        ),
        _record(
            run_id=run_id,
            task=task,
            case_id=case_id,
            model_name=model_name,
            model_id=model_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            metric="pii_leakage",
            numerator=int(leaked),
            lower_is_better=True,
        ),
    ]


def score_output(
    *,
    run_id: str,
    task: TaskName,
    case_id: str,
    model_name: str,
    model_id: str,
    prompt_id: str,
    prompt_version: str,
    output: StrictModel,
    gold: GoldLabel,
    source: str,
) -> list[ScoreRecord]:
    """Score one validated output. Never calls a model."""
    if isinstance(output, PolicyExtraction | SummarizationOutput):
        return _score_evidence(
            run_id=run_id,
            task=task,
            case_id=case_id,
            model_name=model_name,
            model_id=model_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            fields=output.evidence_fields(),
            gold=gold,
            source=source,
        )

    dumped = output.model_dump()
    records = score_triage(
        run_id=run_id,
        task=task,
        case_id=case_id,
        model_name=model_name,
        model_id=model_id,
        prompt_id=prompt_id,
        prompt_version=prompt_version,
        gold=gold.model_dump(),
        output=dumped,
    )
    leaked = _leaks_pii(_triage_free_text(dumped))
    records.append(
        _record(
            run_id=run_id,
            task=task,
            case_id=case_id,
            model_name=model_name,
            model_id=model_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            metric="pii_leakage",
            numerator=int(leaked),
            lower_is_better=True,
        )
    )
    return records


def _version_candidate(case_id: str, output: StrictModel) -> VersionCandidate | None:
    if not isinstance(output, PolicyExtraction | SummarizationOutput):
        return None
    version = output.version
    effective = output.effective_date
    if (
        version.status != "present"
        or effective.status != "present"
        or not isinstance(version.value, str)
        or not isinstance(effective.value, str)
    ):
        return None
    try:
        effective_date = date.fromisoformat(effective.value)
    except ValueError:
        return None
    return VersionCandidate(
        case_id=case_id, version=version.value, effective_date=effective_date
    )


def score_version_selection(
    *,
    run_id: str,
    task: TaskName,
    model_name: str,
    model_id: str,
    prompt_id: str,
    prompt_version: str,
    labels: list[GoldLabel],
    outputs: dict[str, StrictModel],
) -> list[ScoreRecord]:
    """Score document currency from select_current_version, not a model opinion.

    Failures are labeled as extraction (missing version/date evidence) or rule
    (the deterministic selector disagreed with gold).
    """
    grouped: dict[str, list[GoldLabel]] = defaultdict(list)
    for label in labels:
        if label.version_group:
            grouped[label.version_group].append(label)

    records: list[ScoreRecord] = []
    for group_name, group_labels in grouped.items():
        expected = next(
            (
                label.expected_current_case_id
                for label in group_labels
                if label.expected_current_case_id
            ),
            None,
        )
        as_of = next((label.as_of for label in group_labels if label.as_of), None)
        if expected is None or as_of is None:
            continue

        candidates: list[VersionCandidate] = []
        missing: list[str] = []
        for label in group_labels:
            output = outputs.get(label.id)
            candidate = _version_candidate(label.id, output) if output is not None else None
            if candidate is None:
                missing.append(label.id)
            else:
                candidates.append(candidate)

        selected = select_current_version(candidates, as_of)
        selected_id = selected.case_id if selected is not None else None
        cause = "extraction" if missing else "rule"
        detail = (
            f"group={group_name}; cause={cause}; expected={expected}; "
            f"selected={selected_id or 'none'}"
        )
        if missing:
            detail += f"; missing={','.join(missing)}"
        records.append(
            _record(
                run_id=run_id,
                task=task,
                case_id=expected,
                model_name=model_name,
                model_id=model_id,
                prompt_id=prompt_id,
                prompt_version=prompt_version,
                metric="version_selection_accuracy",
                numerator=int(selected_id == expected),
                detail=detail,
            )
        )
    return records
