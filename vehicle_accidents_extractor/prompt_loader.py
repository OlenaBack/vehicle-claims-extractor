"""Load a versioned pair of extraction prompts."""

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExtractionPrompts:
    version: str
    system_prompt: str
    repair_prompt: str
    system_hash: str
    repair_hash: str


def load_extraction_prompts(prompts_directory: Path, version: str) -> ExtractionPrompts:
    directory = prompts_directory / version
    system = (directory / "system.txt").read_text(encoding="utf-8")
    repair = (directory / "repair.txt").read_text(encoding="utf-8")

    return ExtractionPrompts(
        version=version,
        system_prompt=system,
        repair_prompt=repair,
        system_hash=hashlib.sha256(system.encode("utf-8")).hexdigest(),
        repair_hash=hashlib.sha256(repair.encode("utf-8")).hexdigest(),
    )
