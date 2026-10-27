"""Run one model, prompt version and sampling profile over the accident reports."""

import argparse
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

from vehicle_accidents_extractor.extraction.accident_extractor import AccidentExtractor
from vehicle_accidents_extractor.extraction.prompt_builder import PromptBuilder
from vehicle_accidents_extractor.extraction.prompt_loader import (
    ExtractionPrompts,
    load_extraction_prompts,
)
from vehicle_accidents_extractor.extraction.response_validator import ResponseValidator
from vehicle_accidents_extractor.llm.config import Config, ModelConfig, Sampling, load_config
from vehicle_accidents_extractor.llm.llm_client import LLMClient
from vehicle_accidents_extractor.run_records import RunMetadata
from vehicle_accidents_extractor.runs.accident_batch_processor import AccidentBatchProcessor
from vehicle_accidents_extractor.runs.extraction_result_writer import ExtractionResultWriter
from vehicle_accidents_extractor.schema import VehicleAccident


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="openrouter")
    parser.add_argument("--prompt", default="v1")
    parser.add_argument("--sampling", default="deterministic")
    parser.add_argument("--dataset", default="batch-01")
    return parser.parse_args()


def resolve_api_key(model_config: ModelConfig) -> str | None:
    if model_config.api_key_env is None:
        return "ollama"
    return os.getenv(model_config.api_key_env, "").strip() or None


def build_run_metadata(
    *,
    model_profile: str,
    sampling_profile: str,
    dataset: str,
    config: Config,
    model_config: ModelConfig,
    sampling: Sampling,
    prompts: ExtractionPrompts,
) -> RunMetadata:
    return RunMetadata(
        run_id=uuid4().hex,
        started_at=datetime.now(timezone.utc),
        dataset=dataset,
        model_profile=model_profile,
        model=model_config.model,
        base_url=model_config.base_url,
        prompt_version=prompts.version,
        system_hash=prompts.system_hash,
        repair_hash=prompts.repair_hash,
        sampling_profile=sampling_profile,
        temperature=sampling.temperature,
        top_p=sampling.top_p,
        timeout_seconds=config.timeout_seconds,
        max_retries=config.max_retries,
        max_tokens=config.max_tokens,
        price_per_1m=model_config.price_per_1m,
    )


def run(args: argparse.Namespace) -> None:
    load_dotenv(ROOT / ".env")
    config = load_config()
    model_config = config.get_model(args.model)
    sampling = config.get_sampling(args.sampling)
    api_key = resolve_api_key(model_config)
    if api_key is None:
        print(f"Skipping {args.model}: missing {model_config.api_key_env}")
        return

    prompts = load_extraction_prompts(ROOT / "prompts", args.prompt)
    dataset_directory = ROOT / "data" / "batches" / args.dataset
    documents = sorted((dataset_directory / "texts").glob("*.txt"))
    if not documents:
        raise ValueError(f"No accident text documents found in {dataset_directory / 'texts'}")

    run_metadata = build_run_metadata(
        model_profile=args.model,
        sampling_profile=args.sampling,
        dataset=args.dataset,
        config=config,
        model_config=model_config,
        sampling=sampling,
        prompts=prompts,
    )

    with LLMClient(
        base_url=model_config.base_url,
        api_key=api_key,
        model=model_config.model,
        timeout_seconds=config.timeout_seconds,
        max_retries=config.max_retries,
    ) as llm:
        connection_error = llm.ping()
        if connection_error:
            print(f"Skipping {args.model}: {connection_error}")
            return

        extractor = AccidentExtractor(
            llm,
            PromptBuilder(prompts.system_prompt, prompts.repair_prompt),
            ResponseValidator(VehicleAccident),
            sampling,
            config.max_tokens,
        )
        model_name = model_config.model.replace("/", "-")
        filename = f"{args.model}__{model_name}__{args.prompt}__{args.sampling}__{run_metadata.run_id}.jsonl"
        output_path = ROOT / "results" / run_metadata.dataset / filename
        with ExtractionResultWriter(output_path, run_metadata) as writer:
            processed = AccidentBatchProcessor(extractor, writer).run(documents)

        print(f"Saved {processed} document results to {output_path}")


def main() -> None:
    args = parse_args()
    try:
        run(args)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
