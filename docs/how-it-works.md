# How it works

**1. The task.** 30 accident narratives give their facts as free text. Each must become a **`VehicleAccident`**. The question: which LLM does this best?

`read_llm_config()` loads an **`LLMConfig`**. It holds 2 **`LLMProfile`**s (`openrouter`, `ollama`) and 2 **`SamplingProfile`**s (`deterministic`, `varied`). With `--all`, `extraction_setups()` pairs 2 prompt versions with both sampling profiles. Without it, there is one setup and one LLM profile.
**Produces:** 4 **`ExtractionSetup`**s × 2 LLM profiles = 8 planned extraction runs (otherwise 1).

**2. Connecting.** `run()` creates **`AccidentBatchExtractions`**: the batch and its setups, waiting for an LLM. For each LLM profile, `extract_with()` opens an **`LLMClient`** and calls `ping()` once. A local LLM also gets `warm_up()` before each setup.

If the API key is missing, or the LLM doesn't answer (**`LLMUnavailable`**):
- a single run stops with an error;
- with `--all`, the app moves on to the next LLM profile and keeps the runs already saved.

**Produces:** an **`LLMClient`** that answered.

**3. Preparing.** For each setup (a prompt version plus a sampling profile) within one LLM profile, **`AccidentBatchExtractorBuilder`** loads the **`ExtractionPrompts`** and finds the narratives. Before any LLM call, it records the run's settings in **`ExtractionRunMetadata`**, including the price per 1M tokens, so the cost can be calculated later. **`ArtifactPaths`** decides where the run will be saved: a file name built from the LLM profile, model ID, prompt, sampling and run ID. If a setting is missing, or names a profile or prompt version that doesn't exist, the builder stops with a clear error.
**Produces:** an **`AccidentBatchExtractor`** with its **`AccidentExtractor`**.

**4. Extracting.** For each narrative, **`PromptBuilder`** builds two messages: the system prompt with the rules, and the narrative wrapped in `<description>` tags, so the LLM treats it as data. **`LLMClient`** sends the prompt and retries temporary errors up to 2 times. **`ResponseValidator`** checks the response against **`VehicleAccident`**:
- invalid or truncated JSON gets one repair request; if that fails too: *failed*;
- an API error, no content or an unexpected stop raises **`UnrepairableResponse`** (*failed*).

**Produces:** an **`AccidentExtractionOutcome`** (*valid*, *repaired* or *failed*) with its **`LLMResult`**s and **`LLMAttempt`**s.

**5. Saving.** **`AccidentExtractionRecordWriter`** saves each outcome right away as an **`AccidentExtractionRecord`**: one JSON line. The file is never overwritten.
**Produces:** one extraction run of 30 records.

**6. Judging.** `evaluate_extraction_run()` scores one saved run. `calculate_run_metrics()` checks it against the 10 **`GoldenRecord`**s. `score_accident()` compares each golden label with its extraction:
- single values must match after normalizing;
- lists score their overlap;
- vehicles are paired by `match_vehicles()`, in any order.

A failed extraction scores 0. Each miss becomes a **`FieldMismatch`**.
**Produces:** an **`ExtractionRunComparisonRow`**: the run's **`ExtractionRunMetadata`** and its **`RunMetrics`** (accuracy, validity, latency, and cost from **`LLMAttempt`** tokens at the saved price).

**7. The verdict.** `compare_extraction_runs()` builds one row per saved run of a batch. It rejects duplicates and mixed batches, and sorts by model ID, prompt, sampling and start time. The same rows feed two views:
- after `--all`, `main.py` prints `format_terminal_extraction_run_comparison()`;
- `evaluate.py --compare … --markdown` prints `format_markdown_extraction_run_comparison()`: the table in REPORT.md's appendix, kept in sync by a test.

REPORT.md recommends from the mean of 3 repeats of each LLM profile and setup.
**Produces:** an extraction run comparison, in the terminal or as the report's table.

## Design decisions

**Own retries, SDK retries off.** Every HTTP try must be logged with its latency and tokens. The OpenAI SDK hides its own retries, so **`LLMClient`** turns them off and retries temporary errors itself. Each try becomes an **`LLMAttempt`**.

**Unknown tokens are `None`, not 0.** A request that timed out may still have been billed. Counting it as 0 would make the cost look exact. Instead, the cost is flagged as a lower bound.

**Failures are values, not exceptions.** `LLMClient.call()` returns an **`LLMResult`** with an error instead of raising. **`AccidentExtractor`** returns a *failed* **`AccidentExtractionOutcome`**. One bad narrative never stops a run of 30. Bugs in our own code still raise.

**Two kinds of invalid response.** Bad JSON or a cut-off response might be fixed by asking again; an API error or a refusal won't be. **`ResponseValidator`** raises a `ValueError` for the first and **`UnrepairableResponse`** for the second. **`UnrepairableResponse`** is not a `ValueError`, so it can't be caught as repairable by mistake.

**Every record describes its run.** Each **`AccidentExtractionRecord`** carries the full **`ExtractionRunMetadata`**: model ID, prompt version and hashes, sampling, limits, price and machine. A saved run can be scored or audited without knowing how it was made, and the cost uses the price saved at run time.

**Saved runs are never overwritten.** Each run gets a new file with a unique run ID, opened in create-only mode. Records are written as they arrive, so an interrupted run keeps its finished narratives.

**Old runs stay readable.** Renamed fields keep their saved keys through aliases (`model_profile`, `sampling_profile`).

**Scores don't depend on list order.** Vehicles are paired by label first, then by most matching fields, with ties broken by content. A model that lists vehicles in a different order isn't punished.

**Unavailable LLMs fail clearly.** A missing API key or **`LLMUnavailable`** stops a single run with an error. With `--all`, the app moves on to the next LLM profile and keeps the runs already saved.

**One source for comparison tables.** The terminal table and REPORT.md's appendix are built from the same **`ExtractionRunComparisonRow`**s. A test checks that the appendix matches, so the two can't drift apart.