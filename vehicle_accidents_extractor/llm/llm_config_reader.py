"""Read and validate the LLM configuration file."""

import tomllib
from pathlib import Path

from .llm_config import LLMConfig


def read_llm_config(llm_config_path: Path) -> LLMConfig:
    """Read a TOML file and validate its LLM and sampling profiles."""
    contents = tomllib.loads(llm_config_path.read_text(encoding="utf-8"))
    return LLMConfig.model_validate(contents)
