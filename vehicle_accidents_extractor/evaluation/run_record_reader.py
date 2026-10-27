"""Read saved extraction records from JSON Lines."""

from pathlib import Path

from pydantic import ValidationError

from ..run_records import DocumentRunRecord


def read_run_records(path: Path) -> list[DocumentRunRecord]:
    records = []

    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue

            try:
                record = DocumentRunRecord.model_validate_json(line)
            except ValidationError as error:
                raise ValueError(
                    f"{path}, line {line_number}: {error}"
                ) from error

            records.append(record)

    return records
