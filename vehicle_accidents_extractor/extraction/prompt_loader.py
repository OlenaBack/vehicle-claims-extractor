"""Load a versioned pair of extraction prompts."""

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExtractionPrompts:
    prompt_version: str
    system_prompt: str
    repair_prompt: str
    system_hash: str
    repair_hash: str


def load_extraction_prompts(prompts_directory: Path, prompt_version: str) -> ExtractionPrompts:
    prompt_version_directory = prompts_directory / prompt_version
    system_prompt = (prompt_version_directory / "system.txt").read_text(encoding="utf-8")
    repair_prompt = (prompt_version_directory / "repair.txt").read_text(encoding="utf-8")

    return ExtractionPrompts(
        prompt_version=prompt_version,
        system_prompt=system_prompt,
        repair_prompt=repair_prompt,
        system_hash=hashlib.sha256(system_prompt.encode("utf-8")).hexdigest(),
        repair_hash=hashlib.sha256(repair_prompt.encode("utf-8")).hexdigest(),
    )
