# How it works

## 1. The task

The project extracts structured facts from 30 accident narratives. Its goal is to produce a `VehicleAccident` for each narrative and compare two LLM profiles: `openrouter` and `ollama`.

`read_llm_config()` loads an `LLMConfig` containing the LLM profiles and sampling profiles. With `--all`, `extraction_setups()` combines two prompt versions with two sampling profiles. Without `--all`, one prompt version and one sampling profile are selected.

**Produces:** four `ExtractionSetup`s applied to two LLM profiles: eight planned extraction runs, or one run without `--all`.

## 2. Connecting

`run()` creates `AccidentBatchExtractions` with the selected batch and extraction setups. For each LLM profile, `extract_with()` opens an `LLMClient` and calls `ping()` once. For a local LLM, it also calls `warm_up()` before each setup.

If the API key is missing, a single run stops with an error and `--all` skips that profile. If `ping()` or local warm-up fails, `LLMUnavailable` is raised. A single run stops with an error; with `--all`, the app skips that profile and keeps paths for runs already saved.

**Produces:** a connected `LLMClient` that answered its connection check.

## 3. Preparing

For each setup, `AccidentBatchExtractorBuilder` loads the `ExtractionPrompts` and finds the batch's narratives. Before any LLM call, it records the run settings in `ExtractionRunMetadata`, including the price per 1M tokens. `ArtifactPaths` builds the saved run's file path from the LLM profile, model ID, prompt version, sampling profile and run ID. If a required setting is missing or a profile or prompt version is unknown, the builder stops with a clear error.

**Produces:** an `AccidentBatchExtractor` containing its `AccidentExtractor` and the run metadata and output path.

## 4. Extracting

For an initial call, `PromptBuilder` creates two messages: the system prompt with extraction rules, and the narrative wrapped in `<description>` tags so it is treated as data. `LLMClient` sends the request and retries temporary API failures up to the configured limit of two retries. Each call returns an `LLMResult` containing the response and its `LLMAttempt`s.

`ResponseValidator` checks the response against `VehicleAccident`:

- Invalid or truncated output gets one repair request. If it still fails validation, the outcome is `failed`.
- An API error, no content or an unexpected finish reason raises `UnrepairableResponse`; `AccidentExtractor` catches it and returns a `failed` outcome.

**Produces:** an `AccidentExtractionOutcome` with status `valid`, `repaired` or `failed`, and the `LLMResult`s and `LLMAttempt`s from its calls.

## 5. Saving

`AccidentExtractionRecordWriter` saves each outcome immediately as an `AccidentExtractionRecord`, one JSONL line per accident. It opens the output file in exclusive-create mode, so an existing extraction run is never overwritten.

**Produces:** an extraction run with one record for each of the batch's 30 narratives.

## 6. Judging one run

`evaluate_extraction_run()` builds a comparison row for one saved run. `calculate_run_metrics()` compares its records with the batch's 10 `GoldenRecord`s. `score_accident()` compares each golden label with its extraction:

- Scalar values match after trimming and case-folding.
- Lists score by intersection over union; two empty lists count as a match.
- Vehicles pair by equal non-null labels first, then by maximum field agreement. Content-based tie-breaking makes the score independent of list order.
- A failed extraction scores zero; each incorrect field is recorded as a `FieldMismatch`.

**Produces:** an `ExtractionRunComparisonRow` containing `ExtractionRunMetadata` and `RunMetrics` for accuracy, validity, latency and cost. Cost uses the saved `LLMAttempt` token counts and run price.

## 7. Comparing runs

`compare_extraction_runs()` builds one row per saved run. It rejects duplicate run IDs and runs from different batches, loads golden labels from that batch, and sorts by `(model, prompt_version, sampling_profile_name, started_at, run_id)`.

The same rows feed both views:

- After `--all`, `main.py` prints `format_terminal_extraction_run_comparison()`.
- `evaluate.py --compare … --markdown` prints `format_markdown_extraction_run_comparison()`, which supplies the appendix table in `REPORT.md`. A test runs the documented command and checks that its output matches the appendix.

`REPORT.md` recommends from the mean and range of three repeats for each LLM profile and extraction setup.
