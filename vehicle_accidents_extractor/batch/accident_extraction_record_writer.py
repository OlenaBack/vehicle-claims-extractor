"""Serialize accident extraction outcomes and write them as JSON Lines."""

import json
from pathlib import Path
from typing import TextIO

from ..extraction.accident_extractor import AccidentExtractionOutcome
from ..extraction_run_records import AccidentExtractionRecord, ExtractionRunMetadata


class AccidentExtractionRecordWriter:
    def __init__(self, extraction_run_records_path: Path, run_metadata: ExtractionRunMetadata):
        self._extraction_run_records_path = extraction_run_records_path
        self._run_metadata = run_metadata
        self._file: TextIO | None = None

    def __enter__(self) -> "AccidentExtractionRecordWriter":
        self._extraction_run_records_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self._extraction_run_records_path.open("x", encoding="utf-8")
        return self

    def write(self, accident_id: str, outcome: AccidentExtractionOutcome) -> None:
        if self._file is None:
            raise RuntimeError("Use AccidentExtractionRecordWriter inside a with block")

        accident_extraction_record = AccidentExtractionRecord(
            run_metadata=self._run_metadata,
            accident_id=accident_id,
            status=outcome.status,
            extracted_accident=outcome.accident,
            calls=outcome.calls,
            repair_attempted=outcome.repair_attempted,
            validation_errors=outcome.validation_errors,
            latency_seconds=outcome.latency_seconds,
            error=outcome.error,
        )
        json_line = json.dumps(
            accident_extraction_record.model_dump(mode="json", by_alias=True),
            ensure_ascii=False,
            allow_nan=False,
        )
        self._file.write(json_line + "\n")
        self._file.flush()

    def __exit__(self, *exc_info) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None
