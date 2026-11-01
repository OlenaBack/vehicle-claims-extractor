"""Keep one LLM connected while it extracts several setups of an accident batch."""

from pathlib import Path

from ..artifact_paths import ArtifactPaths
from ..input_paths import InputPaths
from ..llm.config import Config
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


def extract_setups_with_llm(
    config: Config,
    llm_profile: str,
    api_key: str,
    accident_batch: str,
    setups: list[ExtractionSetup],
    input_paths: InputPaths,
    artifact_paths: ArtifactPaths,
) -> list[Path]:
    """Extract the batch once per setup and return its saved extraction run paths.

    Connection-check and warm-up failures raise LLMUnavailable, which carries
    paths saved before the failure.
    """
    llm_config = config.get_llm_config(llm_profile)
    saved_paths: list[Path] = []
    with LLMClient(
        base_url=llm_config.base_url,
        api_key=api_key,
        model=llm_config.model,
        timeout_seconds=config.timeout_seconds,
        max_retries=config.max_retries,
    ) as llm_client:
        if connection_error := llm_client.ping():
            raise LLMUnavailable(
                connection_error,
                saved_paths=tuple(saved_paths),
            )

        for setup in setups:
            if llm_config.is_local and (warm_up_error := llm_client.warm_up()):
                raise LLMUnavailable(
                    f"warm-up failed: {warm_up_error}",
                    saved_paths=tuple(saved_paths),
                )
            batch_extractor = (
                AccidentBatchExtractorBuilder(config, input_paths)
                .for_accident_batch(accident_batch)
                .with_llm_profile(llm_profile)
                .with_llm_client(llm_client)
                .with_prompt_version(setup.prompt_version)
                .with_sampling_profile(setup.sampling_profile)
                .saving_records_to(artifact_paths)
                .build()
            )
            processed_count = batch_extractor.extract()
            print(
                f"Saved {processed_count} extraction records to "
                f"{batch_extractor.extraction_run_records_path}"
            )
            saved_paths.append(batch_extractor.extraction_run_records_path)
    return saved_paths
