"""Talks to an AI model over HTTP and records every try.

Both OpenRouter (cloud) and Ollama (local) speak the same OpenAI-style API,
so one class works for both; only the address, key and model name differ.
"""

import time
from dataclasses import dataclass

from openai import APIConnectionError, APITimeoutError, InternalServerError, OpenAI, OpenAIError, RateLimitError

# Temporary problems that may succeed on a second try:
# timeout, lost connection, too many requests, server error (5xx).
# Anything else (e.g. a bad request) fails immediately, because retrying won't help.
RETRYABLE_ERRORS = (APITimeoutError, APIConnectionError, RateLimitError, InternalServerError)


@dataclass(frozen=True)
class LLMAttempt:
    """One HTTP request to the model. Read-only after creation."""

    outcome: str                 # "ok", "no_choices" (empty response), or the error name, e.g. "APITimeoutError"
    latency_seconds: float       # how long this single request took
    input_tokens: int | None     # tokens we sent; None means unknown (not zero)
    output_tokens: int | None    # tokens the model returned; None means unknown
    error: str | None = None     # error message if the request failed


@dataclass(frozen=True)
class LLMResult:
    """What call() returns: the final answer plus every attempt it took to get it."""

    content: str | None          # the model's answer text; None if we got no answer at all
    finish_reason: str | None    # why the model stopped: "stop" = finished, "length" = cut off
    attempts: tuple[LLMAttempt, ...]
    error: str | None = None     # API failure, missing choices, or no text content

    @property
    def has_content(self) -> bool:
        """True if the model sent back text, even empty text."""
        return self.content is not None

    @property
    def retries(self) -> int:
        """Extra tries after the first one."""
        return len(self.attempts) - 1


class LLMClient:
    """A connection to one model, with its retry settings.

    Create one per model and close it when done, ideally with:
        with LLMClient(...) as llm:
            result = llm.call(...)
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: int,
        max_retries: int,
        openai: OpenAI | None = None,  # a ready SDK client (e.g. a fake in tests); LLMClient takes ownership and closes it
    ):
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        self.model = model
        self.max_retries = max_retries
        # max_retries=0 turns off the SDK's own hidden retries, so we can count and log each try ourselves.
        # Applied to an injected client too, so attempts and timing stay accurate.
        sdk = openai or OpenAI(base_url=base_url, api_key=api_key)
        self._openai = sdk.with_options(timeout=timeout_seconds, max_retries=0)

    def __enter__(self) -> "LLMClient":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def close(self) -> None:
        """Release the network connections, including those of an injected SDK client."""
        self._openai.close()

    def ping(self, timeout_seconds: float = 10) -> str | None:
        """Quick "are you there?" check before a long run.

        Returns None if the server answers, otherwise the error name.
        """
        try:
            self._openai.with_options(timeout=timeout_seconds).models.list()
        except OpenAIError as error:
            return type(error).__name__
        return None

    def call(
        self,
        *,
        messages: list[dict],
        temperature: float,
        top_p: float,
        max_tokens: int,
        response_format: dict,
    ) -> LLMResult:
        """Send one request; on a temporary failure wait 1 s, 2 s, 4 s … and try again.

        Never raises for API problems: failures come back inside the LLMResult.
        Bugs in our own code still raise, so they are not hidden.
        """
        attempts: list[LLMAttempt] = []
        for attempt in range(self.max_retries + 1):
            start = time.perf_counter()
            try:
                response = self._openai.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )
            except OpenAIError as error:
                # The server may have processed (and billed) the request before failing,
                # so token usage is unknown, not zero.
                attempts.append(LLMAttempt(type(error).__name__, time.perf_counter() - start, None, None, str(error)))
                if isinstance(error, RETRYABLE_ERRORS) and attempt < self.max_retries:
                    time.sleep(2**attempt)  # wait 1 s, 2 s, 4 s …
                    continue
                return LLMResult(None, None, tuple(attempts), f"{type(error).__name__}: {error}")

            # The request succeeded at the HTTP level; record time and token usage.
            latency = time.perf_counter() - start
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else None
            output_tokens = usage.completion_tokens if usage else None

            # Rare: the server answered but the response holds no answer.
            if not response.choices:
                attempts.append(LLMAttempt("no_choices", latency, input_tokens, output_tokens, "response had no choices"))
                return LLMResult(None, None, tuple(attempts), "response had no choices")

            attempts.append(LLMAttempt("ok", latency, input_tokens, output_tokens))
            choice = response.choices[0]
            content = choice.message.content
            # No text, e.g. the model refused: keep None so has_content is False, and say why.
            error = None if content is not None else (choice.message.refusal or "response had no content")
            return LLMResult(content, choice.finish_reason, tuple(attempts), error)

        raise AssertionError("unreachable")  # every path in the loop returns
