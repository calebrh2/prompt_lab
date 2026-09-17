from __future__ import annotations

from pathlib import Path

from promptlab.records import ScoreRecord
from promptlab.usage import CallRecord

JOIN_FIELDS = (
    "run_id",
    "case_id",
    "task",
    "model_id",
    "prompt_id",
    "prompt_version",
)


def _join_key(record: object) -> tuple[str, ...]:
    return tuple(str(getattr(record, field)) for field in JOIN_FIELDS)


def _assert_scores_join_calls(scores: list[ScoreRecord], calls: list[CallRecord]) -> None:
    call_keys = {_join_key(record) for record in calls}
    assert call_keys
    for score in scores:
        key = _join_key(score)
        assert all(part for part in key), key
        assert key in call_keys, key


def test_score_record_carries_call_join_fields() -> None:
    for field in JOIN_FIELDS:
        assert field in ScoreRecord.model_fields


def test_committed_day5_scores_join_to_run_records() -> None:
    calls = [
        CallRecord.model_validate_json(line)
        for line in Path("docs/day5-run.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    scores = [
        ScoreRecord.model_validate_json(line)
        for line in Path("docs/day5-scores.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    run_ids = {row.run_id for row in calls} | {row.run_id for row in scores}
    assert len(run_ids) == 1
    _assert_scores_join_calls(scores, calls)
