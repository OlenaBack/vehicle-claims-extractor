# Requirements: Structured Extraction Service

Build a service that extracts structured data from raw text according to a schema, compare a provider model with a local model, and justify with measurements which option should go to production.

## Data

- **Source:** texts from the project domain, with no personal data. Synthetic or anonymized texts are acceptable.
- **Amount:** 30 texts. 10 of them are labeled by hand and form the **golden set**, used to measure quality. The golden set is part of the 30.
- **Messiness:** texts vary in length and include typos, missing fields and mixed languages.
- **Golden labels:** stored in `data/` in the same schema the models produce. Fields absent from the text are `null` (or an empty list), never guessed.

Adaptations made to meet these requirements are documented in `data/README.md`.

## Steps

Steps 1–2 form the checkpoint.

### 1. Schema and baseline prompt

- Define a schema with Pydantic or JSON Schema: at least 6 fields, at least 1 enum and at least 1 nested object or list.
- Write a baseline prompt and connect a provider model through its API using structured output.
- Handle transport failures (network errors, rate limits, timeouts) with retries and a timeout.
- Run all 30 texts and save the extraction records in `extractions/`.

### 2. Second model and measurements

- Connect a local model (Ollama or another open-source model) through the same interface as the provider model.
- Keep sampling parameters (`temperature`, `top_p`) in configuration.
- Run 2 models × 2 prompt versions × 2 sampling configurations (8 runs).
- Measure each run as defined in [Measurement definitions](#measurement-definitions).

### 3. Prompt versioning and validation

- Store each prompt version in its own file under `prompts/`, with a changelog stating what changed and why. At least 2 versions.
- Validate every response against the schema. If invalid, make **one** repair attempt; if still invalid, mark it `failed`.
- For every document, log the model, prompt version, sampling parameters, transport retries, whether a repair was attempted, final status (`valid`, `repaired`, `failed`), latency and token usage per call.

### 4. Comparison report

`REPORT.md` contains:

- A table with one row per run and all metrics.
- The measurement definitions used, the local machine (CPU, RAM, GPU if any) and the token prices used for cost.
- An analysis of 3–5 representative errors from both models: input excerpt, expected value, produced value and likely cause.
- Whether prompt v2 improved the metrics compared with v1.
- The production choice in one paragraph, with the conditions under which it would change.

### Optional

- A third, inexpensive provider model.
- Automated regression runs against the golden set.
- Response caching.

## Measurement definitions

`REPORT.md` states these definitions, or any deviation from them.

| Metric | Definition | Notes |
| --- | --- | --- |
| Field-level accuracy | Correct fields ÷ total fields, over the 10 golden texts | Compared after normalization (trim, case, date and number formats). Enums: exact match. Lists: scored per item, order ignored. A correct `null` counts as correct. A `failed` response scores 0 on every field. |
| % valid responses | Valid responses ÷ all responses, over all 30 texts | Reported twice: valid on the first attempt, and valid after repair. |
| Latency p50 / p95 | Wall-clock time per document, from the first request to the final status | Includes failed attempts, backoff, validation and repair. The local model's warm-up call is excluded. |
| Cost per 1,000 documents | (average input tokens × input price + average output tokens × output price) × 1,000 | Averages per document, counting known usage across all attempts, including repairs. Unknown usage (for example, after a timeout) is logged as `null`, not 0. Each run reports `unknown_usage_calls` and `documents_with_unknown_usage`; provider cost is a lower bound when either is above 0. The local model's API cost is $0. |

With 10 golden texts, one wrong field changes accuracy noticeably; the report states this limitation.

## Technical requirements

- Python 3.11+.
- One provider model and one local model. The local model runs on a regular laptop.
- API keys in `.env`; only `.env.example` is committed.
- Runs with one command: `make run` or `python main.py`.
- A missing API key or unreachable local model is skipped with a clear message; the report is still built from saved results.
- Running costs stay within free-tier limits or under $5.

## Submission

One link to a public GitHub repository containing:

- Service code and schema.
- `prompts/` with prompt versions and a changelog.
- `data/` with the texts and the golden set.
- `extractions/` with model outputs and run logs, committed.
- `REPORT.md` with the comparison report.
- `README.md` with setup and run instructions, including how to install the local model.

## Out of scope

UI, deployment, fine-tuning, large datasets and perfect accuracy. The focus is the engineering approach and honest measurements.
