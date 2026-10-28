"""Resolve accident batch inputs and prompt locations."""

from pathlib import Path


class InputPaths:
    def __init__(self, project_root: Path):
        self.batches_directory = project_root / "data" / "batches"
        self.prompts_directory = project_root / "prompts"

    def list_accident_batch_files(self, accident_batch: str) -> list[Path]:
        """Return the batch's text file paths in a fixed order; raise if there are none."""
        accident_batch_texts_directory = self.batches_directory / accident_batch / "texts"
        accident_batch_file_paths = sorted(accident_batch_texts_directory.glob("*.txt"))
        if not accident_batch_file_paths:
            raise ValueError(f"No accident descriptions found in {accident_batch_texts_directory}")
        return accident_batch_file_paths

    def golden_labels_path(self, accident_batch: str) -> Path:
        return self.batches_directory / accident_batch / "golden.jsonl"
