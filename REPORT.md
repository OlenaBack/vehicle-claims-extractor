# Comparison report: vehicle accident extraction

Extracts structured data from 30 accident descriptions (English, Swedish or mixed). Quality is measured on the 10 hand-labeled golden texts. Two models, two prompt versions and two sampling profiles give 8 runs.

- Provider model: `openai/gpt-4o-mini` through OpenRouter.
- Local model: `llama3.2:3b` through Ollama.
- Every run used the final code, including the local model warm-up. Each run was made once.

## Results

| Model | Prompt | Sampling | Accuracy | Valid on first attempt | Valid after repair | Latency p50 | Latency p95 | Cost per 1,000 docs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-4o-mini | v1 | deterministic | 89.9% (161/179) | 100% | 100% | 2.66 s | 4.69 s | $0.424 |
| gpt-4o-mini | v1 | varied | 91.6% (164/179) | 100% | 100% | 2.52 s | 3.66 s | $0.423 |
| gpt-4o-mini | v2 | deterministic | **94.4%** (168/178) | 100% | 100% | 2.90 s | 4.87 s | $0.436 |
| gpt-4o-mini | v2 | varied | 92.7% (166/179) | 100% | 100% | 2.64 s | 5.42 s | $0.436 |
| llama3.2:3b | v1 | deterministic | 65.2% (122/187) | 80.0% | 100% | 2.54 s | 5.44 s | $0 |
| llama3.2:3b | v1 | varied | 66.3% (122/184) | 73.3% | 100% | 2.98 s | 6.34 s | $0 |
| llama3.2:3b | v2 | deterministic | 68.5% (124/181) | 80.0% | 100% | 3.04 s | 5.97 s | $0 |
| llama3.2:3b | v2 | varied | 60.9% (112/184) | 83.3% | 96.7% | 2.70 s | 5.72 s | $0 |

No run had unknown token usage, so the costs are complete, not lower bounds. One response (llama3.2:3b, v2, varied) stayed invalid after repair and is marked `failed`; it scores 0 on every field.

Per-field scores on the three fields prompt v2 targeted (correct/total over the golden texts):

| Run | lighting | weather | injuries_reported |
| --- | --- | --- | --- |
| gpt-4o-mini v1 deterministic | 7/10 | 8/13 | 5/10 |
| gpt-4o-mini v1 varied | 7/10 | 10/13 | 6/10 |
| gpt-4o-mini v2 deterministic | 9/10 | 10/12 | 6/10 |
| gpt-4o-mini v2 varied | 9/10 | 8/13 | 6/10 |
| llama3.2:3b v1 deterministic | 2/10 | 6/17 | 3/10 |
| llama3.2:3b v1 varied | 2/10 | 6/15 | 3/10 |
| llama3.2:3b v2 deterministic | 2/10 | 6/13 | 4/10 |
| llama3.2:3b v2 varied | 2/10 | 5/15 | 3/10 |

## Measurement definitions

Computed by `evaluate.py` (`vehicle_accidents_extractor/evaluation/`), following `REQUIREMENTS.md`:

- **Accuracy:** correct fields divided by total fields over the 10 golden texts. A correct `null` counts as correct, and lists are scored per item. This is why the totals differ between runs: a run that produces more list items has more fields to score. A `failed` response scores 0 on every field.
- **Valid responses:** over all 30 texts, reported on the first attempt and after the single repair attempt.
- **Latency:** wall-clock time per document, from the first request to the final status. It includes retries, backoff and repair. The local model's warm-up call is sent before the run, is not recorded, and so is excluded.
- **Cost per 1,000 documents:** (average input tokens × input price + average output tokens × output price) × 1,000, counting every attempt including repairs. Local API cost is $0.
- **Token prices:** gpt-4o-mini at $0.15 per 1M input tokens and $0.60 per 1M output tokens (`config.toml`). These prices were not re-verified against OpenRouter's current price list.

## Local machine

- CPU: Intel Core Ultra 7 165H
- RAM: 64 GB (63.4 GB usable)
- GPU: NVIDIA RTX 2000 Ada Laptop GPU (about 4 GB VRAM) and Intel Arc integrated graphics. Whether Ollama used the NVIDIA GPU was not verified.
- OS: Windows, x64
- Ollama 0.40.11, model `llama3.2:3b` (Q4_K_M, about 2 GB)

## Limitations

- Only 10 golden texts: one wrong field moves accuracy by roughly 0.5 points overall and by 10 points on a single-valued field. Differences of a few points are within noise.
- Each run was made once. Repeating the same configuration changed accuracy by up to about 5 points on the varied runs. For example, llama3.2:3b v2 varied scored 64.6% in a first run and 60.9% in the final run. Conclusions about sampling are therefore weak.

## Error analysis

All examples are from the final v2 deterministic runs.

1. **gpt-4o-mini, `injuries_reported` (text `2007075702828`).** The text says "None of the occupants was transported." Expected `null`, produced `false`. Likely cause: the model reads "no transport" as "nobody was injured". The schema says no transport means `null`, and v2 restates it, but the rule was not followed.
2. **gpt-4o-mini, `weather` (text `2007043731811`, Swedish).** The road was wet "after a recent rainstorm". Expected `[]`, produced `['rain']`. Likely cause: earlier rain is treated as current weather, despite the explicit v2 rule against it.
3. **gpt-4o-mini, `lighting` (text `2007075702828`).** The text says "the roadway was dark" with no mention of street lighting. Expected `dark_unknown`, produced `dark_unlit`. Likely cause: the rural setting is taken as evidence that there was no street lighting.
4. **llama3.2:3b, `lighting` and `accident_type` (text `2007082203961`).** The text says "daytime collision … intersection" with vehicles crossing paths. Expected `daylight` and `angle`, produced `dark_lit` and `rear_end`. Likely cause: the 3B model contradicts facts stated in the text.
5. **llama3.2:3b on a Swedish text (`2007079723947`).** The text says "dagsljus" (daylight), a dry concrete road, and the vehicle was "bärgades" (towed). Expected `daylight`, `dry`, towed; produced `dawn_dusk`, `snow_ice`, not towed. Likely cause: weak understanding of Swedish, so conditions are invented and the towing information is lost.

The pattern: gpt-4o-mini makes few errors (about 9 mismatched fields in the v2 deterministic run), mostly over-inferring where the schema says `null`. llama3.2:3b has about 50 and makes factual mistakes, worst on the Swedish texts.

## Did prompt v2 improve on v1?

- **gpt-4o-mini:** yes. Accuracy rose by 4.5 points (deterministic) and 1.1 points (varied). Lighting improved from 7/10 to 9/10 in both profiles. Weather improved in the deterministic profile only, and injuries only slightly.
- **llama3.2:3b:** no clear effect. Accuracy rose by 3.3 points when deterministic but fell by 5.4 points when varied, and the lighting score stayed at 2/10. The first-attempt validity was 80% and 83.3% for v2 against 80% and 73.3% for v1.

With 10 golden texts and single runs, only the lighting gain for gpt-4o-mini is clearly larger than the noise.

## Production choice

Use `gpt-4o-mini` with prompt v2 and deterministic sampling. It has the highest accuracy (94.4%), is valid on the first attempt for every document, and costs about $0.44 per 1,000 documents. Its latency is comparable to the local model on this laptop (p50 about 2.9 s against about 3.0 s). `llama3.2:3b` reaches only 61–69% accuracy, makes factual errors on the Swedish texts, and needed repairs on 17–27% of documents.

This choice would change if:
- the descriptions cannot leave the company network (privacy or contract), which makes a local model necessary. The next step would then be to test a larger local model, since the 3B model is too weak;
- volume grows so far that API cost outweighs the cost of running local hardware, or the provider changes its prices;
- a larger golden set shows a different ranking. With 10 golden texts the gap between the models is large enough to be reliable, but differences between prompts and sampling profiles are not.
