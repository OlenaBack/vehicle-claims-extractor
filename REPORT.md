# Comparison report: vehicle accident extraction

Extracts structured data from 30 accident narratives (English, Swedish or mixed). Quality is measured on the 10 narratives in the golden set. Two models, two prompt versions and two sampling profiles give 8 runs.

- Provider model: `openai/gpt-4o-mini` through OpenRouter.
- Local model: `llama3.2:3b` through Ollama.
- Every run used the final code, including the local model warm-up. Each of the 8 setups was run 3 times (24 runs). Tables show the mean with the range (min–max) over the 3 runs.

## Results

| Model | Prompt | Sampling | Accuracy | Valid on first attempt | Valid after repair | Latency p50 | Latency p95 | Cost per 1,000 accidents |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-4o-mini | v1 | deterministic | 90.7% (89.9–91.1) | 100% | 100% | 2.35 s (2.14–2.66) | 3.53 s (2.71–4.69) | $0.424 |
| gpt-4o-mini | v1 | varied | 91.2% (89.9–92.2) | 100% | 100% | 2.26 s (2.13–2.52) | 3.64 s (2.92–4.34) | $0.424 |
| gpt-4o-mini | v2 | deterministic | **93.8%** (93.3–94.4) | 100% | 100% | 2.26 s (1.89–2.90) | 3.58 s (2.77–4.87) | $0.436 |
| gpt-4o-mini | v2 | varied | 92.7% (92.2–93.3) | 100% | 100% | 2.22 s (2.00–2.64) | 3.80 s (2.92–5.42) | $0.435 |
| llama3.2:3b | v1 | deterministic | 65.2% (65.2–65.2) | 80% | 100% | 2.82 s (2.54–2.99) | 6.44 s (5.44–7.43) | $0 |
| llama3.2:3b | v1 | varied | 67.3% (65.6–70.0) | 74% (73–77) | 100% | 3.25 s (2.98–3.54) | see note | $0 |
| llama3.2:3b | v2 | deterministic | 68.0% (66.9–68.5) | 80% | 100% | 3.04 s (2.82–3.26) | 6.25 s (5.96–6.82) | $0 |
| llama3.2:3b | v2 | varied | 64.2% (60.9–66.7) | 83% | 99% (97–100) | 2.86 s (2.70–3.14) | 6.21 s (5.72–6.76) | $0 |

Note: in one llama3.2:3b v1 varied run, p95 was 852.24 s; the other two runs had 6.34 s and 6.65 s. A mean over these is not meaningful, so none is shown. Three accidents in that run were extremely slow: two took 629 s and 1,035 s on a single successful attempt, and one had an attempt that raised `APITimeoutError` after 19,824 s and then succeeded in 4.6 s. The timeout is 300 s, so waits of this length are not ordinary model slowness. The cause was not investigated (a suspended laptop is possible); it is a reliability risk for the local model on this machine.

No run had unknown token usage, so the costs are complete, not lower bounds. In one llama3.2:3b v2 varied run one response stayed invalid after repair and is marked `failed`; it scores 0 on every field.

Per-field scores on the three fields prompt v2 targeted (correct/total over the golden set, one value per run):

| Setup | lighting | weather | injuries_reported |
| --- | --- | --- | --- |
| gpt-4o-mini v1 deterministic | 7/10, 7/10, 7/10 | 9/13, 10/13, 8/13 | 6/10, 5/10, 5/10 |
| gpt-4o-mini v1 varied | 7/10, 7/10, 7/10 | 10/13, 8/13, 10/13 | 5/10, 6/10, 6/10 |
| gpt-4o-mini v2 deterministic | 9/10, 9/10, 9/10 | 9/13, 10/12, 10/13 | 6/10, 6/10, 6/10 |
| gpt-4o-mini v2 varied | 9/10, 9/10, 9/10 | 9/13, 10/13, 8/13 | 6/10, 6/10, 6/10 |
| llama3.2:3b v1 deterministic | 2/10, 2/10, 2/10 | 6/17, 6/17, 6/17 | 3/10, 3/10, 3/10 |
| llama3.2:3b v1 varied | 3/10, 2/10, 2/10 | 7/13, 5/15, 6/15 | 3/10, 3/10, 3/10 |
| llama3.2:3b v2 deterministic | 2/10, 2/10, 2/10 | 6/13, 6/13, 6/13 | 4/10, 4/10, 4/10 |
| llama3.2:3b v2 varied | 2/10, 2/10, 2/10 | 6/16, 5/15, 6/14 | 5/10, 3/10, 4/10 |

Per-field accuracy, prompt v1 → v2 (mean of 3 runs, % correct; ▲ gain, ▼ regression).

| Field | gpt-4o-mini deterministic | gpt-4o-mini varied | llama3.2:3b deterministic | llama3.2:3b varied |
| --- | --- | --- | --- | --- |
| accident_type | 100 → 100 | 100 → 97 ▼ | 50 → 60 ▲ | 53 → 50 ▼ |
| road_surface | 90 → 90 | 87 → 90 ▲ | 50 → 40 ▼ | 43 → 50 ▲ |
| lighting | 70 → 90 ▲ | 70 → 90 ▲ | 20 → 20 | 23 → 20 ▼ |
| location_type | 100 → 100 | 100 → 100 | 40 → 30 ▼ | 53 → 53 |
| speed_limit_mph | 100 → 100 | 100 → 100 | 100 → 90 ▼ | 80 → 90 ▲ |
| injuries_reported | 53 → 60 ▲ | 57 → 60 ▲ | 30 → 40 ▲ | 30 → 40 ▲ |
| critical_reason | 100 → 100 | 100 → 100 | 80 → 80 | 80 → 73 ▼ |
| weather | 69 → 76 ▲ | 72 → 69 ▼ | 35 → 46 ▲ | 42 → 38 ▼ |
| area_type | 100 → 100 | 100 → 100 | 27 → 36 ▲ | 41 → 37 ▼ |
| vehicles.label | 88 → 88 | 88 → 88 | 76 → 76 | 80 → 69 ▼ |
| vehicles.year | 100 → 100 | 100 → 100 | 100 → 98 ▼ | 100 → 92 ▼ |
| vehicles.make | 100 → 100 | 100 → 100 | 94 → 94 | 92 → 86 ▼ |
| vehicles.model | 88 → 100 ▲ | 92 → 96 ▲ | 82 → 92 ▲ | 84 → 78 ▼ |
| vehicles.towed | 100 → 100 | 100 → 100 | 88 → 88 | 86 → 86 |

For gpt-4o-mini, the only clear gain is lighting; the two small drops are one wrong field in one run. For llama3.2:3b most changes are one golden narrative or less and the varied profile drops on many vehicle fields, partly from the one response that stayed invalid after repair.

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
- GPU: NVIDIA RTX 2000 Ada Laptop GPU (about 4 GB VRAM) and Intel Arc integrated graphics. `ollama ps` during local runs showed `llama3.2:3b` (2.6 GB, context 4096) with processor `100% GPU`, so Ollama ran the model fully on the GPU.
- OS: Windows, x64
- Ollama 0.40.11, model `llama3.2:3b` (Q4_K_M, about 2 GB)

## Limitations

- Only 10 narratives in the golden set: one wrong field moves accuracy by roughly 0.5 points overall and by 10 points on a single-valued field. Differences of a few points are within noise.
- Each setup was run 3 times. The ranges above measure run-to-run noise: gpt-4o-mini varies by 1–2 points, llama3.2:3b by up to 6 points (v2 varied: 60.9–66.7%), and deterministic llama3.2:3b runs are almost identical. Three runs give only a rough range, not a confidence interval. Conclusions about sampling are weak.

## Error analysis

All examples are from the v2 deterministic runs. Each error appeared identically in all 3 runs.

1. **gpt-4o-mini, `injuries_reported` (text `2007075702828`).** The text says "None of the occupants was transported." Expected `null`, produced `false`. Likely cause: the model reads "no transport" as "nobody was injured". The schema says no transport means `null`, and v2 restates it, but the rule was not followed.
2. **gpt-4o-mini, `weather` (text `2007043731811`, Swedish).** The road was wet "after a recent rainstorm". Expected `[]`, produced `['rain']`. Likely cause: earlier rain is treated as current weather, despite the explicit v2 rule against it.
3. **gpt-4o-mini, `lighting` (text `2007075702828`).** The text says "the roadway was dark" with no mention of street lighting. Expected `dark_unknown`, produced `dark_unlit`. Likely cause: the rural setting is taken as evidence that there was no street lighting.
4. **llama3.2:3b, `lighting` and `accident_type` (text `2007082203961`).** The text says "daytime collision … intersection" with vehicles crossing paths. Expected `daylight` and `angle`, produced `dark_lit` and `rear_end`. Likely cause: the 3B model contradicts facts stated in the text.
5. **llama3.2:3b on a Swedish narrative (`2007079723947`).** The text says "dagsljus" (daylight), a dry concrete road, and the vehicle was "bärgades" (towed). Expected `daylight`, `dry`, towed; produced `dawn_dusk`, `snow_ice`, not towed. Likely cause: weak understanding of Swedish, so conditions are invented and the towing information is lost.

The pattern: gpt-4o-mini makes few errors (about 10–12 mismatched fields per v2 deterministic run), mostly over-inferring where the schema says `null`. llama3.2:3b has about 57–60 and makes factual mistakes, worst on the Swedish narratives.

## Did prompt v2 improve on v1?

- **gpt-4o-mini:** yes. Mean accuracy rose by 3.1 points (deterministic, 90.7% to 93.8%) and 1.5 points (varied, 91.2% to 92.7%). The ranges do not overlap in the deterministic profile (89.9–91.1 against 93.3–94.4). Lighting improved from 7/10 to 9/10 in every run of both profiles. Weather and injuries changed little, within run-to-run noise.
- **llama3.2:3b:** no clear effect. Mean accuracy rose by 2.8 points when deterministic (65.2% to 68.0%) but fell by 3.1 points when varied (67.3% to 64.2%), and the ranges overlap in the varied profile. Lighting stayed at 2/10. First-attempt validity was 80% and 83% for v2 against 80% and 74% for v1.

Only the gpt-4o-mini gains (accuracy in the deterministic profile, and lighting) are clearly larger than the noise.

## Production choice

Use `gpt-4o-mini` with prompt v2 and deterministic sampling. It has the highest mean accuracy (93.8%, range 93.3–94.4), is valid on the first attempt for every narrative, and costs about $0.44 per 1,000 accidents. Its latency is better than the local model on this laptop (p50 about 2.3 s against about 3.0 s), where Ollama ran fully on the NVIDIA GPU; on a CPU-only machine the local model would be much slower. The local model was also less reliable: one run had accidents that took 629 s to 19,824 s (see the note under the results table). `llama3.2:3b` reaches only 61–70% accuracy across all runs, makes factual errors on the Swedish narratives, and needed repairs on 17–26% of narratives. The varied v2 profile is within noise of the deterministic one (92.7% mean), but deterministic is more stable.

This choice would change if:
- the narratives cannot leave the company network (privacy or contract), which makes a local model necessary. The next step would then be to test a larger local model, since the 3B model is too weak;
- volume grows so far that API cost outweighs the cost of running local hardware, or the provider changes its prices;
- a larger golden set shows a different ranking. With 10 golden narratives the gap between the models is large enough to be reliable, but differences between prompts and sampling profiles are not.
