# vehicle-claims-extractor

Extract structured data from vehicle accident narratives and compare a provider LLM with a local model on accuracy, validity, latency and cost.

The project requirements are in [REQUIREMENTS.md](REQUIREMENTS.md).

## Data

`data/batches/batch-01/`:

- `texts/<SCASEID>.txt`: 30 accident narratives sourced from the National Highway Traffic Safety Administration (NHTSA), adapted into 20 English, 5 Swedish and 5 mixed English–Swedish texts. One file per case, named by NHTSA case ID.
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
- [`batch/`](vehicle_accidents_extractor/batch/): batch extraction setup and execution, and accident extraction record writing.
- [`llm/`](vehicle_accidents_extractor/llm/): model communication, configuration loading and [`config.toml`](vehicle_accidents_extractor/llm/config.toml).
- [`input_paths.py`](vehicle_accidents_extractor/input_paths.py) and [`artifact_paths.py`](vehicle_accidents_extractor/artifact_paths.py): locations for batch inputs and saved extraction records.

The schema remains at package level. [`main.py`](main.py) connects the components.

## Extraction and evaluation flow

### Build an extraction run

```mermaid
flowchart TD
    Main[main entry point] -->|loads| ConfigFile[Config file]
    ConfigFile -->|validated as| Config[Config]
    Main -->|passes config and choices| Builder[AccidentBatchExtractorBuilder]
    Main -->|creates and passes| Inputs[InputPaths]
    Main -->|passes output path resolver| Builder
    Builder -->|requests batch input paths| Inputs
    Inputs -->|returns batch input paths and prompt directory| Builder
    Builder -->|loads selected version with| PromptLoader[Prompt loader]
    PromptFiles[Prompt files] -->|read by| PromptLoader
    PromptLoader -->|returns| Prompts[ExtractionPrompts]
    Prompts -->|system and repair text| PromptBuilder[PromptBuilder]
    Builder -->|creates| PromptBuilder
    Builder -->|uses run metadata| ArtifactPaths[ArtifactPaths]
    ArtifactPaths -->|returns extraction run records path| Builder
    Builder -->|builds| BatchExtractor[AccidentBatchExtractor]
    Builder -->|creates| Client[LLMClient]
    Builder -->|creates| AccidentExtractor[AccidentExtractor]
    Builder -->|creates| Validator[ResponseValidator]
```

### Process an accident batch

```mermaid
flowchart TD
    Main[main entry point] -->|pings, then extracts the batch| BatchExtractor[AccidentBatchExtractor]
    BatchExtractor -->|reads each narrative and uses| AccidentExtractor[AccidentExtractor]
    AccidentExtractor -->|returns outcome| BatchExtractor
    BatchExtractor -->|sends accident ID and outcome| Writer[AccidentExtractionRecordWriter]
```

### Extract and validate one accident narrative

```mermaid
flowchart TD
    Narrative[Accident narrative] --> Extractor[AccidentExtractor]
    Extractor -->|requests initial messages| PromptBuilder[PromptBuilder]
    PromptBuilder -->|initial or repair messages| Extractor
    Extractor -->|sends chat request| Client[LLMClient]
    Client -->|returns response and attempts| LLMResult[LLMResult]
    LLMResult --> Extractor
    Extractor -->|validates response| Validator[ResponseValidator]
    Validator -->|valid data| Accident[VehicleAccident]
    Validator -->|repairable or unrepairable error| Extractor
    Accident --> Extractor
    Extractor -->|requests repair messages| PromptBuilder
    Extractor -->|valid, repaired, or failed| Outcome[AccidentExtractionOutcome]
```

### Save accident extraction records

```mermaid
flowchart TD
    BatchExtractor[AccidentBatchExtractor] -->|provides run metadata and path| Writer[AccidentExtractionRecordWriter]
    BatchExtractor -->|provides accident ID and outcome| Writer
    Writer -->|creates| Record[AccidentExtractionRecord]
    Record -->|writes one JSONL line| JSONL[Saved extraction run]
```

### Evaluate a saved extraction run

```mermaid
flowchart TD
    Evaluate[evaluate entry point] -->|passes extraction run path| Reader[Accident extraction record reader]
    JSONL[Saved extraction run] -->|read as| Reader
    Reader -->|extraction records| Evaluate
    Evaluate -->|requests golden labels path| Inputs[InputPaths]
    Inputs -->|returns golden labels path| Evaluate
    Evaluate -->|reads| GoldenFile[Golden labels file]
    GoldenFile -->|validated as| Golden[GoldenRecord entries]
    Evaluate -->|passes records and labels| Metrics[Run metrics]
    Metrics --> Scores[Accuracy validity latency cost]
```
