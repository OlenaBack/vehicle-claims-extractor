"""Turn one accident description into a validated VehicleAccident.

Coordinate the client, prompt builder and validator, allowing one repair.
Record whole-description latency and each call's outcome.
"""

import time
from dataclasses import dataclass

from ..llm.config import Sampling
from ..llm.llm_client import LLMClient, LLMResult
from ..schema import VehicleAccident
from .extraction_status import ExtractionStatus
from .prompt_builder import PromptBuilder
from .response_validator import ResponseValidator, UnrepairableResponse


@dataclass(frozen=True)
class AccidentExtractionOutcome:
    status: ExtractionStatus
    accident: VehicleAccident | None
    calls: tuple[LLMResult, ...]
    validation_errors: tuple[str, ...]
    latency_seconds: float
    error: str | None = None

    @property
    def repair_attempted(self) -> bool:
        return len(self.calls) == 2


class AccidentExtractor:
    def __init__(
        self,
        llm: LLMClient,
        prompts: PromptBuilder,
        validator: ResponseValidator[VehicleAccident],
        sampling: Sampling,
        max_tokens: int,
    ):
        self._llm = llm
        self._prompts = prompts
        self._validator = validator
        self._sampling = sampling
        self._max_tokens = max_tokens
        self._response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "vehicle_accident",
                "strict": True,
                "schema": validator.schema.model_json_schema(),
            },
        }

    def extract(self, accident_description: str) -> AccidentExtractionOutcome:
        """Process one accident description, preserving every call and allowing one repair."""
        extraction_started_at = time.perf_counter()
        messages = self._prompts.initial(accident_description)
        calls: list[LLMResult] = []
        validation_errors: list[str] = []

        for call_index in range(2):
            llm_result = self._llm.call(
                messages=messages,
                temperature=self._sampling.temperature,
                top_p=self._sampling.top_p,
                max_tokens=self._max_tokens,
                response_format=self._response_format,
            )
            calls.append(llm_result)

            try:
                accident = self._validator.validate(llm_result)
            except UnrepairableResponse as unrepairable:
                return AccidentExtractionOutcome(
                    "failed", None, tuple(calls), tuple(validation_errors),
                    time.perf_counter() - extraction_started_at, str(unrepairable),
                )
            except ValueError as validation_error:
                validation_error_message = str(validation_error)
            else:
                return AccidentExtractionOutcome(
                    "valid" if call_index == 0 else "repaired", accident,
                    tuple(calls), tuple(validation_errors), time.perf_counter() - extraction_started_at,
                )

            validation_errors.append(validation_error_message)
            if call_index == 0:
                messages = self._prompts.repair(
                    messages, llm_result.content, validation_error_message,
                )

        return AccidentExtractionOutcome(
            "failed", None, tuple(calls), tuple(validation_errors),
            time.perf_counter() - extraction_started_at, validation_errors[-1],
        )
