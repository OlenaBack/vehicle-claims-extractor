"""Check response completion and validate JSON against a supplied schema."""

from typing import Generic, TypeVar

from pydantic import BaseModel

from ..llm.llm_client import LLMResult


ModelT = TypeVar("ModelT", bound=BaseModel)


class UnrepairableResponse(Exception):
    """The response cannot be fixed by asking again: API failure, no content, or filtered output.

    Deliberately not a ValueError, so it can never be caught as a repairable error.
    """


class ResponseValidator(Generic[ModelT]):
    def __init__(self, schema: type[ModelT]):
        self._schema = schema

    def validate(self, result: LLMResult) -> ModelT:
        """Return validated data.

        Raises UnrepairableResponse when processing must stop, or ValueError when one
        repair may help: invalid JSON, schema violation, or truncated output.
        """
        if result.error:
            raise UnrepairableResponse(result.error)
        if not result.has_content:
            raise UnrepairableResponse("Response had no content")
        if result.finish_reason == "length":
            raise ValueError("Response was truncated (finish_reason='length')")
        if result.finish_reason != "stop":
            raise UnrepairableResponse(f"Unexpected finish_reason: {result.finish_reason!r}")
        return self._schema.model_validate_json(result.content)
