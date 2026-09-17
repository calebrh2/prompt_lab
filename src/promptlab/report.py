"""Reporting for the Week 2 model-comparison lab.

The reporting layer consumes recorded usage, call, output, and score objects.
It does not rescore model output and it does not call an LLM.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from statistics import median
from typing import Any

from promptlab.records import OutputRecord, ScoreRecord, UsageRecord, load_records
from promptlab.schemas import TaskName
from promptlab.usage import CallRecord, round_trip_latencies

_TASK_ORDER: tuple[TaskName, ...] = ("summarization", "extraction", "triage")

_ConfigKey = tuple[str, str, str]  # task, model_name, prompt_version


def _key(record: Any) -> _ConfigKey:
    return (
        str(record.task),
        str(record.model_name),
        str(record.prompt_version),
    )


def _for_run(records: Sequence[Any], run_id: str) -> list[Any]:
    return [record for record in records if str(record.run_id) == run_id]


def _fmt_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.1f}"


def _aggregate_scores(
    records: Sequence[ScoreRecord],
) -> dict[str, tuple[int, int, bool | None]]:
    """Aggregate compatible score counts without averaging percentages."""

    grouped: dict[str, list[ScoreRecord]] = defaultdict(list)
    for record in records:
        grouped[str(record.metric)].append(record)

    result: dict[str, tuple[int, int, bool | None]] = {}

    for metric, rows in sorted(grouped.items()):
        numerator = sum(int(row.numerator) for row in rows)
        denominator = sum(int(row.denominator) for row in rows)

        directions = {
            bool(value)
            for value in (getattr(row, "lower_is_better", None) for row in rows)
            if value is not None
        }
        lower_is_better: bool | None
        if len(directions) == 1:
            lower_is_better = next(iter(directions))
        else:
            lower_is_better = None

        result[metric] = (numerator, denominator, lower_is_better)

    return result


def _metric_text(records: Sequence[ScoreRecord]) -> str:
    metrics = _aggregate_scores(records)
    if not metrics:
        return "—"

    rendered: list[str] = []
    for metric, (numerator, denominator, lower_is_better) in metrics.items():
        suffix = " ↓" if lower_is_better else ""
        rendered.append(f"{metric}: {numerator}/{denominator}{suffix}")

    return "<br>".join(rendered)


def _usage_summary(
    records: Sequence[UsageRecord],
) -> tuple[str, str, str, str, str, str]:
    """Return token, latency, observation, and retry summaries."""

    if not records:
        return "—", "—", "—", "—", "0", "0"

    prompt_tokens = sum(int(getattr(row, "prompt_tokens", 0) or 0) for row in records)
    completion_tokens = sum(
        int(getattr(row, "completion_tokens", 0) or 0) for row in records
    )

    latencies = round_trip_latencies(records)

    if latencies:
        median_latency = f"{_fmt_number(float(median(latencies)))} ms"
        max_latency = f"{_fmt_number(float(max(latencies)))} ms"
    else:
        median_latency = "—"
        max_latency = "—"

    # A semantic repair is a separate model request and should not also be
    # reported as a transport retry merely because it has an attempt number.
    repair_attempts = sum(
        1
        for row in records
        if str(getattr(row, "kind", "")).lower() == "repair"
    )

    retry_attempts = sum(
        1
        for row in records
        if int(getattr(row, "attempt", 1) or 1) > 1
        and str(getattr(row, "kind", "")).lower() != "repair"
    )

    return (
        str(prompt_tokens),
        str(completion_tokens),
        median_latency,
        max_latency,
        str(len(latencies)),
        str(retry_attempts),
    )


def _output_summary(
    records: Sequence[OutputRecord],
) -> tuple[str, str, str]:
    if not records:
        return "0/0", "0/0", "0"

    total = len(records)
    succeeded = sum(1 for row in records if bool(row.succeeded))
    repairs_needed = sum(
        1 for row in records if int(getattr(row, "repairs", 0) or 0) > 0
    )
    failures = total - succeeded

    return (
        f"{succeeded}/{total}",
        f"{repairs_needed}/{total}",
        str(failures),
    )


def _all_config_keys(
    usage: Sequence[UsageRecord],
    outputs: Sequence[OutputRecord],
    scores: Sequence[ScoreRecord],
) -> list[_ConfigKey]:
    keys = {_key(row) for row in usage}
    keys.update(_key(row) for row in outputs)
    keys.update(_key(row) for row in scores)
    return sorted(keys)


def _write_report(
    *,
    run_id: str,
    usage: Sequence[UsageRecord],
    outputs: Sequence[OutputRecord],
    scores: Sequence[ScoreRecord],
    report_path: Path,
) -> None:
    lines: list[str] = [
        "# Model Comparison",
        "",
        f"Run ID: `{run_id}`",
        "",
        "Counts are reported with their denominators. "
        "Latency uses median and maximum rather than mean.",
        "",
    ]

    keys = _all_config_keys(usage, outputs, scores)
    tasks = sorted({task for task, _model, _prompt in keys})

    if not tasks:
        lines.extend(
            [
                "No records were supplied for this run.",
                "",
            ]
        )

    for task in tasks:
        lines.extend(
            [
                f"## {task.title()}",
                "",
                "| Model | Prompt | Valid outputs | Metrics | Input tokens | "
                "Output tokens | Median latency | Max latency | n | "
                "Repairs | Retries | Final failures |",
                "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | "
                "---: | ---: | ---: |",
            ]
        )

        task_keys = [key for key in keys if key[0] == task]

        for key in task_keys:
            _task, model_name, prompt_version = key

            u = [row for row in usage if _key(row) == key]
            o = [row for row in outputs if _key(row) == key]
            s = [row for row in scores if _key(row) == key]

            (
                input_tokens,
                output_tokens,
                median_latency,
                max_latency,
                n,
                retries,
            ) = _usage_summary(u)

            valid_outputs, repairs, failures = _output_summary(o)
            metric_text = _metric_text(s)

            lines.append(
                "| "
                f"{model_name} | {prompt_version} | {valid_outputs} | "
                f"{metric_text} | {input_tokens} | {output_tokens} | "
                f"{median_latency} | {max_latency} | {n} | {repairs} | "
                f"{retries} | {failures} |"
            )

        lines.append("")

    lines.extend(
        [
            "## Limits",
            "",
            "- The Week 2 comparison uses a small fixed case set; report counts rather "
            "than treating one-case differences as precise production estimates.",
            "- A row measures the model together with the prompt version shown in that row.",
            "- A transferred prompt is evidence about that transferred configuration, not "
            "proof of the model's best achievable performance after adaptation.",
            "- Local Ollama provider/API charge is `$0.00`; token usage and latency still "
            "represent real operational work.",
            "",
        ]
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def _write_decision_scaffold(
    *,
    run_id: str,
    models: Sequence[str],
    usage: Sequence[UsageRecord],
    outputs: Sequence[OutputRecord],
    scores: Sequence[ScoreRecord],
    decision_path: Path,
) -> None:
    """Write an evidence scaffold, not an invented model recommendation."""

    keys = _all_config_keys(usage, outputs, scores)

    lines: list[str] = [
        "# Model Decision Record",
        "",
        f"Run ID: `{run_id}`",
        "",
        "Use this file to record the task-level decision after reviewing the measured "
        "comparison. Do not select one universal model solely because it leads on a "
        "different task.",
        "",
        "## Evaluated models",
        "",
    ]

    evaluated_models = sorted(
        {model for _task, model, _prompt in keys} | {str(model) for model in models}
    )
    if evaluated_models:
        for model in evaluated_models:
            lines.append(f"- {model}")
    else:
        lines.append("- None")

    lines.extend(["", "## Evaluated configurations", ""])

    if keys:
        for task, model, prompt in keys:
            lines.append(f"- `{task}` — {model} — `{prompt}`")
    else:
        lines.append("- No configurations supplied.")

    lines.extend(
        [
            "",
            "## Task decisions",
            "",
            "For each task, complete:",
            "",
            "- selected model",
            "- prompt version",
            "- measured reason",
            "- rejected alternative(s)",
            "- condition that would reopen the decision",
            "",
        ]
    )

    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text("\n".join(lines), encoding="utf-8")


def write_reports(
    *,
    run_id: str,
    models: Sequence[str],
    usage: Sequence[UsageRecord],
    outputs: Sequence[OutputRecord],
    scores: Sequence[ScoreRecord],
    report_path: Path,
    decision_path: Path,
) -> None:
    """Generate the comparison report and decision scaffold for one run.

    Only records whose ``run_id`` matches the requested run are included.
    """

    run_usage = _for_run(usage, run_id)
    run_outputs = _for_run(outputs, run_id)
    run_scores = _for_run(scores, run_id)

    _write_report(
        run_id=run_id,
        usage=run_usage,
        outputs=run_outputs,
        scores=run_scores,
        report_path=Path(report_path),
    )

    _write_decision_scaffold(
        run_id=run_id,
        models=models,
        usage=run_usage,
        outputs=run_outputs,
        scores=run_scores,
        decision_path=Path(decision_path),
    )


def _prompt_label(task: TaskName, model_name: str, prompt_id: str, prompt_version: str) -> str:
    from promptlab.run import assign_prompt

    assignment = assign_prompt(task, model_name)
    base = f"{prompt_id}.{prompt_version}"
    return f"{base} transfer" if assignment.transfer else base


def _model_name(model_id: str, scores: Sequence[ScoreRecord]) -> str:
    for row in scores:
        if row.model_id == model_id:
            return row.model_name
    from promptlab.config import Settings

    for name, config in Settings.from_env().models.items():
        if config.model_id == model_id:
            return name
    return model_id


def _nd(metrics: dict[str, tuple[int, int, bool | None]], name: str) -> str:
    if name not in metrics:
        return "—"
    numerator, denominator, _direction = metrics[name]
    return f"{numerator}/{denominator}"


def _missed_or_invented(
    metrics: dict[str, tuple[int, int, bool | None]], name: str
) -> str:
    if name not in metrics:
        return "—"
    numerator, denominator, _direction = metrics[name]
    return f"{denominator - numerator}/{denominator}"


def _case_quality_metric(task: TaskName) -> str:
    return "queue_accuracy" if task == "triage" else "required_evidence_recall"


def _attempt_counts(calls: Sequence[CallRecord]) -> tuple[str, str, int]:
    case_ids = {row.case_id for row in calls}
    n_cases = len(case_ids)
    primary_by_case: dict[str, int] = defaultdict(int)
    retries = 0
    for row in calls:
        if row.attempt > 1:
            retries += 1
        else:
            primary_by_case[row.case_id] += 1
    repaired = sum(1 for case_id in case_ids if primary_by_case.get(case_id, 0) > 1)
    repairs = f"{repaired}/{n_cases}" if n_cases else "0/0"
    return repairs, str(retries), n_cases


def _tokens_per_case(calls: Sequence[CallRecord], n_cases: int) -> tuple[str, str]:
    if n_cases == 0:
        return "—", "—"
    input_tokens = sum(row.input_tokens for row in calls) / n_cases
    output_tokens = sum(row.output_tokens for row in calls) / n_cases
    return _fmt_number(input_tokens), _fmt_number(output_tokens)


def _latency_cells(calls: Sequence[CallRecord]) -> tuple[str, str, str]:
    latencies = round_trip_latencies(calls)
    if not latencies:
        return "—", "—", "0"
    return (
        f"{_fmt_number(float(median(latencies)))} ms",
        f"{_fmt_number(float(max(latencies)))} ms",
        str(len(latencies)),
    )


def _cost_cell(calls: Sequence[CallRecord]) -> str:
    total = sum(float(row.cost_usd) for row in calls)
    if total == 0.0:
        return "$0.00"
    return f"${total:.2f}"


def _row_ops(calls: Sequence[CallRecord], scores: Sequence[ScoreRecord], task: TaskName) -> str:
    repairs, retries, n_cases = _attempt_counts(calls)
    input_tokens, output_tokens = _tokens_per_case(calls, n_cases)
    median_latency, max_latency, n = _latency_cells(calls)
    scored = {
        row.case_id
        for row in scores
        if row.metric == _case_quality_metric(task)
    }
    failures = f"{max(n_cases - len(scored), 0)}/{n_cases}" if n_cases else "0/0"
    return (
        f"{input_tokens} | {output_tokens} | {median_latency} | {max_latency} | "
        f"{n} | {repairs} | {retries} | {failures} | {_cost_cell(calls)}"
    )


def _evidence_quality(scores: Sequence[ScoreRecord]) -> str:
    metrics = _aggregate_scores(scores)
    return (
        f"{_nd(metrics, 'required_evidence_recall')} | "
        f"{_missed_or_invented(metrics, 'required_evidence_recall')} | "
        f"{_missed_or_invented(metrics, 'unsupported_field_avoidance')} | "
        f"{_nd(metrics, 'citation_correctness')} | "
        f"{_nd(metrics, 'pii_leakage')} | "
        f"{_nd(metrics, 'version_selection_accuracy')}"
    )


def _triage_quality(scores: Sequence[ScoreRecord]) -> str:
    metrics = _aggregate_scores(scores)
    return (
        f"{_nd(metrics, 'queue_accuracy')} | "
        f"{_nd(metrics, 'escalation_accuracy')} | "
        f"{_nd(metrics, 'missed_escalation')} | "
        f"{_nd(metrics, 'unnecessary_escalation')} | "
        f"{_nd(metrics, 'human_boundary')} | "
        f"{_nd(metrics, 'pii_leakage')}"
    )


def _failed_parse_count(
    calls: Sequence[CallRecord], scores: Sequence[ScoreRecord], task: TaskName
) -> tuple[int, int]:
    n_cases = _attempt_counts(calls)[2]
    scored = {row.case_id for row in scores if row.metric == _case_quality_metric(task)}
    failed = max(n_cases - len(scored), 0)
    return failed, n_cases


def _truncated_root_object(calls: Sequence[CallRecord], failed_case_ids: set[str]) -> bool:
    for case_id in failed_case_ids:
        recs = [row for row in calls if row.case_id == case_id]
        if not recs:
            continue
        text = recs[0].response_text or ""
        if text.count("{") == text.count("}") + 1:
            return True
    return False


def _extraction_transfer_limit(
    *,
    calls: Sequence[CallRecord],
    scores: Sequence[ScoreRecord],
    task: TaskName,
    model_name: str,
    label: str,
) -> str | None:
    if task != "extraction" or not label.endswith(" transfer"):
        return None
    failed, n_cases = _failed_parse_count(calls, scores, task)
    if failed == 0 or n_cases == 0:
        return None
    parsed = n_cases - failed
    scored = {row.case_id for row in scores if row.metric == _case_quality_metric(task)}
    failed_ids = {row.case_id for row in calls if row.case_id not in scored}
    truncated = _truncated_root_object(calls, failed_ids)
    detail = (
        "the root object was truncated (one closing brace short), and the schema "
        "repair returned the same truncated text"
        if truncated
        else "schema validation failed and the bounded repair did not produce a valid object"
    )
    return (
        f"Extraction quality for {model_name.title()} on `{label}` is counted only "
        f"over the {parsed} cases that parsed. {failed} of {n_cases} cases never "
        f"produced valid JSON: {detail}. That is a transfer result, not a "
        "measurement of Qwen with an adapted extraction prompt."
    )


def _limits_section(
    transfer_rows: Sequence[str],
    untested: Sequence[str],
    extra_notes: Sequence[str] = (),
) -> list[str]:
    """Caveats the comparison tables do not support."""

    lines = [
        "## Limits",
        "",
        "There are only 12 cases per task. Results are directional, not "
        "production-scale estimates. A one-case or two-case difference "
        "(for example 11/12 versus 10/12) is not a universal model ranking.",
        "",
        "No production-volume reliability claim is being made. The set does not "
        "support claims about behavior at production volume or on document types "
        "absent from the case files.",
        "",
        "Prompt-transfer rows in this run:",
        "",
    ]
    if transfer_rows:
        lines.extend(f"- {row}" for row in transfer_rows)
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "Those rows are evidence of that transferred prompt, not of the "
            "model's capability after adaptation.",
            "",
            "Untested combinations:",
            "",
        ]
    )
    if untested:
        lines.extend(f"- {row}" for row in untested)
    else:
        lines.append("- None.")
    if extra_notes:
        lines.extend(["", *extra_notes])
    lines.extend(
        [
            "",
            "Local Ollama latency depends on lab hardware and is not a portable "
            "production latency figure.",
            "",
        ]
    )
    return lines


def write_comparison(
    *,
    calls: Sequence[CallRecord],
    scores: Sequence[ScoreRecord],
    report_path: Path,
) -> None:
    """Write one quality/tokens/latency/repairs table per task."""

    run_ids = sorted({row.run_id for row in calls} | {row.run_id for row in scores})
    run_id = run_ids[0] if len(run_ids) == 1 else ", ".join(run_ids) if run_ids else "unknown"
    scorer_versions = sorted({row.scorer_version for row in scores})
    scorer = scorer_versions[0] if scorer_versions else "unscored"
    temperatures = sorted({float(row.temperature) for row in calls})
    if not temperatures:
        temperature = "—"
    elif len(temperatures) == 1:
        temperature = f"{temperatures[0]:.1f}"
    else:
        temperature = ", ".join(f"{value:.1f}" for value in temperatures)

    lines: list[str] = [
        "# Model comparison: summarization, extraction, triage",
        "",
        f"Run `{run_id}`. Scorer version `{scorer}`. Temperature `{temperature}`.",
        "Every row names the prompt version it ran.",
        "",
        "Local Ollama `cost_usd` is `$0.00`. No cloud provider price is used.",
        "Token counts and latency include first attempts, transport retries, and schema repairs.",
        "Latency is median and maximum over `n` case round-trips.",
        "",
    ]

    grouped_calls: dict[tuple[TaskName, str], list[CallRecord]] = defaultdict(list)
    for call in calls:
        grouped_calls[(call.task, call.model_id)].append(call)

    grouped_scores: dict[tuple[TaskName, str], list[ScoreRecord]] = defaultdict(list)
    for score in scores:
        grouped_scores[(score.task, score.model_id)].append(score)

    evidence_header = (
        "| Model | Prompt | Required evidence | Missed | Invented/unsupported | "
        "Citations | PII leakage | Version current | Input tokens/case | "
        "Output tokens/case | Median latency | Max latency | n | Repairs | "
        "Retries | Failures | Cost |"
    )
    evidence_divider = (
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
        " ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    )
    triage_header = (
        "| Model | Prompt | Routing accuracy | Escalation accuracy | "
        "Missed escalations | Unnecessary escalations | Human-boundary | "
        "PII leakage | Input tokens/case | Output tokens/case | Median latency | "
        "Max latency | n | Repairs | Retries | Failures | Cost |"
    )
    triage_divider = (
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
        " ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    )

    transfer_rows: list[str] = []
    untested: list[str] = []
    extra_notes: list[str] = []

    for task in _TASK_ORDER:
        model_ids = sorted(
            {model_id for grouped_task, model_id in grouped_calls if grouped_task == task},
            key=lambda model_id: (_model_name(model_id, scores) != "mistral", model_id),
        )
        if not model_ids:
            continue
        header = triage_header if task == "triage" else evidence_header
        divider = triage_divider if task == "triage" else evidence_divider
        lines.extend([f"## {task.title()}", "", header, divider])
        for model_id in model_ids:
            task_calls = grouped_calls[(task, model_id)]
            task_scores = grouped_scores.get((task, model_id), [])
            model_name = _model_name(model_id, task_scores or scores)
            prompt_id = task_calls[0].prompt_id
            prompt_version = task_calls[0].prompt_version
            label = _prompt_label(task, model_name, prompt_id, prompt_version)
            if label.endswith(" transfer"):
                transfer_rows.append(
                    f"{task}: {model_name.title()} ran `{label}`"
                )
                untested.append(
                    f"{task}: {model_name.title()} with an adapted prompt"
                )
                note = _extraction_transfer_limit(
                    calls=task_calls,
                    scores=task_scores,
                    task=task,
                    model_name=model_name,
                    label=label,
                )
                if note is not None:
                    extra_notes.append(note)
            quality = (
                _triage_quality(task_scores)
                if task == "triage"
                else _evidence_quality(task_scores)
            )
            ops = _row_ops(task_calls, task_scores, task)
            lines.append(
                f"| {model_name.title()} | {label} | {quality} | {ops} |"
            )
        lines.append("")

    lines.extend(_limits_section(transfer_rows, untested, extra_notes))

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def write_comparison_from_evidence(
    *,
    run_path: Path,
    scores_path: Path,
    report_path: Path,
) -> None:
    """Generate reports/comparison.md from Day 5 call and score JSONL files."""

    calls: list[CallRecord] = []
    if run_path.exists():
        for line in run_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                calls.append(CallRecord.model_validate_json(line))
    write_comparison(
        calls=calls,
        scores=load_records(scores_path, ScoreRecord),
        report_path=report_path,
    )
