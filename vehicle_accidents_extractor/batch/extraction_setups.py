"""Combine prompt versions and sampling profiles into the setups a comparison runs."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractionSetup:
    prompt_version: str
    sampling_profile: str


def extraction_setups(
    prompt_versions: list[str], sampling_profiles: list[str],
) -> list[ExtractionSetup]:
    """Every combination of prompt version and sampling profile, ordered by prompt version."""
    return [
        ExtractionSetup(prompt_version, sampling_profile)
        for prompt_version in prompt_versions
        for sampling_profile in sampling_profiles
    ]
