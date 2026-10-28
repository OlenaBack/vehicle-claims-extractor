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

    def run(self, description_files: Iterable[Path]) -> int:
        processed = 0

        for description_file in description_files:
            text = description_file.read_text(encoding="utf-8")
            result = self._extractor.extract(text)
            self._writer.write(description_file.stem, result)
            processed += 1

        return processed
