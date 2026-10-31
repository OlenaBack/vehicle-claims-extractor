# Prompt changelog

## v1
Baseline zero-shot system prompt: task, languages, output contract, short field definitions, and null or empty lists for unstated values. Detailed extraction rules are in the structured output schema's field descriptions.

Added `repair.txt` alongside `system.txt` so repair instructions are versioned too. The `{error}` placeholder receives the validation error; `PromptBuilder` receives both prompt texts from the caller.

After the first baseline run, changed "original document" to "original description" in `repair.txt` to match the `<description>` tags. Future runs have a different repair prompt hash; the saved baseline retains its original hash and used no repairs.

Evaluation: baseline, mean of 3 runs per setup on the 10 golden texts (see REPORT.md).

| Model | Sampling | Accuracy | lighting | weather | injuries_reported |
| --- | --- | --- | --- | --- | --- |
| gpt-4o-mini | deterministic | 90.7% | 70% | 69% | 53% |
| gpt-4o-mini | varied | 91.2% | 70% | 72% | 57% |
| llama3.2:3b | deterministic | 65.2% | 20% | 35% | 30% |
| llama3.2:3b | varied | 67.3% | 23% | 42% | 30% |

First-attempt validity is 100% for gpt-4o-mini and 74–80% for llama3.2:3b (100% after repair).

## v2
Restates in `system.txt` three schema rules that v1 left only in the field descriptions: weather (earlier rain or a wet road alone is not current rain; do not infer weather from lighting), lighting (`dark_lit`/`dark_unlit` only when street lighting is stated; `dawn_dusk` only when dawn or dusk is stated; morning or evening alone is null) and injuries_reported (transport, examination or EMS treatment without a stated injury is null). `repair.txt` is unchanged from v1.

Why: in v1 gpt-4o-mini scored 70% on lighting, 40–60% on injuries_reported and 62% on weather on the golden set, and llama3.2:3b scored 30%, 30% and 26–35%. Most mismatches broke rules already stated in the schema, for example `dawn_dusk` from "morning" or injuries from "transported".

Hypothesis: accuracy on these three fields improves, most for the local model. No other field is expected to change.

Evaluation: mean of 3 runs per setup, v1 → v2.

- **gpt-4o-mini: lighting improved as expected** (70% → 90%, in every run of both sampling profiles). Weather (+7 deterministic, −3 varied) and injuries_reported (+7, +3) moved within run-to-run noise, so no clear effect. Overall accuracy rose 90.7% → 93.8% (deterministic) and 91.2% → 92.7% (varied).
- **llama3.2:3b: no effect.** Lighting stayed at 20% (20% → 20% deterministic, 23% → 20% varied). Injuries_reported rose 30% → 40% in both profiles, but weather changed +11 and −4 and overall accuracy +2.8 and −3.1 points, so the targeted fields do not show a reliable gain. The hypothesis that the local model would gain most was not supported.
- **Did v2 break anything v1 got right?** For gpt-4o-mini, no consistent regression: the only per-field drops are −3 points (accident_type and weather, varied), one wrong field in one run, within noise. The unexpected gain is `vehicles.model` (88% → 100% deterministic). For llama3.2:3b deterministic, regressions are `road_surface` (50% → 40%), `location_type` (40% → 30%), `speed_limit_mph` (100% → 90%) and `vehicles.year` (100% → 98%), each one golden text or less; varied runs show losses on vehicle fields, partly caused by one response that stayed invalid after repair (scored 0). These fields were outside v2's scope, so they are sampling noise or side effects of a longer prompt, not a rule change. Full per-field table: REPORT.md.
