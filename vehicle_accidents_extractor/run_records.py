"""Define the persisted format shared by result writing and evaluation."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .llm.llm_client import LLMResult
from .schema import VehicleAccident


class RunMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    started_at: datetime

    model_profile: str
    model: str
    base_url: str

    prompt_version: str
    system_hash: str
    repair_hash: str

    sampling_profile: str
    temperature: float
    top_p: float

    timeout_seconds: int
    max_retries: int
    max_tokens: int
    price_per_1m: tuple[float, float]


class DocumentRunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run: RunMetadata
    document_id: str

    status: Literal["valid", "repaired", "failed"]
    accident: VehicleAccident | None

    calls: tuple[LLMResult, ...]
    repair_attempted: bool
    validation_errors: tuple[str, ...]

    latency_seconds: float
    error: str | None = None
