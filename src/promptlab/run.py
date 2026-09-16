"""Final evaluation runner: three tasks against both configured local models."""

from __future__ import annotations

import argparse
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from pydantic import BaseModel

from promptlab.adapters.base import CompletionRequest, CompletionResult, ModelAdapter
from promptlab.adapters.ollama import OllamaAdapter
from promptlab.config import Settings
from promptlab.corpus import Case, GoldLabel, load_cases
from promptlab.prompts import PromptTemplate, load, render_user
from promptlab.records import ScoreRecord, append_record
from promptlab.schemas import OUTPUT_SCHEMAS, StrictModel, TaskName, schema_description
from promptlab.scoring import score_output, score_version_selection
from promptlab.structured import complete_structured
from promptlab.usage import append_record as append_usage

TASKS: tuple[TaskName, ...] = ("summarization", "extraction", "triage")
# Prompts were developed on Mistral. Qwen always runs the same file as a transfer
# test. summarization/extraction use new versions that put Day 3's
# instance-not-schema rule in the registry; summarize.v1, extract.v2, extract.v3,
# and triage.v1/v2 stay on disk unedited.
PROMPT_SOURCE_MODEL = "mistral"
PROMPT_BY_TASK: dict[TaskName, tuple[str, str]] = {
    "summarization": ("summarize", "v2"),
    "extraction": ("extract", "v4"),
    "triage": ("triage", "v1"),
}
MAX_OUTPUT_TOKENS = 512


@dataclass(frozen=True)
class PromptAssignment:
    """Which prompt a task/model pair runs, and whether that run is a transfer."""

    prompt_id: str
    version: str
    transfer: bool

    @property
    def report_label(self) -> str:
        name = f"{self.prompt_id}.{self.version}"
        return f"{name} transfer" if self.transfer else name


def assign_prompt(task: TaskName, model_name: str) -> PromptAssignment:
    """Choose the Day 5 prompt for one task/model pair.

    Each task uses one prompt file for both models. Qwen is labeled as a
    prompt-transfer result of that file. Old measured versions remain as files.
    """
    prompt_id, version = PROMPT_BY_TASK[task]
    return PromptAssignment(
        prompt_id=prompt_id,
        version=version,
        transfer=model_name != PROMPT_SOURCE_MODEL,
    )


class RecordingAdapter:
    """Persist every adapter attempt, including transport retries and repairs."""

    def __init__(self, inner: ModelAdapter) -> None:
        self.provider = inner.provider
        self.model_id = inner.model_id
        self._inner = inner

    def complete(self, request: CompletionRequest, run_id: str) -> CompletionResult:
        result = self._inner.complete(request, run_id)
        for record in result.records:
            append_usage(record, run_id)
        return result


def _parser(settings: Settings) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local two-model prompt comparison")
    parser.add_argument("--run-id", help="Stable identifier for this run")
    parser.add_argument("--task", choices=TASKS)
    parser.add_argument("--model", choices=tuple(settings.models))
    return parser


def _build_request(
    case: Case,
    template: PromptTemplate,
    *,
    task: TaskName,
    schema: type[BaseModel],
    temperature: float,
) -> CompletionRequest:
    return CompletionRequest(
        task=task,
        case_id=case.id,
        prompt_id=template.prompt_id,
        prompt_version=template.version,
        system=template.system,
        user_content=render_user(
            template,
            {"schema_description": schema_description(schema)},
            case.document_text,
        ),
        temperature=temperature,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )


def _score_case(
    *,
    run_id: str,
    task: TaskName,
    case: Case,
    gold: GoldLabel,
    model_name: str,
    model_id: str,
    prompt_id: str,
    prompt_version: str,
    schema: type[StrictModel],
    output: dict[str, object] | None,
) -> tuple[list[ScoreRecord], StrictModel | None]:
    if output is None:
        return [], None
    parsed = schema.model_validate(output)
    return (
        score_output(
            run_id=run_id,
            task=task,
            case_id=case.id,
            model_name=model_name,
            model_id=model_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            output=parsed,
            gold=gold,
            source=case.document_text,
        ),
        parsed,
    )


def main(argv: Sequence[str] | None = None) -> str:
    settings = Settings.from_env()
    args = _parser(settings).parse_args(argv)
    run_id = args.run_id or str(uuid.uuid4())
    selected_tasks: tuple[TaskName, ...] = (
        TASKS if args.task is None else (cast(TaskName, args.task),)
    )
    selected_models = (args.model,) if args.model is not None else tuple(settings.models)

    adapters = {
        name: RecordingAdapter(OllamaAdapter(model_id=settings.models[name].model_id))
        for name in selected_models
    }
    scores_path = Path("runs") / f"{run_id}.scores.jsonl"
    resolved = ",".join(
        f"{name}={settings.models[name].model_id}" for name in selected_models
    )
    print(
        f"run_id={run_id} models={resolved} "
        f"tasks={','.join(selected_tasks)} temperature={settings.temperature}"
    )

    for task in selected_tasks:
        schema = OUTPUT_SCHEMAS[task]
        pairs = load_cases(task)
        for model_name in selected_models:
            assignment = assign_prompt(task, model_name)
            template = load(assignment.prompt_id, assignment.version)
            adapter = adapters[model_name]
            validated: dict[str, StrictModel] = {}
            labels: list[GoldLabel] = []
            for case, gold in pairs:
                labels.append(gold)
                request = _build_request(
                    case,
                    template,
                    task=task,
                    schema=schema,
                    temperature=settings.temperature,
                )
                record = complete_structured(
                    adapter,
                    request,
                    schema,
                    run_id,
                    max_repairs=settings.max_schema_repairs,
                )
                status = "ok" if record.succeeded else "fail"
                print(
                    f"{task} {model_name} {case.id} {status} "
                    f"repairs={record.repairs} prompt={assignment.report_label}"
                )
                case_scores, parsed = _score_case(
                    run_id=run_id,
                    task=task,
                    case=case,
                    gold=gold,
                    model_name=model_name,
                    model_id=adapter.model_id,
                    prompt_id=assignment.prompt_id,
                    prompt_version=assignment.version,
                    schema=schema,
                    output=record.output,
                )
                if parsed is not None:
                    validated[case.id] = parsed
                for score in case_scores:
                    append_record(scores_path, score)
            for score in score_version_selection(
                run_id=run_id,
                task=task,
                model_name=model_name,
                model_id=adapter.model_id,
                prompt_id=assignment.prompt_id,
                prompt_version=assignment.version,
                labels=labels,
                outputs=validated,
            ):
                append_record(scores_path, score)

    if args.task is None and args.model is None:
        _copy_evidence(run_id)

    return run_id


def _copy_evidence(run_id: str) -> None:
    """Persist the unfiltered Day 5 run and scores as the committed evidence files."""
    from promptlab.report import write_comparison_from_evidence

    dest_dir = Path("docs")
    dest_dir.mkdir(parents=True, exist_ok=True)
    run_path = dest_dir / "day5-run.jsonl"
    scores_path = dest_dir / "day5-scores.jsonl"
    run_path.write_text(
        (Path("runs") / f"{run_id}.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    scores_path.write_text(
        (Path("runs") / f"{run_id}.scores.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    write_comparison_from_evidence(
        run_path=run_path,
        scores_path=scores_path,
        report_path=Path("reports") / "comparison.md",
    )


if __name__ == "__main__":
    print(main())
