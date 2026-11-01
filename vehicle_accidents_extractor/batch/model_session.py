"""Keep one model connected while it extracts several setups of an accident batch."""

import os
from dataclasses import dataclass
from pathlib import Path

from ..artifact_paths import ArtifactPaths
from ..input_paths import InputPaths
from ..llm.config import Config, ModelConfig
from ..llm.llm_client import LLMClient
from .accident_batch_extractor import AccidentBatchExtractorBuilder
from .extraction_setups import ExtractionSetup


@dataclass(frozen=True)
class ModelSession:
    """Pair one selected model profile with the client configured for it."""

    model_profile: str
    model_config: ModelConfig
    llm_client: LLMClient

    def __post_init__(self) -> None:
        if self.llm_client.model != self.model_config.model:
            raise ValueError(
                f"LLM client model {self.llm_client.model!r} does not match "
                f"model profile {self.model_profile!r} ({self.model_config.model!r})"
            )
        if self.llm_client.base_url != self.model_config.base_url:
            raise ValueError(
                f"LLM client base URL {self.llm_client.base_url!r} does not match "
                f"model profile {self.model_profile!r} ({self.model_config.base_url!r})"
            )


def extract_setups_with_model(
    config: Config,
    model_profile: str,
    accident_batch: str,
    setups: list[ExtractionSetup],
    input_paths: InputPaths,
    artifact_paths: ArtifactPaths,
) -> list[Path]:
    """Extract the batch once per setup and return the saved extraction run paths.

    An unavailable model (missing API key, unreachable server, failed warm-up) is
    reported and skipped; setups already saved are still returned.
    """
    model_config = config.get_model(model_profile)
    api_key = "ollama" if model_config.is_local else os.getenv(model_config.api_key_env, "").strip()
    if not api_key:
        print(f"Skipping {model_profile}: missing {model_config.api_key_env}")
        return []

    saved_paths: list[Path] = []
    with LLMClient(
        base_url=model_config.base_url,
        api_key=api_key,
        model=model_config.model,
        timeout_seconds=config.timeout_seconds,
        max_retries=config.max_retries,
    ) as llm_client:
        model_session = ModelSession(model_profile, model_config, llm_client)
        if connection_error := llm_client.ping():
            print(f"Skipping {model_profile}: {connection_error}")
            return saved_paths

        for setup in setups:
            if model_config.is_local and (warm_up_error := llm_client.warm_up()):
                print(f"Skipping {model_profile}: warm-up failed: {warm_up_error}")
                return saved_paths
            batch_extractor = (
                AccidentBatchExtractorBuilder(config, input_paths)
                .for_accident_batch(accident_batch)
                .with_model_session(model_session)
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
