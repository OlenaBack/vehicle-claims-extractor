"""Build and execute one configured accident extraction run."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ..extraction.accident_extractor import AccidentExtractor
from ..extraction.prompt_builder import PromptBuilder
from ..extraction.prompt_loader import load_extraction_prompts
from ..extraction.response_validator import ResponseValidator
from ..extraction_run_records import ExtractionRunMetadata
from ..input_paths import InputPaths
from ..llm.config import Config, ModelConfig, Sampling
from ..llm.llm_client import LLMClient
from ..schema import VehicleAccident
from .accident_extraction_runner import AccidentExtractionRunner
from .extraction_record_writer import ExtractionRecordWriter


class ExtractionRun:
    def __init__(
        self,
        llm: LLMClient,
        extractor: AccidentExtractor,
        accident_file_paths: list[Path],
        run_metadata: ExtractionRunMetadata,
    ):
        self._llm = llm
        self._extractor = extractor
        self._accident_file_paths = accident_file_paths
        self.run_metadata = run_metadata

    def __enter__(self) -> "ExtractionRun":
        return self

    def __exit__(self, *exc_info) -> None:
        self._llm.close()

    def ping(self) -> str | None:
        return self._llm.ping()

    def execute(self, records_path: Path) -> int:
        with ExtractionRecordWriter(records_path, self.run_metadata) as writer:
            return AccidentExtractionRunner(self._extractor, writer).run(self._accident_file_paths)


class ExtractionRunBuilder:
    def __init__(self, config: Config, input_paths: InputPaths):
        self._config = config
        self._input_paths = input_paths
        self._accident_batch: str | None = None
        self._model_profile: str | None = None
        self._api_key: str | None = None
        self._prompt_version: str | None = None
        self._sampling_profile: str | None = None

    def for_accident_batch(self, accident_batch: str) -> "ExtractionRunBuilder":
        self._accident_batch = accident_batch
        return self

    def with_model_profile(self, model_profile: str, api_key: str) -> "ExtractionRunBuilder":
        self._model_profile = model_profile
        self._api_key = api_key
        return self

    def with_prompt_version(self, prompt_version: str) -> "ExtractionRunBuilder":
        self._prompt_version = prompt_version
        return self

    def with_sampling_profile(self, sampling_profile: str) -> "ExtractionRunBuilder":
        self._sampling_profile = sampling_profile
        return self

    def build(self) -> ExtractionRun:
        accident_batch = self._required(self._accident_batch, "accident batch")
        model_profile = self._required(self._model_profile, "model profile")
        api_key = self._required(self._api_key, "API key")
        prompt_version = self._required(self._prompt_version, "prompt version")
        sampling_profile = self._required(self._sampling_profile, "sampling profile")

        model_config = self._config.get_model(model_profile)
        sampling = self._config.get_sampling(sampling_profile)
        prompts = load_extraction_prompts(self._input_paths.prompts_directory, prompt_version)
        accident_file_paths = self._input_paths.list_accident_batch_files(accident_batch)
        run_metadata = ExtractionRunMetadata(
            run_id=uuid4().hex,
            started_at=datetime.now(timezone.utc),
            batch=accident_batch,
            model_profile=model_profile,
            model=model_config.model,
            base_url=model_config.base_url,
            prompt_version=prompts.version,
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
        llm = LLMClient(
            base_url=model_config.base_url,
            api_key=api_key,
            model=model_config.model,
            timeout_seconds=self._config.timeout_seconds,
            max_retries=self._config.max_retries,
        )
        extractor = AccidentExtractor(
            llm,
            PromptBuilder(prompts.system_prompt, prompts.repair_prompt),
            ResponseValidator(VehicleAccident),
            sampling,
            self._config.max_tokens,
        )
        return ExtractionRun(llm, extractor, accident_file_paths, run_metadata)

    @staticmethod
    def _required(selection_value: str | None, selection_name: str) -> str:
        if selection_value is None:
            raise ValueError(f"{selection_name} is required to build an extraction run")
        return selection_value
