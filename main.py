"""Run one model, prompt version and sampling profile over a batch of accident narratives."""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from vehicle_accidents_extractor.artifact_paths import ArtifactPaths
from vehicle_accidents_extractor.input_paths import InputPaths
from vehicle_accidents_extractor.llm.config import ModelConfig, load_config
from vehicle_accidents_extractor.batch.accident_batch_extractor import (
    AccidentBatchExtractorBuilder,
)


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="openrouter")
    parser.add_argument("--prompt", default="v1")
    parser.add_argument("--sampling", default="deterministic")
    parser.add_argument("--batch", default="batch-01")
    return parser.parse_args()


def resolve_api_key(model_config: ModelConfig) -> str | None:
    if model_config.api_key_env is None:
        return "ollama"
    return os.getenv(model_config.api_key_env, "").strip() or None


def run(args: argparse.Namespace) -> None:
    load_dotenv(ROOT / ".env")
    config = load_config()
    model_config = config.get_model(args.model)
    api_key = resolve_api_key(model_config)
    if api_key is None:
        print(f"Skipping {args.model}: missing {model_config.api_key_env}")
        return

    with (
        AccidentBatchExtractorBuilder(config, InputPaths(ROOT))
        .for_accident_batch(args.batch)
        .with_model_profile(args.model, api_key)
        .with_prompt_version(args.prompt)
        .with_sampling_profile(args.sampling)
        .saving_records_to(ArtifactPaths(ROOT))
        .build()
    ) as batch_extractor:
        if connection_error := batch_extractor.ping():
            print(f"Skipping {args.model}: {connection_error}")
            return

        processed_count = batch_extractor.extract()

    print(
        f"Saved {processed_count} extraction records to "
        f"{batch_extractor.extraction_run_records_path}"
    )


def main() -> None:
    args = parse_args()
    try:
        run(args)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
