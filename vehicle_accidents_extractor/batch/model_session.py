"""Keep one model connected while it extracts several setups of an accident batch."""

import os
from pathlib import Path

from ..artifact_paths import ArtifactPaths
from ..input_paths import InputPaths
from ..llm.config import Config
from ..llm.llm_client import LLMClient
from .accident_batch_extractor import AccidentBatchExtractorBuilder
from .extraction_setups import ExtractionSetup


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
                .with_model_profile(model_profile)
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
