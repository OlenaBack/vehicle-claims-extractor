# vehicle-claims-extractor

Extract structured data from vehicle accident descriptions and compare a provider LLM with a local model on accuracy, validity, latency and cost.

The project requirements are in [REQUIREMENTS.md](REQUIREMENTS.md).

## Data

`data/batches/batch-01/`:

- `texts/<SCASEID>.txt`: 30 accident descriptions sourced from the National Highway Traffic Safety Administration (NHTSA), adapted into 20 English, 5 Swedish and 5 mixed English–Swedish texts. One file per case, named by NHTSA case ID.
- `golden.jsonl`: hand-made labels for 10 of the 30 texts, one record per line.

Source and license: [data/README.md](data/README.md).

## Extraction schema

Defined in [`vehicle_accidents_extractor/schema.py`](vehicle_accidents_extractor/schema.py).

## LLM client

Defined in [`vehicle_accidents_extractor/llm/llm_client.py`](vehicle_accidents_extractor/llm/llm_client.py).

`LLMClient` connects to one model (OpenRouter or Ollama) through the OpenAI SDK. It handles retries itself instead of the SDK, so every try is recorded for a fair comparison. `LLMAttempt` holds one try's outcome, latency and token usage; `LLMResult` holds the final answer and all its attempts.

## Package structure

- [`extraction/`](vehicle_accidents_extractor/extraction/): accident extraction, prompt loading and building, and response validation.
- [`evaluation/`](vehicle_accidents_extractor/evaluation/): accident scoring and vehicle matching.
- [`runs/`](vehicle_accidents_extractor/runs/): extraction run assembly and execution, batch processing, and extraction record writing.
- [`llm/`](vehicle_accidents_extractor/llm/): model communication, configuration loading and [`config.toml`](vehicle_accidents_extractor/llm/config.toml).
- [`input_paths.py`](vehicle_accidents_extractor/input_paths.py) and [`artifact_paths.py`](vehicle_accidents_extractor/artifact_paths.py): locations for batch inputs and saved extraction records.

The schema remains at package level. [`main.py`](main.py) connects the components.

## Data flow

```mermaid
flowchart TD
    ConfigFile["llm/config.toml"] --> Config["Config<br/>ModelConfig + Sampling"]
    TextFiles["data/batches/&lt;batch&gt;/texts/*.txt"] -->|paths| Inputs["InputPaths"]
    PromptFiles["prompts/&lt;version&gt;/"] -->|selected prompt files| RunBuilder
    Config --> Main
    Inputs --> RunBuilder
    Main["main.run()"] -->|config + selected profiles| RunBuilder["ExtractionRunBuilder"]
    RunBuilder -->|builds| Run["ExtractionRun<br/>run metadata + client + extractor + file paths"]
    Run -->|ping()| Client["LLMClient"]
    Run --> Runner["AccidentExtractionRunner"]
    Runner -->|read one file as text| Extractor["AccidentExtractor.extract(text)"]
    RunBuilder -->|system + repair prompts| Builder["PromptBuilder"]
    Extractor --> Builder
    Builder -->|messages| Client
    Client -->|response + attempts| LLMResult["LLMResult<br/>LLMAttempt entries"]
    LLMResult --> Validator["ResponseValidator.validate()"]
    Validator -->|valid| Accident["VehicleAccident"]
    Validator -->|repairable error| Repair["PromptBuilder.repair()"]
    Repair -->|corrected messages| Client
    Accident --> ExtractionOutcome["AccidentExtractionOutcome"]
    LLMResult --> ExtractionOutcome
    ExtractionOutcome --> Runner

    Runner -->|accident_id + outcome| Writer["ExtractionRecordWriter"]
    Run --> Metadata["ExtractionRunMetadata"]
    Metadata --> Writer
    Writer --> Record["AccidentExtractionRecord"]
    Record --> JSONL["extractions/&lt;batch&gt;/*.jsonl"]
    Main --> ArtifactPaths["ArtifactPaths"]
    Metadata --> ArtifactPaths
    ArtifactPaths -->|records path| Run

    JSONL --> Reader["read_accident_extraction_records()"]
    Inputs -->|golden_labels_path()| GoldenFile["data/batches/&lt;batch&gt;/golden.jsonl"]
    GoldenFile --> Golden["GoldenRecord entries"]
    Reader --> Metrics["calculate_run_metrics()"]
    Golden --> Metrics
    Metrics --> Score["AccidentScore + RunMetrics"]
```
