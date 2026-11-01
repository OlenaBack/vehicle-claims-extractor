# Feature request: single-accident narrative extraction

## Goal

Implement extraction of one accident narrative into a validated `VehicleAccident`, with response validation and at most one repair attempt.

## Public contract (keep unchanged)

- `AccidentExtractor.extract(narrative: str) -> AccidentExtractionOutcome` in `vehicle_accidents_extractor/extraction/accident_extractor.py`.
- `AccidentExtractionOutcome` exactly as defined in that file, including its fields and the `repair_attempted` property.
- `ExtractionStatus` in `extraction_status.py`: `valid`, `repaired`, or `failed`.
- The existing `LLMClient.call(messages, temperature, top_p, max_tokens, response_format) -> LLMResult`, the `VehicleAccident` schema, and the prompts returned by `load_extraction_prompts` (`system_prompt`, `repair_prompt`).
- The public fluent chain of `AccidentBatchExtractorBuilder` and the records it writes.

## Required behavior

1. **First request.** Send the system prompt, then a user message containing the narrative as `<description>\n{narrative}\n</description>`. Request structured output with `response_format = {"type": "json_schema", "json_schema": {"name": "vehicle_accident", "strict": True, "schema": <VehicleAccident JSON schema>}}`, and pass the configured `temperature`, `top_p`, and `max_tokens`.
2. **Classify each response.**
   - **Unrepairable** — the result reports an error, has no content, or has a `finish_reason` other than `"stop"` or `"length"`. Stop immediately with status `failed`; do not attempt a repair.
   - **Repairable** — `finish_reason` is `"length"` (truncated), the content is not valid JSON, or it does not match the `VehicleAccident` schema.
   - **Valid** — `finish_reason` is `"stop"` and the content validates against `VehicleAccident`.
3. **Repair.** After a repairable first response, send one more request: the previous messages, then the previous response as an assistant message, then a user message made from `repair_prompt` with `{error}` replaced by the validation error. Use the same structured-output and sampling settings.
4. **At most two requests per narrative.** Return `valid` when the first response is valid, `repaired` when the repair response is valid, and `failed` otherwise.
5. **Outcome fields.**
   - `accident`: the validated `VehicleAccident`, or `None` when failed.
   - `calls`: every `LLMResult`, in request order.
   - `validation_errors`: one message per repairable failure, in order.
   - `latency_seconds`: wall-clock time for the whole narrative, from before the first request to the final status, including any repair.
   - `error`: `None` on success; otherwise the unrepairable reason, or the last validation error.

## Allowed changes

- Add, change, or remove modules in `vehicle_accidents_extractor/extraction/`, except `extraction_status.py` and `prompt_loader.py`, which stay unchanged.
- In `vehicle_accidents_extractor/batch/accident_batch_extractor.py`, change only the extractor assembly lines inside `AccidentBatchExtractorBuilder.build()` and the import lines they require.
- Add tests.

## Not allowed

- Any other change to `batch/`, `llm/`, the schema, the prompts, or the record definitions.
- Changing `tests/test_accident_extraction_contract.py`.

## Done when

`python -m pytest tests/test_accident_extraction_contract.py` passes unchanged, together with any tests you add.
