"""Check response completion and validate JSON against a supplied schema."""

from typing import Generic, TypeVar

from pydantic import BaseModel

from .llm_client import LLMResult


ModelT = TypeVar("ModelT", bound=BaseModel)


class ResponseValidator(Generic[ModelT]):
    def __init__(self, schema: type[ModelT]):
        self._schema = schema

    def unrepairable_reason(self, result: LLMResult) -> str | None:
        """Return why processing must stop, or None if validation can proceed."""
        if result.error:
            return result.error
        if not result.has_content:
            return "Response had no content"
        if result.finish_reason not in ("stop", "length"):
            return f"Unexpected finish_reason: {result.finish_reason!r}"
        return None

    def validate(self, result: LLMResult) -> ModelT:
        """Return validated data; raise ValueError for unusable or invalid output."""
        reason = self.unrepairable_reason(result)
        if reason is not None:
            raise ValueError(reason)
        if result.finish_reason != "stop":
            raise ValueError(f"Response did not complete: {result.finish_reason!r}")
        return self._schema.model_validate_json(result.content)
