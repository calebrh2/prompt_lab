"""Day 4 triage run: compare prompt versions v1 and v2 on one local model."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from promptlab.adapters.base import CompletionRequest, CompletionResult, ModelAdapter
from promptlab.adapters.ollama import OllamaAdapter
from promptlab.config import PROJECT_ROOT, Settings
from promptlab.prompts import PromptTemplate, load, render_user
from promptlab.records import OutputRecord, ScoreRecord, append_record
from promptlab.schemas import TaskName, TriageOutput, TriageOutputWithAnalysis
from promptlab.scoring import score_triage
from promptlab.structured import complete_structured
from promptlab.usage import append_record as append_usage

MODEL_NAME = "mistral"
TEMPERATURE = 0.0
MAX_OUTPUT_TOKENS = 512
PROMPT_ID = "triage"
TASK: TaskName = "triage"
CASES_FILE = "triage.jsonl"
VERSIONS: tuple[tuple[str, type[BaseModel]], ...] = (
    ("v1", TriageOutput),
    ("v2", TriageOutputWithAnalysis),
)


class RecordingAdapter:
    """Persist every adapter attempt, including semantic repairs."""

    def __init__(self, inner: ModelAdapter) -> None:
        self.provider = inner.provider
        self.model_id = inner.model_id
        self._inner = inner

    def complete(self, request: CompletionRequest, run_id: str) -> CompletionResult:
        result = self._inner.complete(request, run_id)
        for record in result.records:
            append_usage(record, run_id)
        return result


def load_cases() -> list[dict[str, str]]:
    path = PROJECT_ROOT / "cases" / CASES_FILE
    cases: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        cases.append(
            {
                "id": str(raw["id"]),
                "task": str(raw["task"]),
                "source": str(raw["source"]),
            }
        )
    return cases


def load_gold() -> dict[str, dict[str, Any]]:
    path = PROJECT_ROOT / "cases" / "gold" / "triage.jsonl"
    gold: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        gold[str(raw["id"])] = raw
    return gold


def build_request(case: dict[str, str], template: PromptTemplate) -> CompletionRequest:
    return CompletionRequest(
        task=TASK,
        case_id=case["id"],
        prompt_id=template.prompt_id,
        prompt_version=template.version,
        system=template.system,
        user_content=render_user(template, variables={}, untrusted=case["source"]),
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )


def run_case(
    adapter: ModelAdapter,
    request: CompletionRequest,
    schema: type[BaseModel],
    *,
    run_id: str,
    max_repairs: int,
) -> OutputRecord:
    return complete_structured(
        adapter,
        request,
        schema,
        run_id,
        max_repairs=max_repairs,
    )


def _write_scores(path: Path, records: list[ScoreRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json() + "\n")


def _copy_usage(run_id: str, dest: Path) -> None:
    src = Path("runs") / f"{run_id}.jsonl"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> str:
    settings = Settings.from_env()
    model = settings.models[MODEL_NAME]
    adapter = RecordingAdapter(OllamaAdapter(model_id=model.model_id))
    run_id = str(uuid.uuid4())
    print(f"run_id={run_id} model={model.model_id} temperature={TEMPERATURE}")

    cases = load_cases()
    gold = load_gold()
    scores: list[ScoreRecord] = []

    for prompt_version, schema in VERSIONS:
        template = load(PROMPT_ID, prompt_version)
        for case in cases:
            request = build_request(case, template)
            record = run_case(
                adapter,
                request,
                schema,
                run_id=run_id,
                max_repairs=settings.max_schema_repairs,
            )
            status = "ok" if record.succeeded else "fail"
            print(f"{prompt_version} {request.case_id} {status} repairs={record.repairs}")
            case_scores = score_triage(
                run_id=run_id,
                task=TASK,
                case_id=case["id"],
                model_name=MODEL_NAME,
                prompt_version=prompt_version,
                gold=gold[case["id"]],
                output=record.output,
            )
            scores.extend(case_scores)
            for score in case_scores:
                append_record(Path("runs") / f"{run_id}.scores.jsonl", score)

    _copy_usage(run_id, Path("docs") / "day4-run.jsonl")
    _write_scores(Path("docs") / "day4-scores.jsonl", scores)
    return run_id


if __name__ == "__main__":
    print(main())
