"""Resolve paths for saved extraction records."""

from pathlib import Path

from .extraction_run_records import ExtractionRunMetadata


class ArtifactPaths:
    def __init__(self, project_root: Path):
        self.extractions_directory = project_root / "extractions"

    def extraction_run_records_path(self, run_metadata: ExtractionRunMetadata) -> Path:
        """Return the path for one run's JSONL extraction records."""
        file_safe_model_id = run_metadata.model.replace("/", "-")
        filename = (
            f"{run_metadata.model_profile}__{file_safe_model_id}__"
            f"{run_metadata.prompt_version}__{run_metadata.sampling_profile}__"
            f"{run_metadata.run_id}.jsonl"
        )
        return self.extractions_directory / run_metadata.batch / filename
