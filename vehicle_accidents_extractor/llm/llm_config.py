"""Define validated LLM and sampling profile settings."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


Price = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class LLMProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_url: str
    api_key_env: str | None = Field(default=None, min_length=1)
    model: str = Field(min_length=1)
    price_per_1m: tuple[Price, Price]

    @property
    def is_local(self) -> bool:
        """A local model needs no API key."""
        return self.api_key_env is None

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


class SamplingProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperature: float = Field(ge=0, le=2, allow_inf_nan=False)
    top_p: float = Field(gt=0, le=1, allow_inf_nan=False)


class LLMConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeout_seconds: int = Field(default=60, gt=0, strict=True)
    max_retries: int = Field(default=2, ge=0, strict=True)
    max_tokens: int = Field(default=800, gt=0, strict=True)
    llm_profiles: dict[str, LLMProfile] = Field(min_length=1)
    sampling_profiles: dict[str, SamplingProfile] = Field(min_length=1)

    def get_llm_profile(self, llm_profile_name: str) -> LLMProfile:
        if llm_profile_name not in self.llm_profiles:
            raise ValueError(
                f"Unknown LLM profile {llm_profile_name!r}. "
                f"Available: {', '.join(self.llm_profiles)}"
            )
        return self.llm_profiles[llm_profile_name]

    def get_sampling_profile(self, sampling_profile_name: str) -> SamplingProfile:
        if sampling_profile_name not in self.sampling_profiles:
            raise ValueError(
                f"Unknown sampling profile {sampling_profile_name!r}. "
                f"Available: {', '.join(self.sampling_profiles)}"
            )
        return self.sampling_profiles[sampling_profile_name]
