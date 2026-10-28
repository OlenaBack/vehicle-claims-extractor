"""Serialize accident extraction outcomes and write them as JSON Lines."""

import json
from pathlib import Path
from typing import TextIO

from ..extraction.accident_extractor import AccidentExtractionResult
from ..extraction_run_records import AccidentExtractionRecord, ExtractionRunMetadata


class ExtractionRecordWriter:
    def __init__(self, path: Path, run_metadata: ExtractionRunMetadata):
        self._path = path
        self._run_metadata = run_metadata
        self._file: TextIO | None = None

    def __enter__(self) -> "ExtractionRecordWriter":
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self._path.open("x", encoding="utf-8")
        return self

    def write(self, accident_id: str, result: AccidentExtractionResult) -> None:
        if self._file is None:
            raise RuntimeError("Use ExtractionRecordWriter inside a with block")

        record = AccidentExtractionRecord(
            run=self._run_metadata,
            accident_id=accident_id,
            status=result.status,
            accident=result.accident,
            calls=result.calls,
            repair_attempted=result.repair_attempted,
            validation_errors=result.validation_errors,
            latency_seconds=result.latency_seconds,
            error=result.error,
        )
        line = json.dumps(record.model_dump(mode="json"), ensure_ascii=False, allow_nan=False)
        self._file.write(line + "\n")
        self._file.flush()

    def __exit__(self, *exc_info) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None
