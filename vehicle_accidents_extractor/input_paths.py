"""Resolve accident batch inputs and prompt locations."""

from pathlib import Path


class InputPaths:
    def __init__(self, project_root: Path):
        self.batches_directory = project_root / "data" / "batches"
        self.prompts_directory = project_root / "prompts"

    def accident_narrative_paths(self, accident_batch: str) -> list[Path]:
        """Return the batch's narrative paths in a fixed order; raise if none exist."""
        narratives_directory = self.batches_directory / accident_batch / "texts"
        narrative_paths = sorted(narratives_directory.glob("*.txt"))
        if not narrative_paths:
            raise ValueError(f"No accident narratives found in {narratives_directory}")
        return narrative_paths

    def golden_labels_path(self, accident_batch: str) -> Path:
        return self.batches_directory / accident_batch / "golden.jsonl"
