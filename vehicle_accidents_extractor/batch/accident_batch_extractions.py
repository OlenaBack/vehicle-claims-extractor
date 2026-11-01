"""Extract one accident batch once for each extraction setup."""

from pathlib import Path

from ..artifact_paths import ArtifactPaths
from ..input_paths import InputPaths
from ..llm.llm_config import LLMConfig
from ..llm.llm_client import LLMClient
from .accident_batch_extractor import AccidentBatchExtractorBuilder
from .extraction_setups import ExtractionSetup


class LLMUnavailable(RuntimeError):
    """Raised when an LLM fails its connection check or warm-up."""

    def __init__(
        self,
        reason: str,
        *,
        saved_paths: tuple[Path, ...] = (),
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.saved_paths = saved_paths


class AccidentBatchExtractions:
    """The batch extractions of one accident batch, one per extraction setup."""

    def __init__(
        self,
        *,
        llm_config: LLMConfig,
        accident_batch: str,
        extraction_setups: list[ExtractionSetup],
        input_paths: InputPaths,
        artifact_paths: ArtifactPaths,
    ) -> None:
        self._llm_config = llm_config
        self._accident_batch = accident_batch
        self._extraction_setups = extraction_setups
        self._input_paths = input_paths
        self._artifact_paths = artifact_paths

    def extract_with(self, llm_profile_name: str, api_key: str) -> list[Path]:
        """Connect to the LLM profile, then extract the batch once per extraction setup."""
        llm_profile = self._llm_config.get_llm_profile(llm_profile_name)
        extraction_run_paths: list[Path] = []
        with LLMClient(
            base_url=llm_profile.base_url,
            api_key=api_key,
            model=llm_profile.model,
            timeout_seconds=self._llm_config.timeout_seconds,
            max_retries=self._llm_config.max_retries,
        ) as llm_client:
            if connection_error := llm_client.ping():
                raise LLMUnavailable(
                    connection_error,
                    saved_paths=tuple(extraction_run_paths),
                )

            for extraction_setup in self._extraction_setups:
                if llm_profile.is_local and (warm_up_error := llm_client.warm_up()):
                    raise LLMUnavailable(
                        f"warm-up failed: {warm_up_error}",
                        saved_paths=tuple(extraction_run_paths),
                    )
                accident_batch_extractor = (
                    AccidentBatchExtractorBuilder(self._llm_config, self._input_paths)
                    .for_accident_batch(self._accident_batch)
                    .with_llm_profile(llm_profile_name)
                    .with_llm_client(llm_client)
                    .with_prompt_version(extraction_setup.prompt_version)
                    .with_sampling_profile(extraction_setup.sampling_profile_name)
                    .saving_records_to(self._artifact_paths)
                    .build()
                )
                saved_record_count = accident_batch_extractor.extract()
                print(
                    f"Saved {saved_record_count} extraction records to "
                    f"{accident_batch_extractor.extraction_run_records_path}"
                )
                extraction_run_paths.append(accident_batch_extractor.extraction_run_records_path)
        return extraction_run_paths
