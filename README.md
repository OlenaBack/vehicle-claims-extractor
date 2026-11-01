# vehicle-claims-extractor

Extract structured data from vehicle accident narratives and compare a provider LLM with a local model on accuracy, validity, latency and cost.

The project requirements are in [REQUIREMENTS.md](REQUIREMENTS.md). The measured comparison and production recommendation are in [REPORT.md](REPORT.md).

## Setup

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Put your OpenRouter key in `.env` as `OPENROUTER_API_KEY`. `.env` is not committed. Without a key, a single run fails with a message; `--all` skips that LLM and continues.

### Local model (Ollama)

1. Install Ollama from <https://ollama.com/download>.
2. Start the server. The Windows app starts it automatically; otherwise run `ollama serve`. It listens on `http://localhost:11434`.
3. Pull the model named in [`llm_config.toml`](vehicle_accidents_extractor/llm/llm_config.toml) (about 2 GB):

   ```powershell
   ollama pull llama3.2:3b
   ```

If Ollama is not reachable, a single run fails with a message; `--all` skips that LLM and continues. Before a local run, one small unrecorded request loads the model, so model loading time is not part of the measured latency.

## Run

```powershell
python main.py                                          # openrouter, prompt v1, deterministic, batch-01
python main.py --llm-profile ollama --prompt v2 --sampling-profile varied
python main.py --all                                    # every LLM profile × prompt × sampling profile, then a comparison table
```

Options: `--llm-profile` (`openrouter` or `ollama`), `--prompt` (a folder under `prompts/`), `--sampling-profile` (`deterministic` or `varied`) and `--batch`. The profile options select sections of `llm_config.toml` by name. Use `--all` to run every configured combination and print a comparison; unavailable LLMs are skipped and completed extraction runs are kept.

Evaluate one saved run against the golden labels:

```powershell
python evaluate.py --extraction-run extractions\batch-01\<run file>.jsonl
```

To compare selected saved runs, pass their JSONL paths with `--compare`; add `--markdown` for a report-ready table.

Settings (LLM profiles, prices, timeout, retries and sampling profiles) are in [`llm_config.toml`](vehicle_accidents_extractor/llm/llm_config.toml). Prompt versions and their changelog are in [`prompts/`](prompts/).

## Files and outputs

Accident narratives and golden labels are stored in `data/batches/<batch>/`. Each extraction run writes a JSONL file to `extractions/<batch>/`. Run metadata uses the keys `model_profile` and `sampling_profile` for compatibility with earlier runs. `evaluate.py` reads a saved run and compares its records with that batch's golden labels.

The input data source and adaptations are documented in [data/README.md](data/README.md).

## How it works

See [docs/how-it-works.md](docs/how-it-works.md) for the extraction flow and the design decisions.
