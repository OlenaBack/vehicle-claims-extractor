"""Compare saved extraction runs and render their shared metrics as tables."""

from dataclasses import dataclass
from pathlib import Path

from ..extraction_run_records import AccidentExtractionRecord, ExtractionRunMetadata
from ..input_paths import InputPaths
from ..schema import GoldenRecord
from .accident_extraction_record_reader import read_accident_extraction_records
from .golden_record_reader import read_golden_records
from .run_metrics import RunMetrics, calculate_run_metrics


@dataclass(frozen=True)
class ExtractionRunComparisonRow:
    """One saved extraction run with its calculated run metrics."""

    run_metadata: ExtractionRunMetadata
    metrics: RunMetrics


def evaluate_extraction_run(
    extraction_records: list[AccidentExtractionRecord],
    golden_records: list[GoldenRecord],
) -> ExtractionRunComparisonRow:
    """Build one comparison row from a run's saved records and golden labels."""
    if not extraction_records:
        raise ValueError("Cannot evaluate an extraction run with no accident records")

    run_metadata = extraction_records[0].run_metadata
    metrics = calculate_run_metrics(extraction_records, golden_records)
    return ExtractionRunComparisonRow(run_metadata, metrics)


def compare_extraction_runs(
    extraction_run_paths: list[Path], input_paths: InputPaths,
) -> tuple[ExtractionRunComparisonRow, ...]:
    """Read and score runs from one batch, sorted independently of input path order."""
    if not extraction_run_paths:
        raise ValueError("No extraction runs were provided for comparison")

    record_sets = []
    for extraction_run_path in extraction_run_paths:
        extraction_records = read_accident_extraction_records(extraction_run_path)
        if not extraction_records:
            raise ValueError(
                f"Cannot compare an extraction run with no accident records: {extraction_run_path}"
            )
        record_sets.append(extraction_records)

    seen_run_ids = set()
    duplicate_run_ids = set()
    for records in record_sets:
        run_id = records[0].run_metadata.run_id
        if run_id in seen_run_ids:
            duplicate_run_ids.add(run_id)
        seen_run_ids.add(run_id)
    if duplicate_run_ids:
        run_ids = ", ".join(sorted(duplicate_run_ids))
        raise ValueError(f"Cannot compare duplicate extraction run IDs: {run_ids}")

    batches = {records[0].run_metadata.batch for records in record_sets}
    if len(batches) != 1:
        batch_names = ", ".join(sorted(batches))
        raise ValueError(f"Cannot compare extraction runs from different batches: {batch_names}")

    accident_batch = next(iter(batches))
    golden_records = read_golden_records(input_paths.golden_labels_path(accident_batch))
    rows = [
        evaluate_extraction_run(extraction_records, golden_records)
        for extraction_records in record_sets
    ]
    return tuple(sorted(rows, key=_sort_key))


def format_terminal_extraction_run_comparison(
    rows: tuple[ExtractionRunComparisonRow, ...],
) -> str:
    """Render the run comparison fields that are useful in a terminal."""
    header = (
        f"{'model ID':<24}{'prompt':<8}{'sampling':<15}{'accuracy':>9}{'valid 1st':>10}"
        f"{'valid final':>12}{'p50 s':>8}{'p95 s':>8}{'cost/1k':>10}"
    )
    lines = [header]
    for row in rows:
        metadata = row.run_metadata
        metrics = row.metrics
        lines.append(
            f"{metadata.model:<24}{metadata.prompt_version:<8}"
            f"{metadata.sampling_profile_name:<15}"
            f"{metrics.accuracy:>9.1%}{metrics.first_attempt_validity:>10.1%}"
            f"{metrics.final_validity:>12.1%}"
            f"{metrics.latency_p50_seconds:>8.2f}{metrics.latency_p95_seconds:>8.2f}"
            f"{format_cost_per_1000_accidents(metrics.cost_per_1000_accidents):>10}"
        )
    return "\n".join(lines)


def format_markdown_extraction_run_comparison(
    rows: tuple[ExtractionRunComparisonRow, ...],
) -> str:
    """Render all comparison fields as a Markdown table for the report appendix."""
    header = (
        "| # | Model ID | Prompt | Sampling | Run ID | Accuracy | Valid 1st | "
        "Valid after repair | p50 | p95 | Cost / 1,000 | Unknown usage attempts | "
        "Accidents with unknown usage |"
    )
    separator = "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    lines = [header, separator]
    for index, row in enumerate(rows, start=1):
        metadata = row.run_metadata
        metrics = row.metrics
        lines.append(
            f"| {index} | {metadata.model} | {metadata.prompt_version} | "
            f"{metadata.sampling_profile_name} | `{metadata.run_id[:8]}` | "
            f"{metrics.accuracy:.1%} ({metrics.correct}/{metrics.total}) | "
            f"{metrics.first_attempt_validity:.0%} | {metrics.final_validity:.0%} | "
            f"{metrics.latency_p50_seconds:.2f} s | {metrics.latency_p95_seconds:.2f} s | "
            f"{format_cost_per_1000_accidents(metrics.cost_per_1000_accidents)} | "
            f"{metrics.unknown_usage_attempts} | "
            f"{metrics.accidents_with_unknown_token_usage} |"
        )
    return "\n".join(lines)


def format_cost_per_1000_accidents(cost: float) -> str:
    """Format a run's cost estimate with three decimal places."""
    return f"${cost:.3f}"


def _sort_key(row: ExtractionRunComparisonRow) -> tuple:
    metadata = row.run_metadata
    return (
        metadata.model,
        metadata.prompt_version,
        metadata.sampling_profile_name,
        metadata.started_at,
        metadata.run_id,
    )
