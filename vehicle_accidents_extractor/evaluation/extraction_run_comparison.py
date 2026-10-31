"""Compare saved extraction runs of one batch in a single table."""

from pathlib import Path

from ..schema import GoldenRecord
from .accident_extraction_record_reader import read_accident_extraction_records
from .run_metrics import calculate_run_metrics

TABLE_HEADER = (
    f"{'model':<24}{'prompt':<8}{'sampling':<15}{'accuracy':>9}{'valid 1st':>10}"
    f"{'valid final':>12}{'p50 s':>8}{'p95 s':>8}{'$/1000':>9}"
)


def format_extraction_run_comparison(
    extraction_run_paths: list[Path], golden_records: list[GoldenRecord],
) -> str:
    """One row per extraction run: accuracy, validity on the first attempt and after repair, latency, cost."""
    rows = [TABLE_HEADER]
    for path in extraction_run_paths:
        records = read_accident_extraction_records(path)
        if not records:
            raise ValueError(f"Cannot compare an extraction run with no accident records: {path}")
        metrics = calculate_run_metrics(records, golden_records)
        run_metadata = records[0].run_metadata
        rows.append(
            f"{run_metadata.model:<24}{run_metadata.prompt_version:<8}"
            f"{run_metadata.sampling_profile:<15}"
            f"{metrics.accuracy:>9.1%}{metrics.first_attempt_validity:>10.1%}"
            f"{metrics.final_validity:>12.1%}"
            f"{metrics.latency_p50_seconds:>8.2f}{metrics.latency_p95_seconds:>8.2f}"
            f"{metrics.cost_per_1000_accidents:>9.3f}"
        )
    return "\n".join(rows)
