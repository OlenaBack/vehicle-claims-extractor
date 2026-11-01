"""Run accident extraction: one setup by default, or every LLM profile, prompt and sampling setup with --all."""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from vehicle_accidents_extractor.artifact_paths import ArtifactPaths
from vehicle_accidents_extractor.batch.accident_batch_extractions import (
    AccidentBatchExtractions,
    LLMUnavailable,
)
from vehicle_accidents_extractor.batch.extraction_setups import (
    ExtractionSetup,
    extraction_setups,
)
from vehicle_accidents_extractor.evaluation.extraction_run_comparison import (
    compare_extraction_runs,
    format_terminal_extraction_run_comparison,
)
from vehicle_accidents_extractor.extraction.prompt_loader import available_prompt_versions
from vehicle_accidents_extractor.input_paths import InputPaths
from vehicle_accidents_extractor.llm.llm_config import LLMProfile
from vehicle_accidents_extractor.llm.llm_config_reader import read_llm_config


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--llm-profile", default="openrouter")
    parser.add_argument("--prompt", default="v1")
    parser.add_argument("--sampling-profile", default="deterministic")
    parser.add_argument("--batch", default="batch-01")
    parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Run every configured LLM profile with every prompt version and sampling profile, "
            "then print a comparison table. Ignores --llm-profile, --prompt and --sampling-profile."
        ),
    )
    return parser.parse_args()


def resolve_api_key(llm_profile: LLMProfile) -> str | None:
    """Return the API key for an LLM profile, or None if a required key is missing.

    A local Ollama server needs no real key; the client still requires a value.
    """
    if llm_profile.is_local:
        return "ollama"
    return os.getenv(llm_profile.api_key_env, "").strip() or None


def run(args: argparse.Namespace) -> None:
    load_dotenv(ROOT / ".env")
    input_paths = InputPaths(ROOT)
    llm_config = read_llm_config(input_paths.llm_config_path)
    artifact_paths = ArtifactPaths(ROOT)

    if args.all:
        llm_profile_names = list(llm_config.llm_profiles)
        setups = extraction_setups(
            available_prompt_versions(input_paths.prompts_directory),
            list(llm_config.sampling_profiles),
        )
    else:
        llm_profile_names = [args.llm_profile]
        setups = [ExtractionSetup(args.prompt, args.sampling_profile)]

    accident_batch_extractions = AccidentBatchExtractions(
        llm_config=llm_config,
        accident_batch=args.batch,
        extraction_setups=setups,
        input_paths=input_paths,
        artifact_paths=artifact_paths,
    )
    saved_paths: list[Path] = []
    for llm_profile_name in llm_profile_names:
        llm_profile = llm_config.get_llm_profile(llm_profile_name)
        api_key = resolve_api_key(llm_profile)
        if api_key is None:
            if not args.all:
                raise ValueError(
                    f"Missing {llm_profile.api_key_env} for LLM profile {llm_profile_name!r}"
                )
            print(f"Skipping {llm_profile_name}: missing {llm_profile.api_key_env}")
            continue

        try:
            saved_paths += accident_batch_extractions.extract_with(llm_profile_name, api_key)
        except LLMUnavailable as unavailable:
            if not args.all:
                raise LLMUnavailable(
                    f"{llm_profile_name} unavailable: {unavailable.reason}",
                    saved_paths=unavailable.saved_paths,
                ) from unavailable
            print(f"Skipping {llm_profile_name}: {unavailable.reason}")
            saved_paths += unavailable.saved_paths

    if args.all and saved_paths:
        rows = compare_extraction_runs(saved_paths, input_paths)
        print("\n" + format_terminal_extraction_run_comparison(rows))


def main() -> None:
    args = parse_args()
    try:
        run(args)
    except (OSError, ValueError, LLMUnavailable) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
