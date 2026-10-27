# Prompt changelog

## v1
Baseline zero-shot system prompt: task, languages, output contract, short field definitions, and null or empty lists for unstated values. Detailed extraction rules are in the structured output schema's field descriptions.

Added `repair.txt` alongside `system.txt` so repair instructions are versioned too. The `{error}` placeholder receives the validation error; `PromptBuilder` receives both prompt texts from the caller.

After the first baseline run, changed "original document" to "original description" in `repair.txt` to match the `<description>` tags. Future runs have a different repair prompt hash; the saved baseline retains its original hash and used no repairs.

Evaluation: not yet measured.
