"""Build and extract all accident narratives in one batch."""

from __future__ import annotations

from datetime import datetime, timezone
import os
import platform
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from ..artifact_paths import ArtifactPaths
from ..extraction.accident_extractor import AccidentExtractor
from ..extraction.prompt_builder import PromptBuilder
from ..extraction.prompt_loader import load_extraction_prompts
from ..extraction.response_validator import ResponseValidator
from ..extraction_run_records import ExtractionRunMetadata
from ..input_paths import InputPaths
from ..llm.config import Config
from ..schema import VehicleAccident
from .accident_extraction_record_writer import AccidentExtractionRecordWriter

if TYPE_CHECKING:
    from .model_session import ModelSession


class AccidentBatchExtractor:
    def __init__(
        self,
        accident_extractor: AccidentExtractor,
        narrative_paths: list[Path],
        run_metadata: ExtractionRunMetadata,
        extraction_run_records_path: Path,
    ):
        self._accident_extractor = accident_extractor
        self._narrative_paths = narrative_paths
        self.run_metadata = run_metadata
        self.extraction_run_records_path = extraction_run_records_path

    def extract(self) -> int:
        with AccidentExtractionRecordWriter(
            self.extraction_run_records_path, self.run_metadata,
        ) as record_writer:
            processed_count = 0
            for narrative_path in self._narrative_paths:
                narrative = narrative_path.read_text(encoding="utf-8")
                outcome = self._accident_extractor.extract(narrative)
                record_writer.write(narrative_path.stem, outcome)
                processed_count += 1
        return processed_count


class AccidentBatchExtractorBuilder:
    def __init__(self, config: Config, input_paths: InputPaths):
        self._config = config
        self._input_paths = input_paths
        self._artifact_paths: ArtifactPaths | None = None
        self._accident_batch: str | None = None
        self._model_session: ModelSession | None = None
        self._prompt_version: str | None = None
        self._sampling_profile: str | None = None

    def for_accident_batch(self, accident_batch: str) -> "AccidentBatchExtractorBuilder":
        self._accident_batch = accident_batch
        return self

    def with_model_session(self, model_session: ModelSession) -> "AccidentBatchExtractorBuilder":
        self._model_session = model_session
        return self

    def with_prompt_version(self, prompt_version: str) -> "AccidentBatchExtractorBuilder":
        self._prompt_version = prompt_version
        return self

    def with_sampling_profile(self, sampling_profile: str) -> "AccidentBatchExtractorBuilder":
        self._sampling_profile = sampling_profile
        return self

    def saving_records_to(self, artifact_paths: ArtifactPaths) -> "AccidentBatchExtractorBuilder":
        self._artifact_paths = artifact_paths
        return self

    def build(self) -> AccidentBatchExtractor:
        accident_batch = self._required(self._accident_batch, "accident batch")
        prompt_version = self._required(self._prompt_version, "prompt version")
        sampling_profile = self._required(self._sampling_profile, "sampling profile")
        if self._artifact_paths is None:
            raise ValueError("Artifact paths are required to build an accident batch extractor")
        if self._model_session is None:
            raise ValueError("A model session is required to build an accident batch extractor")

        model_profile = self._model_session.model_profile
        model_config = self._model_session.model_config
        llm_client = self._model_session.llm_client
        sampling = self._config.get_sampling(sampling_profile)
        prompts = load_extraction_prompts(self._input_paths.prompts_directory, prompt_version)
        narrative_paths = self._input_paths.accident_narrative_paths(accident_batch)
        run_metadata = ExtractionRunMetadata(
            run_id=uuid4().hex,
            started_at=datetime.now(timezone.utc),
            batch=accident_batch,
            model_profile=model_profile,
            model=model_config.model,
            base_url=model_config.base_url,
            prompt_version=prompts.prompt_version,
            system_hash=prompts.system_hash,
            repair_hash=prompts.repair_hash,
            sampling_profile=sampling_profile,
            temperature=sampling.temperature,
            top_p=sampling.top_p,
            timeout_seconds=self._config.timeout_seconds,
            max_retries=self._config.max_retries,
            max_tokens=self._config.max_tokens,
            price_per_1m=model_config.price_per_1m,
            machine=(
                f"{platform.system()}-{platform.release()} · {platform.processor()} · "
                f"{os.cpu_count()} logical CPUs"
            ),
        )
        extraction_run_records_path = self._artifact_paths.extraction_run_records_path(run_metadata)
        accident_extractor = AccidentExtractor(
            llm_client,
            PromptBuilder(prompts.system_prompt, prompts.repair_prompt),
            ResponseValidator(VehicleAccident),
            sampling,
            self._config.max_tokens,
        )
        return AccidentBatchExtractor(
            accident_extractor,
            narrative_paths,
            run_metadata,
            extraction_run_records_path,
        )

    @staticmethod
    def _required(selection_value: str | None, selection_name: str) -> str:
        if selection_value is None:
            raise ValueError(f"{selection_name} is required to build an accident batch extractor")
        return selection_value
