"""Checks the saved-run comparison output used by REPORT.md."""

import unittest
from pathlib import Path
from unittest.mock import patch

from vehicle_accidents_extractor.evaluation.accident_extraction_record_reader import (
    read_accident_extraction_records,
)
from vehicle_accidents_extractor.evaluation.extraction_run_comparison import (
    compare_extraction_runs,
    format_markdown_extraction_run_comparison,
)
from vehicle_accidents_extractor.input_paths import InputPaths


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ExtractionRunComparisonTests(unittest.TestCase):
    def test_markdown_matches_the_saved_run_appendix_independent_of_path_order(self) -> None:
        extraction_run_paths = sorted((PROJECT_ROOT / "extractions" / "batch-01").glob("*.jsonl"))
        input_paths = InputPaths(PROJECT_ROOT)

        rows = compare_extraction_runs(extraction_run_paths, input_paths)
        reversed_rows = compare_extraction_runs(list(reversed(extraction_run_paths)), input_paths)
        markdown = format_markdown_extraction_run_comparison(rows)
        reversed_markdown = format_markdown_extraction_run_comparison(reversed_rows)

        report = (PROJECT_ROOT / "REPORT.md").read_text(encoding="utf-8")
        appendix = report.split("## Appendix: all 24 runs", maxsplit=1)[1]
        report_table = "\n".join(line for line in appendix.splitlines() if line.startswith("|"))

        self.assertEqual(len(rows), 24)
        self.assertEqual(markdown, reversed_markdown)
        self.assertEqual(markdown, report_table)

    def test_comparison_rejects_runs_from_different_batches(self) -> None:
        path = next((PROJECT_ROOT / "extractions" / "batch-01").glob("*.jsonl"))
        records = read_accident_extraction_records(path)
        other_metadata = records[0].run_metadata.model_copy(update={"batch": "batch-02"})
        other_records = [
            record.model_copy(update={"run_metadata": other_metadata})
            for record in records
        ]

        with patch(
            "vehicle_accidents_extractor.evaluation.extraction_run_comparison.read_accident_extraction_records",
            side_effect=[records, other_records],
        ):
            with self.assertRaisesRegex(ValueError, "different batches: batch-01, batch-02"):
                compare_extraction_runs([path, path], InputPaths(PROJECT_ROOT))


if __name__ == "__main__":
    unittest.main()
