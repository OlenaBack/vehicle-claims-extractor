# Prompt changelog

## v1
Baseline zero-shot system prompt: task, languages, output contract, short field definitions, and null or empty lists for unstated values. Detailed extraction rules are in the structured output schema's field descriptions.

Added `repair.txt` alongside `system.txt` so repair instructions are versioned too. The `{error}` placeholder receives the validation error; `PromptBuilder` receives both prompt texts from the caller.

After the first baseline run, changed "original document" to "original description" in `repair.txt` to match the `<description>` tags. The baseline numbers below were all measured with the changed repair prompt.

Evaluation: baseline, mean of 3 runs per setup on the 10 narratives in the golden set (see REPORT.md).

| Model | Sampling | Accuracy | lighting | weather | injuries_reported |
| --- | --- | --- | --- | --- | --- |
| gpt-4o-mini | deterministic | 90.3% | 70% | 67% | 50% |
| gpt-4o-mini | varied | 90.3% | 70% | 62% | 60% |
| llama3.2:3b | deterministic | 65.4% | 20% | 35% | 30% |
| llama3.2:3b | varied | 66.1% | 33% | 44% | 30% |

First-attempt validity is 100% for gpt-4o-mini and 78–80% for llama3.2:3b. After repair it is 100%, except llama3.2:3b varied (97%): 3 of its 90 responses stayed invalid and scored 0.

## v2
Restates in `system.txt` three schema rules that v1 left only in the field descriptions: weather (earlier rain or a wet road alone is not current rain; do not infer weather from lighting), lighting (`dark_lit`/`dark_unlit` only when street lighting is stated; `dawn_dusk` only when dawn or dusk is stated; morning or evening alone is null) and injuries_reported (transport, examination or EMS treatment without a stated injury is null). `repair.txt` is unchanged from v1.

Why: in v1 gpt-4o-mini scored 70% on lighting, 50–60% on injuries_reported and 62–67% on weather on the golden set, and llama3.2:3b scored 20–33%, 30% and 35–44%. Most mismatches broke rules already stated in the schema, for example `dawn_dusk` from "morning" or injuries from "transported".

Hypothesis: accuracy on these three fields improves, most for the local model. No other field is expected to change.

Evaluation: mean of 3 runs per setup, v1 → v2.

- **gpt-4o-mini: lighting improved as expected** (70% → 90%, in every run of both sampling profiles). Weather also gained (+10 points deterministic, +12 varied; 1–2 fields per run on a base of 13) and injuries_reported rose 50% → 60% (deterministic) and 60% → 63% (varied), which is within run-to-run noise. Overall accuracy rose 90.3% → 93.7% (deterministic) and 90.3% → 92.9% (varied); the ranges do not overlap in either profile.
- **llama3.2:3b: no reliable effect.** Lighting did not improve (20% → 20% deterministic, 33% → 17% varied). Injuries_reported rose 30% → 40% in both profiles and weather rose (+11 and +14 points), but weather totals changed between runs (13–17 items), so this is weak evidence. Overall accuracy rose 2.6 points deterministic (65.4% → 68.0%) and fell 0.8 points varied (66.1% → 65.3%). The hypothesis that the local model would gain most was not supported.
- **Did v2 break anything v1 got right?** For gpt-4o-mini, almost nothing: the only drop is `vehicles.towed` (100% → 98% in both profiles), one wrong field in one run each. Unexpected gains are `vehicles.model` (88% → 100% deterministic, 88% → 92% varied). For llama3.2:3b deterministic, regressions are `road_surface` (50% → 40%), `location_type` (40% → 30%), `speed_limit_mph` (100% → 90%) and `vehicles.year` (100% → 98%), each one narrative or less. In the varied profile lighting (33% → 17%), `vehicles.model` (80% → 68%), `vehicles.towed` (86% → 79%) and `accident_type` (53% → 47%) dropped, while v2 had no failed responses. These fields were outside v2's scope, so they are sampling noise or side effects of a longer prompt, not a rule change. Full per-field table: REPORT.md.
