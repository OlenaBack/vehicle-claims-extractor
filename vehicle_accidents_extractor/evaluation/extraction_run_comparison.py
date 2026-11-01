"""Compare saved extraction runs of one batch in a single table."""

from pathlib import Path

from ..schema import GoldenRecord
from .accident_extraction_record_reader import read_accident_extraction_records
from .run_metrics import calculate_run_metrics

TABLE_HEADER = (
    "| Model | Prompt | Sampling | Accuracy | Valid first | Valid after repair | "
    "p50 | p95 | Cost / 1,000 accidents | Unknown usage attempts | "
    "Accidents with unknown usage | Cost lower bound |"
)
TABLE_SEPARATOR = "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"


def format_extraction_run_comparison(
    extraction_run_paths: list[Path], golden_records: list[GoldenRecord],
) -> str:
    """Format one Markdown row per extraction run with its measured metrics."""
    rows = [TABLE_HEADER, TABLE_SEPARATOR]
    for path in extraction_run_paths:
        records = read_accident_extraction_records(path)
        if not records:
            raise ValueError(f"Cannot compare an extraction run with no accident records: {path}")
        metrics = calculate_run_metrics(records, golden_records)
        run_metadata = records[0].run_metadata
        values = (
            run_metadata.model,
            run_metadata.prompt_version,
            run_metadata.sampling_profile,
            f"{metrics.accuracy:.1%} ({metrics.correct}/{metrics.total})",
            f"{metrics.first_attempt_validity:.1%}",
            f"{metrics.final_validity:.1%}",
            f"{metrics.latency_p50_seconds:.2f}s",
            f"{metrics.latency_p95_seconds:.2f}s",
            f"${metrics.cost_per_1000_accidents:.4f}",
            str(metrics.unknown_usage_attempts),
            str(metrics.accidents_with_unknown_token_usage),
            "yes" if metrics.cost_is_lower_bound else "no",
        )
        rows.append("| " + " | ".join(_markdown_cell(value) for value in values) + " |")
    return "\n".join(rows)


def _markdown_cell(value: str) -> str:
    """Keep metadata values inside their Markdown table cell."""
    return value.replace("|", r"\|").replace("\r", " ").replace("\n", " ")
