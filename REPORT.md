# Comparison report: vehicle accident extraction

Extracts structured data from 30 accident narratives (English, Swedish or mixed). Quality is measured on the 10 narratives in the golden set. Two models, two prompt versions and two sampling profiles give 8 runs.

- Provider model: `openai/gpt-4o-mini` through OpenRouter.
- Local model: `llama3.2:3b` through Ollama.
- Every run used the final code, including the local model warm-up. Each of the 8 setups was run 3 times (24 runs). Tables show the mean with the range (min–max) over the 3 runs.

## Results

| Model | Prompt | Sampling | Accuracy | Valid on first attempt | Valid after repair | Latency p50 | Latency p95 | Cost per 1,000 accidents |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-4o-mini | v1 | deterministic | 90.3% (89.4–91.1) | 100% | 100% | 2.03 s (2.00–2.05) | 3.02 s (2.75–3.46) | $0.424 |
| gpt-4o-mini | v1 | varied | 90.3% (89.9–90.5) | 100% | 100% | 1.97 s (1.92–2.04) | 2.81 s (2.59–2.96) | $0.424 |
| gpt-4o-mini | v2 | deterministic | **93.7%** (93.3–93.9) | 100% | 100% | 2.05 s (1.88–2.23) | 3.35 s (3.17–3.61) | $0.436 |
| gpt-4o-mini | v2 | varied | 92.9% (92.2–93.3) | 100% | 100% | 2.12 s (2.02–2.20) | 2.90 s (2.73–3.13) | $0.436 |
| llama3.2:3b | v1 | deterministic | 65.4% (65.2–65.6) | 80% | 100% | 2.60 s (2.34–3.07) | 5.64 s (5.18–6.40) | $0 |
| llama3.2:3b | v1 | varied | 66.1% (63.7–69.2) | 78% (73–87) | 97% (93–100) | 2.58 s (2.41–2.74) | 5.45 s (4.95–6.07) | $0 |
| llama3.2:3b | v2 | deterministic | 68.0% (66.9–68.5) | 80% | 100% | 2.66 s (2.51–2.85) | 5.50 s (5.17–6.08) | $0 |
| llama3.2:3b | v2 | varied | 65.3% (63.0–66.7) | 82% (77–87) | 100% | 2.61 s (2.48–2.85) | 5.37 s (4.97–6.13) | $0 |

Validity over all responses: gpt-4o-mini produced 360 of 360 valid on the first attempt, so repair never ran. llama3.2:3b needed repair for 72 of 360 responses (20%): 69 became valid and 3 stayed invalid. The 3 `failed` responses are all in llama3.2:3b v1 varied (runs 1 and 2; accident `2005076197285` failed in both). Each had the same error: the repaired `weather` list contained a duplicate item. A `failed` response scores 0 on every field.

No request timed out or returned an API error in any of the 24 runs, and the slowest accident took 8.8 s. Token usage was known for all 792 requests, so the costs are complete, not lower bounds.

Per-field scores on the three fields prompt v2 targeted (correct/total over the golden set, one value per run):

| Setup | lighting | weather | injuries_reported |
| --- | --- | --- | --- |
| gpt-4o-mini v1 deterministic | 7/10, 7/10, 7/10 | 9/13, 9/13, 8/13 | 5/10, 6/10, 4/10 |
| gpt-4o-mini v1 varied | 7/10, 7/10, 7/10 | 8/13, 8/13, 8/13 | 6/10, 6/10, 6/10 |
| gpt-4o-mini v2 deterministic | 9/10, 9/10, 9/10 | 10/13, 10/13, 10/13 | 6/10, 6/10, 6/10 |
| gpt-4o-mini v2 varied | 9/10, 9/10, 9/10 | 9/13, 9/13, 10/12 | 6/10, 7/10, 6/10 |
| llama3.2:3b v1 deterministic | 2/10, 2/10, 2/10 | 6/17, 6/17, 6/17 | 3/10, 3/10, 3/10 |
| llama3.2:3b v1 varied | 3/10, 3/10, 4/10 | 5/14, 7/15, 7/14 | 3/10, 3/10, 3/10 |
| llama3.2:3b v2 deterministic | 2/10, 2/10, 2/10 | 6/13, 6/13, 6/13 | 4/10, 4/10, 4/10 |
| llama3.2:3b v2 varied | 2/10, 2/10, 1/10 | 9/13, 8/14, 6/13 | 4/10, 4/10, 4/10 |

Per-field accuracy, prompt v1 → v2 (mean of 3 runs, % correct; ▲ gain, ▼ regression).

| Field | gpt-4o-mini deterministic | gpt-4o-mini varied | llama3.2:3b deterministic | llama3.2:3b varied |
| --- | --- | --- | --- | --- |
| accident_type | 100 → 100 | 100 → 100 | 50 → 60 ▲ | 53 → 47 ▼ |
| road_surface | 90 → 90 | 87 → 90 ▲ | 50 → 40 ▼ | 43 → 47 ▲ |
| lighting | 70 → 90 ▲ | 70 → 90 ▲ | 20 → 20 | 33 → 17 ▼ |
| location_type | 100 → 100 | 100 → 100 | 40 → 30 ▼ | 40 → 47 ▲ |
| speed_limit_mph | 100 → 100 | 100 → 100 | 100 → 90 ▼ | 83 → 87 ▲ |
| injuries_reported | 50 → 60 ▲ | 60 → 63 ▲ | 30 → 40 ▲ | 30 → 40 ▲ |
| critical_reason | 100 → 100 | 100 → 100 | 80 → 80 | 80 → 80 |
| weather | 67 → 77 ▲ | 62 → 74 ▲ | 35 → 46 ▲ | 44 → 58 ▲ |
| area_type | 100 → 100 | 100 → 100 | 27 → 36 ▲ | 40 → 40 |
| vehicles.label | 88 → 88 | 88 → 88 | 76 → 76 | 75 → 74 ▼ |
| vehicles.year | 100 → 100 | 100 → 100 | 100 → 98 ▼ | 96 → 96 |
| vehicles.make | 100 → 100 | 100 → 100 | 94 → 94 | 92 → 89 ▼ |
| vehicles.model | 88 → 100 ▲ | 88 → 92 ▲ | 82 → 92 ▲ | 80 → 68 ▼ |
| vehicles.towed | 100 → 98 ▼ | 100 → 98 ▼ | 88 → 88 | 86 → 79 ▼ |

For gpt-4o-mini, v2 gained on lighting (+20 points in both profiles), weather (+10 to +12) and vehicles.model, and made two small drops: one wrong `vehicles.towed` field in one deterministic run and one in one varied run. Nothing else changed for the worse. For llama3.2:3b the changes go both ways and mostly span one or two golden narratives: lighting (varied), vehicles.model (varied) and `vehicles.towed` (varied) drop, while weather, injuries_reported and area_type gain. With 3 runs and ranges of up to 5.5 points, these llama changes are not clearly larger than the noise.

## Measurement definitions

Computed by `evaluate.py` (`vehicle_accidents_extractor/evaluation/`), following `REQUIREMENTS.md`:

- **Accuracy:** correct fields divided by total fields over the 10 narratives in the golden set. A correct `null` counts as correct, and lists are scored per item. This is why the totals differ between runs: a run that produces more list items has more fields to score. A `failed` response scores 0 on every field.
- **Valid responses:** over all 30 narratives, reported on the first attempt and after the single repair attempt.
- **Latency:** wall-clock time per accident, from the first request to the final status. It includes retries, backoff and repair. The local model's warm-up call is sent before the run, is not recorded, and so is excluded.
- **Cost per 1,000 accidents:** (average input tokens × input price + average output tokens × output price) × 1,000, counting every attempt including repairs. Local API cost is $0.
- **Token prices:** gpt-4o-mini at $0.15 per 1M input tokens and $0.60 per 1M output tokens (`config.toml`). These prices were verified against OpenRouter's price list on 2026-10-29.
- **Normalization:** before comparing, strings are trimmed and casefolded; other JSON values (numbers, booleans, `null`) are compared exactly. Lists are scored per item as intersection over union of the normalized items.
- **Vehicle matching:** golden and extracted vehicles are paired independently of list order. First, vehicles with equal non-null labels are paired. The rest are paired to maximize the number of matching fields among label, year, make, model and towed, each vehicle used once; ties are broken by vehicle contents. Each pair scores five fields. A golden vehicle with no counterpart (missed) scores all five as incorrect, and an extra extracted vehicle adds incorrect fields.

## Local machine

- CPU: Intel Core Ultra 7 165H
- RAM: 64 GB (63.4 GB usable)
- GPU: NVIDIA RTX 2000 Ada Laptop GPU (about 4 GB VRAM) and Intel Arc integrated graphics. `ollama ps` in an earlier session showed `llama3.2:3b` (2.6 GB, context 4096) with processor `100% GPU`, so Ollama ran the model fully on the GPU. It was not re-checked during the 24 runs reported here.
- Recorded in every run file: `Windows-11 · Intel64 Family 6 Model 170 Stepping 4, GenuineIntel · 22 logical CPUs`.
- OS: Windows, x64
- Ollama 0.40.11, model `llama3.2:3b` (Q4_K_M, about 2 GB)

## Limitations

- Only 10 narratives in the golden set: one wrong field moves accuracy by roughly 0.5 points overall and by 10 points on a single-valued field. Differences of a few points are within noise.
- Each setup was run 3 times. The ranges above measure run-to-run noise: gpt-4o-mini varies by 0.6–1.7 points, llama3.2:3b by up to 5.5 points (v1 varied: 63.7–69.2%), and deterministic llama3.2:3b runs are almost identical (0.4 and 1.7 points). Three runs give only a rough range, not a confidence interval. Conclusions about sampling are weak.
- All 24 runs were made on the same day (2026-10-31, 06:57–07:33 UTC), on one machine and one network, one after another. The ranges show repeatability in that environment, not variation across days, API load or hardware. No run had a timeout, so this data says nothing about the local model's stability over long periods.

## Error analysis

All examples are from the v2 deterministic runs. Each error appeared identically in all 3 runs.

1. **gpt-4o-mini, `injuries_reported` (text `2007075702828`).** The text says "None of the occupants was transported." Expected `null`, produced `false`. Likely cause: the model reads "no transport" as "nobody was injured". The schema says no transport means `null`, and v2 restates it, but the rule was not followed.
2. **gpt-4o-mini, `weather` (text `2007043731811`, Swedish).** The road was wet "after a recent rainstorm". Expected `[]`, produced `['rain']`. Likely cause: earlier rain is treated as current weather, despite the explicit v2 rule against it.
3. **gpt-4o-mini, `lighting` (text `2007075702828`).** The text says "the roadway was dark" with no mention of street lighting. Expected `dark_unknown`, produced `dark_unlit`. Likely cause: the rural setting is taken as evidence that there was no street lighting.
4. **llama3.2:3b, `lighting` and `accident_type` (text `2007082203961`).** The text says "daytime collision … intersection" with vehicles crossing paths. Expected `daylight` and `angle`, produced `dark_lit` and `rear_end`. Likely cause: the 3B model contradicts facts stated in the text.
5. **llama3.2:3b on a Swedish narrative (`2007079723947`).** The text says "dagsljus" (daylight), a dry concrete road, and the vehicle was "bärgades" (towed). Expected `daylight`, `dry`, towed; produced `dawn_dusk`, `snow_ice`, not towed. Likely cause: weak understanding of Swedish, so conditions are invented and the towing information is lost.

The pattern: gpt-4o-mini makes few errors (11–12 mismatched fields per v2 deterministic run out of 179). Most are over-inference where the golden value is `null`: `injuries_reported` is wrong in 4 of 10 narratives (`True` or `False` instead of `null`), plus a `road_surface` of `dry` and weather values (`rain`, `clear`, `other`) that the text does not support. llama3.2:3b has 57–60 mismatches out of 181 and does the same over-inference more often, besides making factual mistakes, worst on the Swedish narratives.

## Did prompt v2 improve on v1?

- **gpt-4o-mini:** yes. Mean accuracy rose by 3.4 points when deterministic (90.3% to 93.7%) and by 2.6 points when varied (90.3% to 92.9%). The ranges do not overlap in either profile (deterministic 89.4–91.1 against 93.3–93.9; varied 89.9–90.5 against 92.2–93.3). Lighting improved from 7/10 to 9/10 in every run of both profiles. Weather rose from 67% to 77% (deterministic) and from 62% to 74% (varied), and injuries from 5/10 to 6/10 on average: these two are smaller changes, partly within run-to-run noise. The only drop is one wrong `vehicles.towed` field in one run of each profile.
- **llama3.2:3b:** no reliable effect. Mean accuracy rose by 2.6 points when deterministic (65.4% to 68.0%, ranges 65.2–65.6 against 66.9–68.5, which do not overlap) but fell by 0.8 points when varied (66.1% to 65.3%, ranges overlapping). Lighting did not improve: it stayed at 2/10 when deterministic and fell from 3–4/10 to 1–2/10 when varied. Weather and injuries_reported gained (injuries from 3/10 to 4/10 in all deterministic and varied runs), and several vehicle fields dropped in the varied profile. First-attempt validity was 80% and 82% for v2 against 80% and 78% for v1.

The hypothesis for v2 ("lighting improved as expected for gpt-4o-mini; no effect on llama3.2:3b") holds for lighting in both models. For llama3.2:3b, the deterministic gain of 2.6 points was not expected and is not repeated under varied sampling.

Only the gpt-4o-mini gains (accuracy in both profiles, and lighting) are clearly larger than the noise.

## Production choice

Use `gpt-4o-mini` with prompt v2 and deterministic sampling. It has the highest mean accuracy (93.7%, range 93.3–93.9), is valid on the first attempt for every narrative, and costs about $0.44 per 1,000 accidents. Its latency is better than the local model on this laptop (p50 about 2.1 s against about 2.7 s, p95 3.4 s against 5.5 s), where Ollama ran fully on the NVIDIA GPU in an earlier session; on a CPU-only machine the local model would be much slower. `llama3.2:3b` reaches only 63–69% accuracy across all runs, makes factual errors on the Swedish narratives, and needed repair for 20% of responses; 3 responses stayed invalid after repair (all in v1 varied). The varied v2 profile is within noise of the deterministic one (92.9% mean against 93.7%), but deterministic is more stable (spread 0.6 points against 1.1).

The weakest field of the chosen setup is `injuries_reported` (about 62% correct over the golden set): the model fills in `true` or `false` where the golden value is `null`. Results for it need a human check, or a further prompt revision tested on the same golden set.

This choice would change if:
- the narratives cannot leave the company network (privacy or contract), which makes a local model necessary. The next step would then be to test a larger local model, since the 3B model is too weak;
- volume grows so far that API cost outweighs the cost of running local hardware, or the provider changes its prices;
- a larger golden set shows a different ranking. With 10 golden narratives the gap between the models is large enough to be reliable, but differences between prompts and sampling profiles are not.
