"""Run extraction across accident descriptions and write each extraction record."""

from collections.abc import Iterable
from pathlib import Path

from ..extraction.accident_extractor import AccidentExtractor
from .extraction_record_writer import ExtractionRecordWriter


class AccidentExtractionRunner:
    def __init__(
        self,
        extractor: AccidentExtractor,
        writer: ExtractionRecordWriter,
    ):
        self._extractor = extractor
        self._writer = writer

    def run(self, accident_file_paths: Iterable[Path]) -> int:
        processed_count = 0

        for accident_file in accident_file_paths:
            text = accident_file.read_text(encoding="utf-8")
            outcome = self._extractor.extract(text)
            self._writer.write(accident_file.stem, outcome)
            processed_count += 1

        return processed_count
