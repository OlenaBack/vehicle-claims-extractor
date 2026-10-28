"""Resolve accident batch inputs and prompt locations."""

from pathlib import Path


class InputPaths:
    def __init__(self, project_root: Path):
        self.batches_directory = project_root / "data" / "batches"
        self.prompts_directory = project_root / "prompts"

    def accident_description_files(self, accident_batch: str) -> list[Path]:
        """Return the batch's accident descriptions in a fixed order; raise if none exist."""
        texts_directory = self.batches_directory / accident_batch / "texts"
        description_file_paths = sorted(texts_directory.glob("*.txt"))
        if not description_file_paths:
            raise ValueError(f"No accident descriptions found in {texts_directory}")
        return description_file_paths

    def golden_labels_path(self, accident_batch: str) -> Path:
        return self.batches_directory / accident_batch / "golden.jsonl"
