"""Run accident extraction: one setup by default, or every LLM profile, prompt and sampling setup with --all."""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from vehicle_accidents_extractor.artifact_paths import ArtifactPaths
from vehicle_accidents_extractor.batch.extract_setups_with_llm import (
    LLMUnavailable,
    extract_setups_with_llm,
)
from vehicle_accidents_extractor.batch.extraction_setups import (
    ExtractionSetup,
    extraction_setups,
)
from vehicle_accidents_extractor.evaluation.extraction_run_comparison import (
    format_extraction_run_comparison,
)
from vehicle_accidents_extractor.evaluation.golden_record_reader import read_golden_records
from vehicle_accidents_extractor.extraction.prompt_loader import available_prompt_versions
from vehicle_accidents_extractor.input_paths import InputPaths
from vehicle_accidents_extractor.llm.config import LLMConfig, load_config


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--llm-profile", default="openrouter")
    parser.add_argument("--prompt", default="v1")
    parser.add_argument("--sampling", default="deterministic")
    parser.add_argument("--batch", default="batch-01")
    parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Run every configured LLM profile with every prompt version and sampling profile, "
            "then print a comparison table. Ignores --llm-profile, --prompt and --sampling."
        ),
    )
    return parser.parse_args()


def resolve_api_key(llm_config: LLMConfig) -> str | None:
    """Return the API key for an LLM profile, or None if a required key is missing.

    A local Ollama server needs no real key; the client still requires a value.
    """
    if llm_config.is_local:
        return "ollama"
    return os.getenv(llm_config.api_key_env, "").strip() or None


def run(args: argparse.Namespace) -> None:
    load_dotenv(ROOT / ".env")
    config = load_config()
    input_paths = InputPaths(ROOT)
    artifact_paths = ArtifactPaths(ROOT)

    if args.all:
        llm_profiles = list(config.llm_profiles)
        setups = extraction_setups(
            available_prompt_versions(input_paths.prompts_directory), list(config.sampling),
        )
    else:
        llm_profiles = [args.llm_profile]
        setups = [ExtractionSetup(args.prompt, args.sampling)]

    saved_paths: list[Path] = []
    for llm_profile in llm_profiles:
        llm_config = config.get_llm_config(llm_profile)
        api_key = resolve_api_key(llm_config)
        if api_key is None:
            if not args.all:
                raise ValueError(
                    f"Missing {llm_config.api_key_env} for LLM profile {llm_profile!r}"
                )
            print(f"Skipping {llm_profile}: missing {llm_config.api_key_env}")
            continue

        try:
            saved_paths += extract_setups_with_llm(
                config, llm_profile, api_key, args.batch, setups, input_paths, artifact_paths,
            )
        except LLMUnavailable as unavailable:
            if not args.all:
                raise LLMUnavailable(
                    f"{llm_profile} unavailable: {unavailable.reason}",
                    saved_paths=unavailable.saved_paths,
                ) from unavailable
            print(f"Skipping {llm_profile}: {unavailable.reason}")
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
