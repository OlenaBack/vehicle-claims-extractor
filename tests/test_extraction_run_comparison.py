"""Test the saved-run comparison output."""

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from vehicle_accidents_extractor.evaluation.extraction_run_comparison import (
    format_extraction_run_comparison,
)


class ExtractionRunComparisonTests(unittest.TestCase):
    def test_formats_markdown_with_all_run_metrics(self):
        record = SimpleNamespace(
            run_metadata=SimpleNamespace(
                model="openai/gpt-4o-mini",
                prompt_version="v2",
                sampling_profile="varied",
            ),
        )
        metrics = SimpleNamespace(
            accuracy=0.9,
            correct=9,
            total=10,
            first_attempt_validity=0.8,
            final_validity=0.9,
            latency_p50_seconds=1.234,
            latency_p95_seconds=2.345,
            cost_per_1000_accidents=0.12345,
            unknown_usage_attempts=2,
            accidents_with_unknown_token_usage=1,
            cost_is_lower_bound=True,
        )

        with (
            patch(
                "vehicle_accidents_extractor.evaluation.extraction_run_comparison."
                "read_accident_extraction_records",
                return_value=[record],
            ),
            patch(
                "vehicle_accidents_extractor.evaluation.extraction_run_comparison."
                "calculate_run_metrics",
                return_value=metrics,
            ),
        ):
            comparison = format_extraction_run_comparison([Path("run.jsonl")], [])

        rows = comparison.splitlines()
        self.assertEqual(len(rows), 3)
        self.assertTrue(rows[0].startswith("| Model | Prompt | Sampling |"))
        self.assertTrue(rows[1].startswith("| --- |"))
        self.assertIn("| Accuracy |", rows[0])
        self.assertIn("| Valid first |", rows[0])
        self.assertIn("| Valid after repair |", rows[0])
        self.assertIn("| Unknown usage attempts |", rows[0])
        self.assertIn("| Accidents with unknown usage |", rows[0])
        self.assertIn("| Cost lower bound |", rows[0])
        self.assertEqual(
            rows[2],
            "| openai/gpt-4o-mini | v2 | varied | 90.0% (9/10) | 80.0% | 90.0% "
            "| 1.23s | 2.35s | $0.1235 | 2 | 1 | yes |",
        )


if __name__ == "__main__":
    unittest.main()
