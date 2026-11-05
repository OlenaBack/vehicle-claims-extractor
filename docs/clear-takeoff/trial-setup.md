# Clear Takeoff — Trial Preparation

**Status:** In preparation (2026-11-01)
**Repository:** `OlenaBack/vehicle-claims-extractor`
**Preparation branch:** `clear-takeoff/trial-preparation`
**Reference:** Clear Takeoff `MVP.md`, `PLAN.md`, and `rules/clear-takeoff-v0.1.md` as frozen by tag `rules-v0.1` (see **Decorator**). The tag identifies the frozen rules and MVP documentation; this trial records its own starting snapshot commit separately (see **Starting snapshot**).

## Trial task

Reimplement **single-accident narrative extraction with response validation and at most one repair attempt**. Codex designs the helpers within `vehicle_accidents_extractor/extraction/`. On this branch the previous implementation is still present:

- `vehicle_accidents_extractor/extraction/accident_extractor.py`
- `vehicle_accidents_extractor/extraction/prompt_builder.py`
- `vehicle_accidents_extractor/extraction/response_validator.py`

In the snapshot, `accident_extractor.py` becomes a public-contract stub and the other two files are removed (see **Snapshot requirements**). Keep `extraction_status.py` and `prompt_loader.py` unchanged; code outside the edit scope uses them.

Preserve `AccidentExtractor.extract(narrative: str) -> AccidentExtractionOutcome`, its outcome structure, and compatibility with existing callers. On the first valid response return `valid`; after a successful repair return `repaired`; after unsuccessful permitted attempts return `failed`. Unrepairable responses fail without a repair attempt. The full behavior given to both runs is in the request file (`docs/clear-takeoff/feature-request.md`).

**Allowed additional edit:** Only the extractor assembly lines inside `AccidentBatchExtractorBuilder.build()`, and the import lines they require, in `vehicle_accidents_extractor/batch/accident_batch_extractor.py`. No other edits to that file or `batch/`, `llm/`, schema, prompts, or record definitions. Keep the builder's public fluent chain and result unchanged. Allow the skill to choose helper names, classes, and responsibilities within `extraction/` while preserving the public extractor outcome contract. No implementation files have been removed from this branch.

## Fixed coding setup

- **Coding agent:** OpenAI Codex.
- **Model selected:** GPT-6.1 Sol, Medium reasoning effort (reported available locally). **Codex CLI:** 0.164.0. Confirm effective runtime settings before each run.
- **Coding skill:** Matt Pocock's `implement`, source repository [mattpocock/skills](https://github.com/mattpocock/skills), source commit `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d`. Local skill content was inspected; the user's reported SHA-256 is `483BDC4CCF4AC31D86AC7BEEAA0D0DB80313E71E120BB8C59B3196AE5DECD53D`. `implement` calls `tdd` and `code-review`: install both from the same source commit, identically in both runs, and record their SHA-256 values too.
- **Glossary:** Existing approved `GLOSSARY.md`, identical in both runs. Do not run additional design or domain-modeling workflows that would change shared inputs.
- **Decorator:** [Clear Takeoff v0.1 rules](https://github.com/OlenaBack/clear-takeoff/blob/15edec369d701ba125e5c31d36389a63713947ee/rules/clear-takeoff-v0.1.md), frozen by annotated tag `rules-v0.1` on commit `15edec369d701ba125e5c31d36389a63713947ee` of `OlenaBack/clear-takeoff`. **Status: tag pending creation and remote verification.** Expected rules file at that commit: blob `33a07c62ec43fb931a3a54d47c02dc6a5f453b30`, SHA-256 `ff0e5ffad35b44bebcf16df7d537f71058559264b76e9edce283b5aef9867c78` (unchanged since `417169d`). Mark the tag verified only after `git ls-remote --tags origin rules-v0.1` lists it and `git rev-parse "rules-v0.1^{commit}"` returns that commit.
- **Shared project instructions:** Neutral `AGENTS.md`. The baseline uses only the shared instructions. The decorated run appends the full, unchanged text of `rules/clear-takeoff-v0.1.md` at the `rules-v0.1` tag to `AGENTS.md`; record the SHA-256 of the resulting `AGENTS.md`.
- **Starting snapshot:** commit _(to be recorded)_ of the snapshot repository; both run directories are clones at this commit.

## Validation and evaluation

- **Shared prewritten acceptance tests:** `tests/test_clear_takeoff_acceptance.py`, testing via `AccidentBatchExtractorBuilder.with_llm_client(fake)` and saved JSONL records. Use these unchanged in both runs, alongside the skill's normal tests and review. Tests were written on the preparation branch; six cases were reported passing against the existing implementation. Re-run after changes.
- Capture the **initial generated code before review-driven corrections** in each run.
- Compare the two implementations with a **blind LLM evaluation**, assessing each independently before comparing. Score semantic consistency, self-explanatory code, cohesive responsibilities, and readable execution flow (1–5 each), with concrete code evidence. Record trade-offs and a justified comparison; scores are subjective, not proof of superiority.
- **Blind judge prompt:** `docs/clear-takeoff/blind-evaluation-prompt-v0.1.md` (written before either run; freeze with trial snapshot). **Inputs:** Give the judge only the exported files in scope (`extraction/` and the builder's assembly lines) under randomly assigned neutral labels (A/B), with no branch names, git history, commit messages, or `AGENTS.md`. Instruct it not to guess which implementation is which.
- Use the same task, approved public contract and design, starting snapshot, Codex model/settings, installed skill revisions, and glossary in both runs. Only the decorated run receives Clear Takeoff rules.
- Do not change either implementation based on evaluation findings before recording the comparison.

**Run shared tests:** Install development dependencies with `python -m pip install -r requirements-dev.txt`, then run `python -m pytest tests/test_clear_takeoff_acceptance.py` (in the snapshot: `tests/test_accident_extraction_contract.py`).

## Snapshot requirements

Build the history-free snapshot from this branch **by exclusion**. Do not delete these files from the preparation branch; the experiment documentation stays available here.

1. **Exclude `docs/clear-takeoff/` entirely.** The trial specification and the blind judge prompt stay outside both agents' working directories.
2. **Rename the acceptance test** to `tests/test_accident_extraction_contract.py`. Keep its content and assertions unchanged.
3. **Provide one identical request file** to both runs: copy `docs/clear-takeoff/feature-request.md` to the snapshot root as `FEATURE_REQUEST.md`. It specifies the public contract, permitted changes, and expected behavior, and does not mention Clear Takeoff, its rules, or the evaluation criteria.
4. **Exclude `.git` history** and any other files containing the previous implementation or experiment instructions.
5. **Public-contract stub.** Code outside the edit scope imports from `extraction/`: the builder imports `AccidentExtractor`, the record writer imports `AccidentExtractionOutcome`, and `extraction_run_records.py` imports `ExtractionStatus`. Replace `extraction/accident_extractor.py` with a stub that has a neutral module docstring, the unchanged `AccidentExtractionOutcome` dataclass, and `AccidentExtractor.extract(narrative: str) -> AccidentExtractionOutcome` raising `NotImplementedError`. Keep `extraction_status.py` and `prompt_loader.py` unchanged. Delete `prompt_builder.py` and `response_validator.py`; their names would reveal the previous design.
6. **Builder adjustment.** In the snapshot's `batch/accident_batch_extractor.py`, remove the imports of the two deleted modules and reduce the extractor assembly to `accident_extractor = AccidentExtractor()`. Nothing else in the file changes.
7. **One snapshot repository, two clones.** Create a new repository from the snapshot with a single commit on a branch named `trial` and no remote, and record that commit under **Starting snapshot**. Clone it into two separate run directories (baseline and decorated) and remove the clones' remote, so neither run can reach this repository's history. `implement` commits inside its run directory.
8. **Neutral branch rule.** In the snapshot's `AGENTS.md`, replace the `clear-takeoff/*` branch rule with: "Commit only to the current branch, `trial`; do not create, switch, or push branches."

## Remaining preparation

1. Verify the effective model/settings and the installed skill revisions. Once the tag is pushed, verify `rules-v0.1` remotely as described under **Decorator**.
2. Freeze the request file, the blind judge prompt, and prepared answers for expected clarifying questions; keep all three in `docs/clear-takeoff/`.
3. Build the snapshot repository following the snapshot requirements, neutralizing solution-revealing README diagrams and REPORT/CHANGELOG details. Preserve identical non-solution context in both runs. Record its commit.
4. Verify the snapshot: the shared contract tests fail only at the stub (`NotImplementedError`); no file mentions Clear Takeoff, the rules, or the removed helpers; the history contains only the snapshot commit. Then clone it into the two run directories, append the rules to `AGENTS.md` only in the decorated directory, and record its SHA-256.
5. Run both trials and capture the code before review fixes. Copy each result to `clear-takeoff/baseline` or `clear-takeoff/decorated` in this repository, then record the blind evaluation.

## Safety

**Never commit, push, or merge experiment changes to `main` or `master`.** In this repository, work only on explicitly named `clear-takeoff/*` branches; in the run directories, only on `trial`. Verify repository and target branch before every write.
