"""Load and validate run settings. Resolve API keys separately at runtime."""

import tomllib
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"
Price = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_url: str
    api_key_env: str | None = Field(default=None, min_length=1)
    model: str = Field(min_length=1)
    price_per_1m: tuple[Price, Price]

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        HttpUrl(value)
        return value

    @field_validator("model", "api_key_env")
    @classmethod
    def reject_surrounding_whitespace(cls, value: str | None) -> str | None:
        if value is not None and (not value.strip() or value != value.strip()):
            raise ValueError("must be nonempty and have no surrounding whitespace")
        return value


class Sampling(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperature: float = Field(ge=0, le=2, allow_inf_nan=False)
    top_p: float = Field(gt=0, le=1, allow_inf_nan=False)


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeout_seconds: int = Field(default=60, gt=0, strict=True)
    max_retries: int = Field(default=2, ge=0, strict=True)
    max_tokens: int = Field(default=800, gt=0, strict=True)
    models: dict[str, ModelConfig] = Field(min_length=1)
    sampling: dict[str, Sampling] = Field(min_length=1)

    def get_model(self, name: str) -> ModelConfig:
        if name not in self.models:
            raise ValueError(
                f"Unknown model profile {name!r}. Available: {', '.join(self.models)}"
            )
        return self.models[name]

    def get_sampling(self, name: str) -> Sampling:
        if name not in self.sampling:
            raise ValueError(
                f"Unknown sampling profile {name!r}. Available: {', '.join(self.sampling)}"
            )
        return self.sampling[name]


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Config:
    """Read TOML and validate it without loading or requiring credentials.

    The default path is relative to the project; explicit paths are relative
    to the caller's working directory. File, TOML and validation errors propagate.
    """
    return Config.model_validate(tomllib.loads(path.read_text(encoding="utf-8")))
