"""Load a versioned pair of extraction prompts."""

import hashlib
from dataclasses import dataclass
from pathlib import Path


SYSTEM_PROMPT_FILENAME = "system.txt"
REPAIR_PROMPT_FILENAME = "repair.txt"


@dataclass(frozen=True)
class ExtractionPrompts:
    prompt_version: str
    system_prompt: str
    repair_prompt: str
    system_hash: str
    repair_hash: str


def available_prompt_versions(prompts_directory: Path) -> list[str]:
    """Prompt versions that have both a system and a repair prompt, sorted; raise if none."""
    prompt_versions = sorted(
        path.name
        for path in prompts_directory.iterdir()
        if (path / SYSTEM_PROMPT_FILENAME).is_file() and (path / REPAIR_PROMPT_FILENAME).is_file()
    )
    if not prompt_versions:
        raise ValueError(f"No complete prompt versions found in {prompts_directory}")
    return prompt_versions


def load_extraction_prompts(prompts_directory: Path, prompt_version: str) -> ExtractionPrompts:
    prompt_version_directory = prompts_directory / prompt_version
    system_prompt = (prompt_version_directory / SYSTEM_PROMPT_FILENAME).read_text(encoding="utf-8")
    repair_prompt = (prompt_version_directory / REPAIR_PROMPT_FILENAME).read_text(encoding="utf-8")

    return ExtractionPrompts(
        prompt_version=prompt_version,
        system_prompt=system_prompt,
        repair_prompt=repair_prompt,
        system_hash=hashlib.sha256(system_prompt.encode("utf-8")).hexdigest(),
        repair_hash=hashlib.sha256(repair_prompt.encode("utf-8")).hexdigest(),
    )
