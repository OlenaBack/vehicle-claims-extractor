"""Evaluate a saved accident extraction run."""

import argparse
from pathlib import Path

from vehicle_accidents_extractor.evaluation.run_metrics import (
    calculate_run_metrics,
)
from vehicle_accidents_extractor.evaluation.accident_extraction_record_reader import (
    read_accident_extraction_records,
)
from vehicle_accidents_extractor.input_paths import InputPaths
from vehicle_accidents_extractor.schema import GoldenRecord


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--extraction-run",
        type=Path,
        required=True,
        help="Path to a saved extraction run JSONL file.",
    )
    parser.add_argument(
        "--golden",
        type=Path,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        records = read_accident_extraction_records(args.extraction_run)
        if not records:
            raise ValueError("Cannot evaluate an extraction run with no accident records")
        batch = records[0].run.batch
        golden_path = args.golden or InputPaths(ROOT).golden_labels_path(batch)
        golden = [
            GoldenRecord.model_validate_json(line)
            for line in golden_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        metrics = calculate_run_metrics(records, golden)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error

    print(f"Accidents: {metrics.accident_count}")
    print(f"Golden accidents: {metrics.golden_accident_count}")
    print(
        f"Accuracy: {metrics.correct}/{metrics.total} "
        f"({metrics.accuracy:.1%})"
    )
    print(f"First-attempt validity: {metrics.first_attempt_validity:.1%}")
    print(f"Validity after repair: {metrics.final_validity:.1%}")
    print(f"Latency p50: {metrics.latency_p50_seconds:.3f}s")
    print(f"Latency p95: {metrics.latency_p95_seconds:.3f}s")
    print(f"Estimated cost/1,000 accidents: ${metrics.cost_per_1000_accidents:.4f}")
    print(f"Unknown-usage attempts: {metrics.unknown_usage_calls}")
    print(
        "Accidents with unknown usage: "
        f"{metrics.accidents_with_unknown_usage}"
    )
    if metrics.cost_is_lower_bound:
        print("Cost is a lower bound because some token usage is unknown.")

    print("\nField scores:")
    for field, (correct, total) in metrics.by_field.items():
        print(f"  {field}: {correct}/{total} ({correct / total:.1%})")


if __name__ == "__main__":
    main()
