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

```mermaid
flowchart TD
    subgraph RunSetup[Set up extraction run]
        ConfigFile[Config file] -->|loaded and validated as| Config[Config]
        Config -->|settings| Main[main entry point]
        Main -->|config and selections| RunBuilder[ExtractionRunBuilder]
        Main -->|creates and passes| Inputs[InputPaths]
        Main -->|passes output path resolver| RunBuilder
        RunBuilder -->|requests description paths| Inputs
        Inputs -->|returns description paths| RunBuilder
        Inputs -->|provides prompt directory| RunBuilder
        RunBuilder -->|uses run metadata| ArtifactPaths[ArtifactPaths]
        ArtifactPaths -->|returns extraction run records path| RunBuilder
        RunBuilder -->|loads selected version| PromptLoader[Prompt loader]
        PromptFiles[Prompt files] -->|read by| PromptLoader
        PromptLoader -->|returns| Prompts[ExtractionPrompts]
        Prompts -->|system and repair text| PromptBuilder[PromptBuilder]
        RunBuilder -->|builds| Run[ExtractionRun]
        RunBuilder -->|creates| Validator[ResponseValidator]
        RunBuilder -->|creates| Client[LLMClient]
        RunBuilder -->|creates| Extractor[AccidentExtractor]
    end

    subgraph BatchExtraction[Extract the accident batch]
        Main -->|checks connection| Run
        Main -->|executes| Run
        Run -->|checks connection| Client
        Run -->|reads each description and passes text| Extractor
        Extractor -->|builds messages| PromptBuilder
        PromptBuilder -->|messages| Extractor
        Extractor -->|sends request| Client
        Client -->|returns response and attempts| LLMResult[LLMResult]
        LLMResult -->|returns to| Extractor
        Extractor -->|passes response to| Validator
        Validator -->|returns validated accident| Accident[VehicleAccident]
        Accident -->|validated data| Extractor
        Validator -->|returns validation error| Extractor
        Extractor -->|returns| Outcome[AccidentExtractionOutcome]
        Outcome -->|accident ID and outcome| Run
        Run -->|writes| Writer[ExtractionRecordWriter]
        Run -->|run metadata| Writer
        Run -->|extraction run records path| Writer
        Writer -->|serializes| Record[AccidentExtractionRecord]
        Record -->|JSONL line| JSONL[Saved extraction run]
    end

    subgraph RunEvaluation[Evaluate extraction run]
        JSONL -->|read| Reader[Accident extraction record reader]
        Evaluate[evaluate entry point] -->|requests golden labels path| Inputs
        Inputs -->|returns golden labels path| Evaluate
        Evaluate -->|reads| GoldenFile[Golden labels file]
        GoldenFile -->|validated as| Golden[GoldenRecord entries]
        Reader -->|extraction records| Metrics[Run metrics]
        Golden -->|golden records| Metrics
        Evaluate -->|scores the run| Metrics
        Metrics --> Scores[Accuracy validity latency cost]
    end
```
