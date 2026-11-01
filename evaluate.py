"""Evaluate one saved extraction run or compare several runs from one batch."""

import argparse
import glob
from pathlib import Path

from vehicle_accidents_extractor.evaluation.accident_extraction_record_reader import (
    read_accident_extraction_records,
)
from vehicle_accidents_extractor.evaluation.extraction_run_comparison import (
    compare_extraction_runs,
    evaluate_extraction_run,
    format_cost_per_1000_accidents,
    format_markdown_extraction_run_comparison,
    format_terminal_extraction_run_comparison,
)
from vehicle_accidents_extractor.evaluation.golden_record_reader import read_golden_records
from vehicle_accidents_extractor.input_paths import InputPaths


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    run_mode = parser.add_mutually_exclusive_group(required=True)
    run_mode.add_argument(
        "--extraction-run",
        dest="extraction_run_path",
        type=Path,
        help="Path to a saved extraction run JSONL file.",
    )
    run_mode.add_argument(
        "--compare",
        dest="extraction_run_paths",
        nargs="+",
        type=Path,
        help="Paths to saved extraction run JSONL files from one batch.",
    )
    parser.add_argument(
        "--golden",
        dest="golden_labels_path",
        type=Path,
        help="Golden labels file for --extraction-run.",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Render --compare as a Markdown table.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        input_paths = InputPaths(ROOT)
        if args.extraction_run_paths is not None:
            if args.golden_labels_path is not None:
                raise ValueError("--golden can only be used with --extraction-run")
            extraction_run_paths = expand_extraction_run_paths(args.extraction_run_paths)
            rows = compare_extraction_runs(extraction_run_paths, input_paths)
            comparison = (
                format_markdown_extraction_run_comparison(rows)
                if args.markdown
                else format_terminal_extraction_run_comparison(rows)
            )
            print(comparison)
            return
        if args.markdown:
            raise ValueError("--markdown can only be used with --compare")

        extraction_records = read_accident_extraction_records(args.extraction_run_path)
        if not extraction_records:
            raise ValueError("Cannot evaluate an extraction run with no accident records")
        accident_batch = extraction_records[0].run_metadata.batch
        golden_labels_path = args.golden_labels_path or input_paths.golden_labels_path(accident_batch)
        golden_records = read_golden_records(golden_labels_path)
        comparison_row = evaluate_extraction_run(extraction_records, golden_records)
        metrics = comparison_row.metrics
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error

    print(f"Machine: {extraction_records[0].run_metadata.machine}")
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
    print(
        "Estimated cost/1,000 accidents: "
        f"{format_cost_per_1000_accidents(metrics.cost_per_1000_accidents)}"
    )
    print(f"Attempts with unknown token usage: {metrics.unknown_usage_attempts}")
    print(
        "Accidents with unknown token usage: "
        f"{metrics.accidents_with_unknown_token_usage}"
    )
    if metrics.cost_is_lower_bound:
        print("Cost is a lower bound because some token usage is unknown.")

    print("\nField scores:")
    for field, (correct, total) in metrics.by_field.items():
        print(f"  {field}: {correct}/{total} ({correct / total:.1%})")


def expand_extraction_run_paths(paths: list[Path]) -> list[Path]:
    """Expand wildcard arguments while preserving explicit paths and input order."""
    expanded_paths = []
    for path in paths:
        if glob.has_magic(str(path)):
            matches = sorted(Path(match) for match in glob.glob(str(path), recursive=True))
            if not matches:
                raise ValueError(f"No extraction runs match {path}")
            expanded_paths.extend(matches)
        else:
            expanded_paths.append(path)
    return expanded_paths


if __name__ == "__main__":
    main()
