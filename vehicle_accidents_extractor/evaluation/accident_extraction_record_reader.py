"""Read saved extraction records from JSON Lines."""

from pathlib import Path

from pydantic import ValidationError

from ..extraction_run_records import AccidentExtractionRecord


def read_accident_extraction_records(
    extraction_run_records_path: Path,
) -> list[AccidentExtractionRecord]:
    extraction_records = []

    with extraction_run_records_path.open(encoding="utf-8") as records_file:
        for line_number, json_line in enumerate(records_file, start=1):
            if not json_line.strip():
                continue

            try:
                accident_extraction_record = AccidentExtractionRecord.model_validate_json(json_line)
            except ValidationError as error:
                raise ValueError(
                    f"{extraction_run_records_path}, line {line_number}: {error}"
                ) from error

            extraction_records.append(accident_extraction_record)

    return extraction_records
