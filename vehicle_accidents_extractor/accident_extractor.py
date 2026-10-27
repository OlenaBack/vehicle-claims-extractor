"""Turn one accident description into a validated VehicleAccident.

Coordinate the client, prompt builder and validator, allowing one repair.
Record whole-document latency; transport retries belong to LLMClient.
"""

import time
from dataclasses import dataclass
from typing import Literal

from .config import Sampling
from .llm_client import LLMClient, LLMResult
from .prompt_builder import PromptBuilder
from .response_validator import ResponseValidator
from .schema import VehicleAccident


@dataclass(frozen=True)
class AccidentExtractionResult:
    status: Literal["valid", "repaired", "failed"]
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
                "schema": VehicleAccident.model_json_schema(),
            },
        }

    def extract(self, text: str) -> AccidentExtractionResult:
        """Process one document, preserving every call and allowing one repair."""
        start = time.perf_counter()
        messages = self._prompts.initial(text)
        calls: list[LLMResult] = []
        validation_errors: list[str] = []

        for index in range(2):
            llm_result = self._llm.call(
                messages=messages,
                temperature=self._sampling.temperature,
                top_p=self._sampling.top_p,
                max_tokens=self._max_tokens,
                response_format=self._response_format,
            )
            calls.append(llm_result)
            reason = self._validator.unrepairable_reason(llm_result)
            if reason is not None:
                return AccidentExtractionResult(
                    "failed", None, tuple(calls), tuple(validation_errors),
                    time.perf_counter() - start, reason,
                )

            try:
                accident = self._validator.validate(llm_result)
            except ValueError as validation_error:
                error = str(validation_error)
            else:
                return AccidentExtractionResult(
                    "valid" if index == 0 else "repaired", accident,
                    tuple(calls), tuple(validation_errors), time.perf_counter() - start,
                )

            validation_errors.append(error)
            if index == 0:
                messages = self._prompts.repair(messages, llm_result.content, error)

        return AccidentExtractionResult(
            "failed", None, tuple(calls), tuple(validation_errors),
            time.perf_counter() - start, validation_errors[-1],
        )
