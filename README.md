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

## Extraction and evaluation flow

### Build an extraction run

```mermaid
flowchart TD
    Main[main entry point] -->|loads| ConfigFile[Config file]
    ConfigFile -->|validated as| Config[Config]
    Main -->|passes config and choices| Builder[ExtractionRunBuilder]
    Main -->|creates and passes| Inputs[InputPaths]
    Main -->|passes output path resolver| Builder
    Builder -->|requests description paths| Inputs
    Inputs -->|returns description paths and prompt directory| Builder
    Builder -->|loads selected version with| PromptLoader[Prompt loader]
    PromptFiles[Prompt files] -->|read by| PromptLoader
    PromptLoader -->|returns| Prompts[ExtractionPrompts]
    Prompts -->|system and repair text| PromptBuilder[PromptBuilder]
    Builder -->|creates| PromptBuilder
    Builder -->|uses run metadata| ArtifactPaths[ArtifactPaths]
    ArtifactPaths -->|returns extraction run records path| Builder
    Builder -->|builds| Run[ExtractionRun]
    Builder -->|creates| Client[LLMClient]
    Builder -->|creates| Extractor[AccidentExtractor]
    Builder -->|creates| Validator[ResponseValidator]
```

### Process the accident batch

```mermaid
flowchart TD
    Main[main entry point] -->|checks connection and executes| Run[ExtractionRun]
    Run -->|checks connection| Client[LLMClient]
    Run -->|reads each description and passes text| Extractor[AccidentExtractor]
    Extractor -->|requests initial or repair messages| PromptBuilder[PromptBuilder]
    PromptBuilder -->|messages| Extractor
    Extractor -->|sends chat request| Client
    Client -->|returns response and attempts| LLMResult[LLMResult]
    LLMResult -->|response| Extractor
    Extractor -->|passes response to| Validator[ResponseValidator]
    Validator -->|returns validated accident| Accident[VehicleAccident]
    Accident -->|validated data| Extractor
    Validator -->|returns validation error| Extractor
    Extractor -->|returns| Outcome[AccidentExtractionOutcome]
    Outcome -->|accident ID and outcome| Run
    Run -->|writes with run metadata and records path| Writer[ExtractionRecordWriter]
    Writer -->|serializes| Record[AccidentExtractionRecord]
    Record -->|JSONL line| JSONL[Saved extraction run]
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
