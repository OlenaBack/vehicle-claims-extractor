"""Calculate one run's metrics from records and golden labels, without file access."""

from dataclasses import dataclass

from ..extraction_run_records import AccidentExtractionRecord
from ..schema import GoldenRecord
from .accident_extraction_scorer import score_accident


@dataclass(frozen=True)
class RunMetrics:
    accident_count: int
    golden_accident_count: int
    correct: int
    total: int
    by_field: dict[str, tuple[int, int]]
    first_attempt_valid_count: int
    final_valid_count: int
    latency_p50_seconds: float
    latency_p95_seconds: float
    cost_per_1000_accidents: float
    unknown_usage_attempts: int
    accidents_with_unknown_token_usage: int
    cost_is_lower_bound: bool

    @property
    def accuracy(self) -> float:
        return self.correct / self.total

    @property
    def first_attempt_validity(self) -> float:
        return self.first_attempt_valid_count / self.accident_count

    @property
    def final_validity(self) -> float:
        return self.final_valid_count / self.accident_count


def calculate_run_metrics(
    extraction_records: list[AccidentExtractionRecord],
    golden_records: list[GoldenRecord],
) -> RunMetrics:
    """Aggregate accuracy, validity, latency and known API cost for one run.

    Unknown token usage contributes no estimated charge, making nonzero-price
    cost estimates lower bounds. unknown_usage_attempts counts HTTP attempts,
    including retries, rather than logical LLM calls.
    """
    if not extraction_records:
        raise ValueError("Cannot calculate metrics for an empty run")
    if not golden_records:
        raise ValueError("Cannot calculate accuracy without golden labels")

    extraction_records_by_accident_id = {
        extraction_record.accident_id: extraction_record
        for extraction_record in extraction_records
    }
    if len(extraction_records_by_accident_id) != len(extraction_records):
        raise ValueError("Duplicate accident IDs in run records")
    if len({golden_record.accident_id for golden_record in golden_records}) != len(golden_records):
        raise ValueError("Duplicate accident IDs in golden labels")
    run_metadata = extraction_records[0].run_metadata
    if any(
        extraction_record.run_metadata != run_metadata
        for extraction_record in extraction_records
    ):
        raise ValueError("Run records contain mixed metadata")
    missing_golden_accident_ids = sorted(
        golden_record.accident_id
        for golden_record in golden_records
        if golden_record.accident_id not in extraction_records_by_accident_id
    )
    if missing_golden_accident_ids:
        raise ValueError(
            "Missing extractions for golden accidents: "
            f"{', '.join(missing_golden_accident_ids)}"
        )

    correct = total = 0
    field_counts: dict[str, list[int]] = {}
    for golden_record in golden_records:
        extraction_record = extraction_records_by_accident_id[golden_record.accident_id]
        extracted_accident = (
            None if extraction_record.status == "failed" else extraction_record.extracted_accident
        )
        score = score_accident(golden_record.golden_label, extracted_accident)
        correct += score.correct
        total += score.total
        for field, (field_correct, field_total) in score.by_field.items():
            counts = field_counts.setdefault(field, [0, 0])
            counts[0] += field_correct
            counts[1] += field_total

    input_price, output_price = run_metadata.price_per_1m
    known_cost_usd = 0.0
    unknown_usage_attempts = accidents_with_unknown_token_usage = 0
    for extraction_record in extraction_records:
        accident_has_unknown_token_usage = False
        for llm_call in extraction_record.calls:
            for attempt in llm_call.attempts:
                known_cost_usd += (
                    (attempt.input_tokens or 0) * input_price
                    + (attempt.output_tokens or 0) * output_price
                ) / 1_000_000
                if attempt.input_tokens is None or attempt.output_tokens is None:
                    unknown_usage_attempts += 1
                    accident_has_unknown_token_usage = True
        accidents_with_unknown_token_usage += int(accident_has_unknown_token_usage)

    accident_latencies = sorted(
        extraction_record.latency_seconds for extraction_record in extraction_records
    )
    return RunMetrics(
        accident_count=len(extraction_records),
        golden_accident_count=len(golden_records),
        correct=correct,
        total=total,
        by_field={field: (counts[0], counts[1]) for field, counts in field_counts.items()},
        first_attempt_valid_count=sum(
            extraction_record.status == "valid" for extraction_record in extraction_records
        ),
        final_valid_count=sum(
            extraction_record.status != "failed" for extraction_record in extraction_records
        ),
        latency_p50_seconds=_percentile(accident_latencies, 0.5),
        latency_p95_seconds=_percentile(accident_latencies, 0.95),
        cost_per_1000_accidents=known_cost_usd / len(extraction_records) * 1000,
        unknown_usage_attempts=unknown_usage_attempts,
        accidents_with_unknown_token_usage=accidents_with_unknown_token_usage,
        cost_is_lower_bound=unknown_usage_attempts > 0 and (input_price > 0 or output_price > 0),
    )


def _percentile(sorted_values: list[float], percentile: float) -> float:
    """Interpolate at (n - 1) * percentile in a nonempty sorted sequence."""
    position = (len(sorted_values) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return sorted_values[lower] + fraction * (sorted_values[upper] - sorted_values[lower])
