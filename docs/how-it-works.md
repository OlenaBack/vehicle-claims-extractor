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