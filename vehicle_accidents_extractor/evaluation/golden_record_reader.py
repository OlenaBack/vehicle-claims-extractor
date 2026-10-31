"""Read golden labels from a JSONL file."""

from pathlib import Path

from ..schema import GoldenRecord


def read_golden_records(golden_labels_path: Path) -> list[GoldenRecord]:
    return [
        GoldenRecord.model_validate_json(line)
        for line in golden_labels_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
