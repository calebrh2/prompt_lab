from decimal import Decimal
from pathlib import Path
from statistics import median
from typing import Literal

from promptlab.records import OutputRecord, ScoreRecord, UsageRecord
from promptlab.report import write_reports
from promptlab.usage import CallRecord, round_trip_latencies


def _usage(
    *,
    case_id: str,
    latency_ms: float,
    kind: Literal["primary", "transport_retry", "repair", "repair_retry"],
    attempt: int,
) -> UsageRecord:
    return UsageRecord(
        run_id="demo",
        task="triage",
        case_id=case_id,
        model_name="mistral",
        model_id="fixture-model",
        prompt_version="triage-mistral-v1",
        attempt=attempt,
        kind=kind,
        status="success",
        prompt_tokens=100,
        completion_tokens=25,
        latency_ms=latency_ms,
        cost_usd=Decimal("0"),
    )


def test_report_sums_repair_latency_into_the_case(tmp_path: Path) -> None:
    usage = [
        _usage(case_id="T01", latency_ms=1000.0, kind="primary", attempt=1),
        _usage(case_id="T01", latency_ms=2000.0, kind="repair", attempt=1),
        _usage(case_id="T02", latency_ms=5000.0, kind="primary", attempt=1),
    ]
    outputs = [
        OutputRecord(
            run_id="demo",
            task="triage",
            case_id="T01",
            model_name="mistral",
            model_id="fixture-model",
            prompt_version="triage-mistral-v1",
            succeeded=True,
            repairs=1,
            output={"queue": "card_dispute"},
        ),
        OutputRecord(
            run_id="demo",
            task="triage",
            case_id="T02",
            model_name="mistral",
            model_id="fixture-model",
            prompt_version="triage-mistral-v1",
            succeeded=True,
            repairs=0,
            output={"queue": "card_dispute"},
        ),
    ]
    scores = [
        ScoreRecord(
            run_id="demo",
            task="triage",
            case_id="T01",
            model_name="mistral",
            model_id="fixture-model",
            prompt_id="triage",
            prompt_version="triage-mistral-v1",
            scorer_version="2.0.0",
            metric="queue_accuracy",
            numerator=1,
            denominator=1,
        )
    ]
    report = tmp_path / "comparison.md"
    write_reports(
        run_id="demo",
        models=["mistral"],
        usage=usage,
        outputs=outputs,
        scores=scores,
        report_path=report,
        decision_path=tmp_path / "model-decision.md",
    )
    text = report.read_text(encoding="utf-8")
    assert "4000 ms" in text
    assert "5000 ms" in text
    assert "| 2 |" in text
    assert "2000 ms" not in text


def test_day5_run_latency_is_one_round_trip_per_case() -> None:
    path = Path("docs/day5-run.jsonl")
    records = [
        CallRecord.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(records) == 81
    latencies = round_trip_latencies(records)
    assert len(latencies) == 72
    qwen_extract = round_trip_latencies(
        [row for row in records if row.task == "extraction" and "qwen" in row.model_id]
    )
    assert len(qwen_extract) == 12
    assert max(qwen_extract) == 28360
    assert median(qwen_extract) == 16328.5


def test_day5_comparison_tables_use_counts_tokens_and_local_cost(tmp_path: Path) -> None:
    from promptlab.report import write_comparison_from_evidence

    report = tmp_path / "comparison.md"
    write_comparison_from_evidence(
        run_path=Path("docs/day5-run.jsonl"),
        scores_path=Path("docs/day5-scores.jsonl"),
        report_path=report,
    )
    text = report.read_text(encoding="utf-8")
    assert "# Model comparison" in text
    assert "## Summarization" in text
    assert "## Extraction" in text
    assert "## Triage" in text
    assert "summarize.v2" in text
    assert "summarize.v2 transfer" in text
    assert "extract.v4 transfer" in text
    assert "triage.v1 transfer" in text
    assert "Missed" in text
    assert "Invented/unsupported" in text
    assert "Routing accuracy" in text
    assert "Escalation accuracy" in text
    assert "Missed escalations" in text
    assert "Unnecessary escalations" in text
    assert "Human-boundary" in text
    assert "PII leakage" in text
    assert "Input tokens/case" in text
    assert "Output tokens/case" in text
    assert "Median latency" in text
    assert "Max latency" in text
    assert "$0.00" in text
    assert "%" not in text
    assert "mean" not in text.lower()
    assert "16328.5 ms" in text
    assert "28360 ms" in text
