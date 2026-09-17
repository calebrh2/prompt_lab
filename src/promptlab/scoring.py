"""Deterministic Day 4 scoring. Does not call a model."""

from __future__ import annotations

from typing import Any

from promptlab.config import BOUNDARY_LANGUAGE_PATTERNS
from promptlab.records import ScoreRecord
from promptlab.schemas import TaskName

SCORER_VERSION = "day4.v1"


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
    prompt_version: str,
    metric: str,
    numerator: int,
    lower_is_better: bool = False,
    detail: str | None = None,
) -> ScoreRecord:
    return ScoreRecord(
        run_id=run_id,
        task=task,
        case_id=case_id,
        model_name=model_name,
        prompt_version=prompt_version,
        scorer_version=SCORER_VERSION,
        metric=metric,
        numerator=numerator,
        denominator=1,
        lower_is_better=lower_is_better,
        detail=detail,
    )


def score_triage(
    *,
    run_id: str,
    task: TaskName,
    case_id: str,
    model_name: str,
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
            prompt_version=prompt_version,
            metric="human_boundary",
            numerator=int(boundary_ok),
            detail=None if boundary_ok else "boundary language present",
        ),
    ]
