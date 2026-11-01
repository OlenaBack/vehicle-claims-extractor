# Vehicle Accident Extraction

This project extracts structured accident facts from accident narratives and evaluates them against human-prepared labels.

## Language

**Accident narrative**:
A narrative account of one vehicle accident that serves as extraction input.
_Avoid_: document, raw claim

**Accident ID**:
An identifier for the accident represented by a narrative in a batch.
_Avoid_: document ID

**Batch**:
A named collection of accident narratives; golden labels may cover a subset for evaluation.
_Avoid_: dataset (when referring to the named collection)

**Golden set**:
The accident narratives in a batch that have human-prepared labels and are used to measure extraction accuracy.
_Avoid_: test set

**Golden label**:
The human-prepared structured accident facts for one narrative in the golden set.
_Avoid_: expected output, answer key

**LLM profile**:
One `[llm_profiles.*]` section in `llm_config.toml`, such as `openrouter`. It holds the endpoint, API key variable, model ID and price per 1M tokens, and is used to create an `LLMClient`. The CLI selects it with `--llm-profile`; code calls its name `llm_profile_name` and its settings `llm_profile`. Saved extraction runs store its name under the key `model_profile`.
_Avoid_: model, model profile (the model ID is only one part of a profile)

**Sampling profile**:
One `[sampling_profiles.*]` section in `llm_config.toml`, such as `varied`. It holds the temperature and top_p sent with every LLM call in a batch extraction.
_Avoid_: sampling config

**Model ID**:
The provider's name for an LLM, such as `openai/gpt-4o-mini`.

**Batch extraction**:
Processing accident narratives in a batch using one LLM profile and one extraction setup.

**Extraction setup**:
A prompt version combined with a sampling profile. A batch extraction applies one setup to one LLM profile.
_Avoid_: configuration, experiment

**Extraction run**:
The recorded instance of a batch extraction, including its settings and per-accident records.
_Avoid_: job, batch run

**Accident extraction record**:
The saved outcome for one accident narrative in one extraction run, including its extracted facts or failure.
_Avoid_: result (when referring to an individual extraction outcome)

**Extraction run comparison**:
A table with one row per extraction run of a batch, showing accuracy, validity, latency and cost against the golden set.
_Avoid_: report (that is REPORT.md), leaderboard

**Machine**:
The operating system, processor and logical CPU count recorded with an extraction run, so latency can be interpreted. It never includes the hostname.
