"""Build and extract all accident narratives in one batch."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ..artifact_paths import ArtifactPaths
from ..extraction.accident_extractor import AccidentExtractor
from ..extraction.prompt_builder import PromptBuilder
from ..extraction.prompt_loader import load_extraction_prompts
from ..extraction.response_validator import ResponseValidator
from ..extraction_run_records import ExtractionRunMetadata
from ..input_paths import InputPaths
from ..llm.config import Config
from ..llm.llm_client import LLMClient
from ..schema import VehicleAccident
from .accident_extraction_record_writer import AccidentExtractionRecordWriter


class AccidentBatchExtractor:
    def __init__(
        self,
        llm_client: LLMClient,
        accident_extractor: AccidentExtractor,
        narrative_paths: list[Path],
        run_metadata: ExtractionRunMetadata,
        extraction_run_records_path: Path,
    ):
        self._llm_client = llm_client
        self._accident_extractor = accident_extractor
        self._narrative_paths = narrative_paths
        self.run_metadata = run_metadata
        self.extraction_run_records_path = extraction_run_records_path

    def __enter__(self) -> "AccidentBatchExtractor":
        return self

    def __exit__(self, *exc_info) -> None:
        self._llm_client.close()

    def ping(self) -> str | None:
        return self._llm_client.ping()

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
        self._model_profile: str | None = None
        self._api_key: str | None = None
        self._prompt_version: str | None = None
        self._sampling_profile: str | None = None

    def for_accident_batch(self, accident_batch: str) -> "AccidentBatchExtractorBuilder":
        self._accident_batch = accident_batch
        return self

    def with_model_profile(self, model_profile: str, api_key: str) -> "AccidentBatchExtractorBuilder":
        self._model_profile = model_profile
        self._api_key = api_key
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
        model_profile = self._required(self._model_profile, "model profile")
        api_key = self._required(self._api_key, "API key")
        prompt_version = self._required(self._prompt_version, "prompt version")
        sampling_profile = self._required(self._sampling_profile, "sampling profile")
        if self._artifact_paths is None:
            raise ValueError("Artifact paths are required to build an accident batch extractor")

        model_config = self._config.get_model(model_profile)
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
        )
        extraction_run_records_path = self._artifact_paths.extraction_run_records_path(run_metadata)
        llm_client = LLMClient(
            base_url=model_config.base_url,
            api_key=api_key,
            model=model_config.model,
            timeout_seconds=self._config.timeout_seconds,
            max_retries=self._config.max_retries,
        )
        accident_extractor = AccidentExtractor(
            llm_client,
            PromptBuilder(prompts.system_prompt, prompts.repair_prompt),
            ResponseValidator(VehicleAccident),
            sampling,
            self._config.max_tokens,
        )
        return AccidentBatchExtractor(
            llm_client,
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
