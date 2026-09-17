from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from promptlab.adapters.base import CompletionRequest, CompletionResult
from promptlab.adapters.ollama import OllamaAdapter
from promptlab.config import Settings
from promptlab.prompts import PROMPT_DIR, load
from promptlab.records import ScoreRecord
from promptlab.run import (
    PROMPT_BY_TASK,
    PROMPT_SOURCE_MODEL,
    TASKS,
    assign_prompt,
    main,
)
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


def _present(value: str) -> dict[str, str]:
    return {"value": value, "status": "present", "citation": "1. Document Control"}


def _summarization_json() -> str:
    return json.dumps(
        {
            "document_status": "valid",
            "title": _present("title"),
            "version": _present("1.0"),
            "effective_date": _present("2025-01-01"),
            "purpose": _present("purpose"),
            "required_steps": _present("steps"),
            "exceptions": _present("none"),
        }
    )


def _extraction_json() -> str:
    return json.dumps(
        {
            "document_status": "valid",
            "policy_name": _present("policy"),
            "version": _present("1.0"),
            "effective_date": _present("2025-01-01"),
            "jurisdictions": _present("PA"),
            "beneficial_ownership_threshold": _present("25 percent"),
            "review_frequency": _present("24 months"),
            "required_documents": _present("formation documents"),
        }
    )


def _triage_json() -> str:
    return json.dumps(
        {
            "queue": "card_dispute",
            "escalation_required": False,
            "confidence": 0.8,
            "rationale": "recognized duplicate charge",
            "draft_reply": "A specialist will review this request.",
            "human_review_required": True,
            "customer_outcome": None,
        }
    )


def _payload(task: str) -> str:
    if task == "summarization":
        return _summarization_json()
    if task == "extraction":
        return _extraction_json()
    return _triage_json()


def _install_stub(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[str, str, str, str, str, float]]:
    calls: list[tuple[str, str, str, str, str, float]] = []

    def fake_complete(
        self: OllamaAdapter, request: CompletionRequest, run_id: str
    ) -> CompletionResult:
        calls.append(
            (
                self.model_id,
                request.task,
                request.prompt_id,
                request.prompt_version,
                request.case_id,
                request.temperature,
            )
        )
        assert "{document_text}" not in request.user_content
        assert "{schema_description}" not in request.user_content
        if request.task == "triage":
            assert "<customer_message>" in request.user_content
        else:
            assert "<document>" in request.user_content
        record = _stub_record(request, run_id, self.model_id)
        return CompletionResult(
            succeeded=True,
            text=_payload(request.task),
            error_type=None,
            records=[record],
        )

    monkeypatch.setattr(OllamaAdapter, "complete", fake_complete)
    return calls


def test_run_py_does_not_call_ollama_directly() -> None:
    source = Path("src/promptlab/run.py").read_text(encoding="utf-8")
    assert "httpx" not in source
    assert "/api/generate" not in source
    assert "complete_structured" in source
    assert "from promptlab.prompts import" in source
    assert "OllamaAdapter" in source


def test_main_runs_three_tasks_on_both_models(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    calls = _install_stub(monkeypatch)
    run_id = main([])
    UUID(run_id)

    settings = Settings.from_env()
    model_ids = [settings.models[name].model_id for name in settings.models]
    expected_prompts = {
        "summarization": ("summarize", "v2"),
        "extraction": ("extract", "v4"),
        "triage": ("triage", "v1"),
    }
    expected: list[tuple[str, str, str, str, str, float]] = []
    for task in TASKS:
        prompt_id, prompt_version = expected_prompts[task]
        prefix = {"summarization": "S", "extraction": "E", "triage": "T"}[task]
        for model_id in model_ids:
            for index in range(1, 13):
                expected.append(
                    (
                        model_id,
                        task,
                        prompt_id,
                        prompt_version,
                        f"{prefix}{index:02d}",
                        0.0,
                    )
                )
    assert calls == expected
    assert len(calls) == 3 * len(model_ids) * 12

    usage = [
        json.loads(line)
        for line in (tmp_path / "runs" / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    outputs = [
        json.loads(line)
        for line in (tmp_path / "runs" / f"{run_id}.outputs.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert len(usage) == 72
    assert len(outputs) == 72
    assert {row["provider"] for row in usage} == {"ollama"}
    assert {row["model_id"] for row in usage} == set(model_ids)
    assert {row["task"] for row in outputs} == set(TASKS)
    assert all(row["succeeded"] is True for row in outputs)
    assert all(row["cost_usd"] == 0.0 for row in usage)

    scores = [
        ScoreRecord.model_validate_json(line)
        for line in (tmp_path / "runs" / f"{run_id}.scores.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    call_records = [CallRecord.model_validate(row) for row in usage]
    join_fields = (
        "run_id",
        "case_id",
        "task",
        "model_id",
        "prompt_id",
        "prompt_version",
    )
    call_keys = {
        tuple(str(getattr(record, field)) for field in join_fields) for record in call_records
    }
    assert scores
    for score in scores:
        key = tuple(str(getattr(score, field)) for field in join_fields)
        assert key in call_keys


def test_task_filter_runs_one_task_on_both_models(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    calls = _install_stub(monkeypatch)
    run_id = main(["--task", "extraction"])
    UUID(run_id)
    assert len(calls) == 24
    assert {call[1] for call in calls} == {"extraction"}
    assert {call[2] for call in calls} == {"extract"}
    assert {call[3] for call in calls} == {"v4"}


def test_model_filter_runs_all_tasks_on_one_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    calls = _install_stub(monkeypatch)
    settings = Settings.from_env()
    model_name = next(iter(settings.models))
    model_id = settings.models[model_name].model_id
    run_id = main(["--model", model_name])
    UUID(run_id)
    assert len(calls) == 36
    assert {call[0] for call in calls} == {model_id}
    assert {call[1] for call in calls} == set(TASKS)


def test_each_task_uses_a_transfer_test_not_an_adapted_prompt() -> None:
    settings = Settings.from_env()
    assert PROMPT_SOURCE_MODEL in settings.models
    assert PROMPT_BY_TASK == {
        "summarization": ("summarize", "v2"),
        "extraction": ("extract", "v4"),
        "triage": ("triage", "v1"),
    }
    for task, (prompt_id, version) in PROMPT_BY_TASK.items():
        source = assign_prompt(task, PROMPT_SOURCE_MODEL)
        assert source.prompt_id == prompt_id
        assert source.version == version
        assert source.transfer is False
        assert source.report_label == f"{prompt_id}.{version}"
        for model_name in settings.models:
            if model_name == PROMPT_SOURCE_MODEL:
                continue
            transferred = assign_prompt(task, model_name)
            assert transferred.prompt_id == source.prompt_id
            assert transferred.version == source.version
            assert transferred.transfer is True
            assert transferred.report_label == f"{prompt_id}.{version} transfer"


def test_measured_day5_prompt_files_remain_loadable() -> None:
    for prompt_id, version in PROMPT_BY_TASK.values():
        template = load(prompt_id, version)
        assert template.prompt_id == prompt_id
        assert template.version == version
        assert (PROMPT_DIR / f"{prompt_id}.{version}.md").is_file()
    preserved = (
        "summarize.v1.md",
        "extract.v1.md",
        "extract.v2.md",
        "extract.v3.md",
        "triage.v1.md",
        "triage.v2.md",
        "baseline.v0.md",
    )
    for filename in preserved:
        assert (PROMPT_DIR / filename).is_file()


def test_adapted_prompt_versions_keep_instance_not_schema_in_the_registry() -> None:
    summarize = load("summarize", "v2")
    extract = load("extract", "v4")
    for template in (summarize, extract):
        assert "JSON instance" in template.system
        assert "$defs" in template.system
        assert "JSON Schema" in template.system
        assert "{schema_description}" in template.user_template
        assert "{document_text}" in template.user_template
    assert "SummarizationOutput" in summarize.system
    assert "PolicyExtraction" in extract.system
    assert "Northglass" in extract.user_template


def test_prior_prompt_versions_were_not_replaced() -> None:
    v1 = (PROMPT_DIR / "summarize.v1.md").read_text(encoding="utf-8")
    v2 = (PROMPT_DIR / "extract.v2.md").read_text(encoding="utf-8")
    assert not v1.lstrip().startswith("## System")
    assert not v2.lstrip().startswith("## System")
    assert "$defs" not in v1
    assert "$defs" not in v2


def test_runner_records_actual_versions_and_labels_transfer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    _install_stub(monkeypatch)
    run_id = main([])
    captured = capsys.readouterr().out
    settings = Settings.from_env()

    for task, (prompt_id, version) in PROMPT_BY_TASK.items():
        source_label = f"{prompt_id}.{version}"
        transfer_label = f"{source_label} transfer"
        source_lines = [
            line
            for line in captured.splitlines()
            if line.startswith(f"{task} {PROMPT_SOURCE_MODEL} ")
            and f"prompt={source_label}" in line
            and "transfer" not in line
        ]
        assert source_lines
        for model_name in settings.models:
            if model_name == PROMPT_SOURCE_MODEL:
                continue
            transfer_lines = [
                line
                for line in captured.splitlines()
                if line.startswith(f"{task} {model_name} ")
                and f"prompt={transfer_label}" in line
            ]
            assert transfer_lines

    usage = [
        json.loads(line)
        for line in (tmp_path / "runs" / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    scores = [
        json.loads(line)
        for line in (tmp_path / "runs" / f"{run_id}.scores.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    recorded_versions = {row["prompt_version"] for row in usage} | {
        row["prompt_version"] for row in scores
    }
    assert recorded_versions == {"v1", "v2", "v4"}
    assert all("transfer" not in row["prompt_version"] for row in usage)
    assert all("transfer" not in row["prompt_version"] for row in scores)
