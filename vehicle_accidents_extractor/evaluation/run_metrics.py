"""Calculate one run's metrics from records and golden labels, without file access."""

from dataclasses import dataclass

from ..run_records import DocumentRunRecord
from ..schema import GoldenRecord
from .accident_extraction_scorer import score_accident


@dataclass(frozen=True)
class RunMetrics:
    document_count: int
    golden_document_count: int
    correct: int
    total: int
    by_field: dict[str, tuple[int, int]]
    first_attempt_valid_count: int
    final_valid_count: int
    latency_p50_seconds: float
    latency_p95_seconds: float
    cost_per_1000_documents: float
    unknown_usage_calls: int
    documents_with_unknown_usage: int
    cost_is_lower_bound: bool

    @property
    def accuracy(self) -> float:
        return self.correct / self.total

    @property
    def first_attempt_validity(self) -> float:
        return self.first_attempt_valid_count / self.document_count

    @property
    def final_validity(self) -> float:
        return self.final_valid_count / self.document_count


def calculate_run_metrics(
    records: list[DocumentRunRecord],
    golden: list[GoldenRecord],
) -> RunMetrics:
    """Aggregate accuracy, validity, latency and known API cost for one run.

    Unknown token usage contributes no estimated charge, making nonzero-price
    cost estimates lower bounds. unknown_usage_calls counts HTTP attempts,
    including retries, rather than logical LLM calls.
    """
    if not records:
        raise ValueError("Cannot calculate metrics for an empty run")
    if not golden:
        raise ValueError("Cannot calculate accuracy without golden labels")

    by_id = {record.document_id: record for record in records}
    if len(by_id) != len(records):
        raise ValueError("Duplicate document IDs in run records")
    if len({label.id for label in golden}) != len(golden):
        raise ValueError("Duplicate document IDs in golden labels")
    run = records[0].run
    if any(record.run != run for record in records):
        raise ValueError("Run records contain mixed metadata")
    missing = sorted(label.id for label in golden if label.id not in by_id)
    if missing:
        raise ValueError(f"Missing results for golden documents: {', '.join(missing)}")

    correct = total = 0
    field_counts: dict[str, list[int]] = {}
    for label in golden:
        record = by_id[label.id]
        produced = None if record.status == "failed" else record.accident
        score = score_accident(label.labels, produced)
        correct += score.correct
        total += score.total
        for field, (field_correct, field_total) in score.by_field.items():
            counts = field_counts.setdefault(field, [0, 0])
            counts[0] += field_correct
            counts[1] += field_total

    input_price, output_price = run.price_per_1m
    known_cost = 0.0
    unknown_usage_calls = documents_with_unknown_usage = 0
    for record in records:
        document_has_unknown_usage = False
        for call in record.calls:
            for attempt in call.attempts:
                known_cost += (
                    (attempt.input_tokens or 0) * input_price
                    + (attempt.output_tokens or 0) * output_price
                ) / 1_000_000
                if attempt.input_tokens is None or attempt.output_tokens is None:
                    unknown_usage_calls += 1
                    document_has_unknown_usage = True
        documents_with_unknown_usage += int(document_has_unknown_usage)

    latencies = sorted(record.latency_seconds for record in records)
    return RunMetrics(
        document_count=len(records),
        golden_document_count=len(golden),
        correct=correct,
        total=total,
        by_field={field: (counts[0], counts[1]) for field, counts in field_counts.items()},
        first_attempt_valid_count=sum(record.status == "valid" for record in records),
        final_valid_count=sum(record.status != "failed" for record in records),
        latency_p50_seconds=_percentile(latencies, 0.5),
        latency_p95_seconds=_percentile(latencies, 0.95),
        cost_per_1000_documents=known_cost / len(records) * 1000,
        unknown_usage_calls=unknown_usage_calls,
        documents_with_unknown_usage=documents_with_unknown_usage,
        cost_is_lower_bound=unknown_usage_calls > 0 and (input_price > 0 or output_price > 0),
    )


def _percentile(sorted_values: list[float], percentile: float) -> float:
    """Interpolate at (n - 1) * percentile in a nonempty sorted sequence."""
    position = (len(sorted_values) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return sorted_values[lower] + fraction * (sorted_values[upper] - sorted_values[lower])
