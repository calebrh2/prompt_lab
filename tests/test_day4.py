from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from promptlab.adapters.base import CompletionRequest, CompletionResult
from promptlab.adapters.ollama import OllamaAdapter
from promptlab.config import Settings
from promptlab.day4 import MODEL_NAME, TEMPERATURE, load_cases, main
from promptlab.prompts import load
from promptlab.schemas import TriageOutput, TriageOutputWithAnalysis
from promptlab.usage import CallRecord


def _stub_record(request: CompletionRequest, run_id: str, model_id: str) -> CallRecord:
    return CallRecord(
        record_id="00000000-0000-4000-8000-000000000001",
        run_id=run_id,
        timestamp=datetime.now(UTC),
        provider="ollama",
        model_id=model_id,
        task=request.task,
        case_id=request.case_id,
        prompt_id=request.prompt_id,
        prompt_version=request.prompt_version,
        attempt=1,
        temperature=request.temperature,
        max_output_tokens=request.max_output_tokens,
        input_tokens=1,
        output_tokens=1,
        cached_input_tokens=None,
        latency_ms=1,
        cost_usd=0.0,
        stop_reason="stop",
        error_type=None,
        response_text="ok",
    )


def _triage_json(*, with_analysis: bool) -> str:
    payload: dict[str, object] = {
        "queue": "card_dispute",
        "escalation_required": False,
        "confidence": 0.8,
        "rationale": "recognized duplicate charge",
        "draft_reply": "A specialist will review this request.",
        "human_review_required": True,
        "customer_outcome": None,
    }
    if with_analysis:
        payload["analysis"] = "Routing from a recognized duplicate charge."
    return json.dumps(payload)


def test_load_cases_returns_all_twelve() -> None:
    cases = load_cases()
    assert [case["id"] for case in cases] == [f"T{i:02d}" for i in range(1, 13)]
    assert all(case["task"] == "triage" and case["source"] for case in cases)


def test_triage_v1_does_not_request_analysis() -> None:
    template = load("triage", "v1")
    assert "analysis" not in template.system.lower()
    assert "analysis" not in template.user_template.lower()


def test_triage_v2_requests_analysis() -> None:
    template = load("triage", "v2")
    assert "analysis" in template.system.lower()
    assert "TriageOutputWithAnalysis" in template.system
    extra = set(TriageOutputWithAnalysis.model_fields) - set(TriageOutput.model_fields)
    assert extra == {"analysis"}
    assert not hasattr(__import__("promptlab.schemas", fromlist=["schemas"]), "TriageDecision")


def test_main_runs_both_prompt_versions_on_one_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    calls: list[tuple[str, str, str, float]] = []

    def fake_complete(
        self: OllamaAdapter, request: CompletionRequest, run_id: str
    ) -> CompletionResult:
        calls.append((self.model_id, request.prompt_version, request.case_id, request.temperature))
        assert request.task == "triage"
        assert request.temperature == TEMPERATURE
        assert request.prompt_id == "triage"
        assert "{document_text}" not in request.user_content
        assert "<customer_message>" in request.user_content
        assert "</customer_message>" in request.user_content
        assert "card_dispute" in request.system
        text = _triage_json(with_analysis=request.prompt_version == "v2")
        record = _stub_record(request, run_id, self.model_id)
        return CompletionResult(succeeded=True, text=text, error_type=None, records=[record])

    monkeypatch.setattr(OllamaAdapter, "complete", fake_complete)
    run_id = main()
    UUID(run_id)

    settings = Settings.from_env()
    model_id = settings.models[MODEL_NAME].model_id
    expected = [
        (model_id, version, f"T{i:02d}", 0.0)
        for version in ("v1", "v2")
        for i in range(1, 13)
    ]
    assert calls == expected

    usage_path = tmp_path / "runs" / f"{run_id}.jsonl"
    output_path = tmp_path / "runs" / f"{run_id}.outputs.jsonl"
    docs_run = tmp_path / "docs" / "day4-run.jsonl"
    docs_scores = tmp_path / "docs" / "day4-scores.jsonl"
    usage = [json.loads(line) for line in usage_path.read_text(encoding="utf-8").splitlines()]
    outputs = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    scores = [json.loads(line) for line in docs_scores.read_text(encoding="utf-8").splitlines()]
    copied = [json.loads(line) for line in docs_run.read_text(encoding="utf-8").splitlines()]

    assert len(usage) == 24
    assert len(outputs) == 24
    assert copied == usage
    assert {row["run_id"] for row in usage} == {run_id}
    assert {row["run_id"] for row in scores} == {run_id}
    assert all(row["task"] == "triage" for row in outputs)
    assert all(row["model_id"] == model_id for row in outputs)
    assert all(row["succeeded"] is True for row in outputs)
    assert {row["prompt_version"] for row in outputs[:12]} == {"v1"}
    assert {row["prompt_version"] for row in outputs[12:]} == {"v2"}
    assert {row["metric"] for row in scores} >= {
        "queue_accuracy",
        "escalation_accuracy",
        "missed_escalation",
        "unnecessary_escalation",
        "human_boundary",
    }
