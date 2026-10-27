"""Process accident text files through extraction and result writing."""

from collections.abc import Iterable
from pathlib import Path

from ..extraction.accident_extractor import AccidentExtractor
from .extraction_result_writer import ExtractionResultWriter


class AccidentBatchProcessor:
    def __init__(
        self,
        extractor: AccidentExtractor,
        writer: ExtractionResultWriter,
    ):
        self._extractor = extractor
        self._writer = writer

    def run(self, documents: Iterable[Path]) -> int:
        processed = 0

        for document in documents:
            text = document.read_text(encoding="utf-8")
            result = self._extractor.extract(text)
            self._writer.write(document.stem, result)
            processed += 1

        return processed
