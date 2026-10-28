"""Define run metadata and per-accident extraction records."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .extraction.extraction_status import ExtractionStatus
from .llm.llm_client import LLMResult
from .schema import VehicleAccident


class ExtractionRunMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    started_at: datetime
    batch: str

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
    price_per_1m: tuple[float, float]  # USD per 1M tokens: (input, output)


class AccidentExtractionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run: ExtractionRunMetadata
    accident_id: str

    status: ExtractionStatus
    accident: VehicleAccident | None

    calls: tuple[LLMResult, ...]
    repair_attempted: bool
    validation_errors: tuple[str, ...]

    latency_seconds: float
    error: str | None = None
