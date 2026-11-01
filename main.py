"""Run accident extraction: one setup by default, or every model, prompt and sampling setup with --all."""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from vehicle_accidents_extractor.artifact_paths import ArtifactPaths
from vehicle_accidents_extractor.batch.extraction_setups import (
    ExtractionSetup,
    extraction_setups,
)
from vehicle_accidents_extractor.batch.model_session import (
    LLMUnavailable,
    extract_setups_with_model,
)
from vehicle_accidents_extractor.evaluation.extraction_run_comparison import (
    format_extraction_run_comparison,
)
from vehicle_accidents_extractor.evaluation.golden_record_reader import read_golden_records
from vehicle_accidents_extractor.extraction.prompt_loader import available_prompt_versions
from vehicle_accidents_extractor.input_paths import InputPaths
from vehicle_accidents_extractor.llm.config import ModelConfig, load_config


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="openrouter")
    parser.add_argument("--prompt", default="v1")
    parser.add_argument("--sampling", default="deterministic")
    parser.add_argument("--batch", default="batch-01")
    parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Run every configured model with every prompt version and sampling profile, "
            "then print a comparison table. Ignores --model, --prompt and --sampling."
        ),
    )
    return parser.parse_args()


def resolve_api_key(model_config: ModelConfig) -> str | None:
    """Return the API key for an LLM profile, or None if a required key is missing.

    A local Ollama server needs no real key; the client still requires a value.
    """
    if model_config.is_local:
        return "ollama"
    return os.getenv(model_config.api_key_env, "").strip() or None


def run(args: argparse.Namespace) -> None:
    load_dotenv(ROOT / ".env")
    config = load_config()
    input_paths = InputPaths(ROOT)
    artifact_paths = ArtifactPaths(ROOT)

    if args.all:
        model_profiles = list(config.models)
        setups = extraction_setups(
            available_prompt_versions(input_paths.prompts_directory), list(config.sampling),
        )
    else:
        model_profiles = [args.model]
        setups = [ExtractionSetup(args.prompt, args.sampling)]

    saved_paths: list[Path] = []
    for model_profile in model_profiles:
        model_config = config.get_model(model_profile)
        api_key = resolve_api_key(model_config)
        if api_key is None:
            if not args.all:
                raise ValueError(
                    f"Missing {model_config.api_key_env} for LLM profile {model_profile!r}"
                )
            print(f"Skipping {model_profile}: missing {model_config.api_key_env}")
            continue

        try:
            saved_paths += extract_setups_with_model(
                config, model_profile, api_key, args.batch, setups, input_paths, artifact_paths,
            )
        except LLMUnavailable as unavailable:
            if not args.all:
                raise
            print(f"Skipping {model_profile}: {unavailable.reason}")
            saved_paths += unavailable.saved_paths

    if args.all and saved_paths:
        golden_records = read_golden_records(input_paths.golden_labels_path(args.batch))
        print("\n" + format_extraction_run_comparison(saved_paths, golden_records))


def main() -> None:
    args = parse_args()
    try:
        run(args)
    except (OSError, ValueError, LLMUnavailable) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
