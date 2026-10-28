"""Resolve accident batch inputs and prompt locations."""

from pathlib import Path


class InputPaths:
    def __init__(self, project_root: Path):
        self.batches_directory = project_root / "data" / "batches"
        self.prompts_directory = project_root / "prompts"

    def accident_batch_input_paths(self, accident_batch: str) -> list[Path]:
        """Return the batch's input paths in a fixed order; raise if none exist."""
        accident_batch_input_directory = self.batches_directory / accident_batch / "texts"
        accident_batch_input_paths = sorted(accident_batch_input_directory.glob("*.txt"))
        if not accident_batch_input_paths:
            raise ValueError(f"No accident narratives found in {accident_batch_input_directory}")
        return accident_batch_input_paths

    def golden_labels_path(self, accident_batch: str) -> Path:
        return self.batches_directory / accident_batch / "golden.jsonl"
