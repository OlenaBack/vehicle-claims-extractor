# Prompt changelog

## v1
Baseline zero-shot system prompt: task, languages, output contract, short field definitions, and null or empty lists for unstated values. Detailed extraction rules are in the structured output schema's field descriptions.

Added `repair.txt` alongside `system.txt` so repair instructions are versioned too. The `{error}` placeholder receives the validation error; `PromptBuilder` receives both prompt texts from the caller.

After the first baseline run, changed "original document" to "original description" in `repair.txt` to match the `<description>` tags. Future runs have a different repair prompt hash; the saved baseline retains its original hash and used no repairs.

Evaluation: not yet measured.

## v2
Restates in `system.txt` three schema rules that v1 left only in the field descriptions: weather (earlier rain or a wet road alone is not current rain; do not infer weather from lighting), lighting (`dark_lit`/`dark_unlit` only when street lighting is stated; `dawn_dusk` only when dawn or dusk is stated; morning or evening alone is null) and injuries_reported (transport, examination or EMS treatment without a stated injury is null). `repair.txt` is unchanged from v1.

Why: in v1 gpt-4o-mini scored 70% on lighting, 40–60% on injuries_reported and 62% on weather on the golden set, and llama3.2:3b scored 30%, 30% and 26–35%. Most mismatches broke rules already stated in the schema, for example `dawn_dusk` from "morning" or injuries from "transported".

Hypothesis: accuracy on these three fields improves, most for the local model. No other field is expected to change.

Evaluation: not yet measured.
