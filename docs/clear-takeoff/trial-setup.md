# Clear Takeoff — Trial Preparation

**Status:** In preparation (2026-11-01)
**Repository:** `OlenaBack/vehicle-claims-extractor`
**Preparation branch:** `clear-takeoff/trial-preparation`
**Reference:** Clear Takeoff `MVP.md`; approved trial decisions take precedence where the original MVP has not yet been updated.

## Trial task

Reimplement **single-accident narrative extraction with response validation and at most one repair attempt**. Codex may redesign helpers within `vehicle_accidents_extractor/extraction/`, including the following existing files:

- `vehicle_accidents_extractor/extraction/accident_extractor.py`
- `vehicle_accidents_extractor/extraction/prompt_builder.py`
- `vehicle_accidents_extractor/extraction/response_validator.py`

Preserve `AccidentExtractor.extract(narrative: str) -> AccidentExtractionOutcome`, its outcome structure, and compatibility with existing callers. On the first valid response return `valid`; after a successful repair return `repaired`; after unsuccessful permitted attempts return `failed`. Unrepairable responses fail without a repair attempt.

**Allowed additional edit:** Only the extractor assembly/construction lines inside `AccidentBatchExtractorBuilder.build()` in `vehicle_accidents_extractor/batch/accident_batch_extractor.py`. No other edits to that file or `batch/`, `llm/`, schema, prompts, or record definitions. Keep the builder's public fluent chain and result unchanged. Allow the skill to choose helper names, classes, and responsibilities within `extraction/` while preserving the public extractor outcome contract. No implementation files have been removed yet.

## Fixed coding setup

- **Coding agent:** OpenAI Codex.
- **Model selected:** GPT-6.1 Sol, Medium reasoning effort (reported available locally). **Codex CLI:** 0.164.0. Confirm effective runtime settings before each run.
- **Coding skill:** Matt Pocock's `implement`, source repository [mattpocock/skills](https://github.com/mattpocock/skills), source commit `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d`. Local skill content was inspected; the user's reported SHA-256 is `483BDC4CCF4AC31D86AC7BEEAA0D0DB80313E71E120BB8C59B3196AE5DECD53D`.
- **Glossary:** Existing approved `GLOSSARY.md`, identical in both runs. Do not run additional design or domain-modeling workflows that would change shared inputs.
- **Decorator:** [Clear Takeoff v0.1 rules](https://github.com/OlenaBack/clear-takeoff/blob/clear-takeoff/rules-v0.1/rules/clear-takeoff-v0.1.md), branch `clear-takeoff/rules-v0.1`, frozen tag `rules-v0.1` **pending creation/verification**; planned target is commit `417169dbd8d04ef1adba5946f0f1e16871b06efc`. Verify tag points to its final intended commit before use. Freeze the exact rule text in the decorated run.
- **Shared project instructions:** Neutral `AGENTS.md` on this preparation branch. The baseline uses only the shared instructions; the decorated run adds the frozen rule text.

## Validation and evaluation

- **Shared prewritten acceptance tests:** `tests/test_clear_takeoff_acceptance.py`, testing via `AccidentBatchExtractorBuilder.with_llm_client(fake)` and saved JSONL records. Use these unchanged in both runs, alongside the skill's normal tests and review. Tests were written on the preparation branch; execution is not yet verified.
- Capture the **initial generated code before review-driven corrections** in each run.
- Compare the two implementations with a **blind LLM evaluation**, assessing each independently before comparing. Score semantic consistency, self-explanatory code, cohesive responsibilities, and readable execution flow (1–5 each), with concrete code evidence. Record trade-offs and a justified comparison; scores are subjective, not proof of superiority.
- Use the same task, approved public contract and design, starting source snapshot, Codex model/settings, installed skill revision, and glossary in both runs. Only the decorated run receives Clear Takeoff rules.
- Do not change either implementation based on evaluation findings before recording the comparison.

## Remaining preparation

1. Verify the effective model/settings and the `rules-v0.1` tag at its intended commit; run the shared acceptance tests.
2. Freeze the written task/design inputs and the exact common starting commit.
3. Prepare a clean snapshot for reimplementation **only on a `clear-takeoff/*` branch**. Remove existing targeted implementation and neutralize solution-revealing README diagrams, REPORT/CHANGELOG details; prevent access to original implementation through git history (for example, use an exported history-free snapshot). Preserve identical non-solution context in both runs.
4. Create `clear-takeoff/baseline` and `clear-takeoff/decorated` from the same prepared commit. Verify their shared inputs and the decorator difference before invoking Codex.
5. Run both trials, capture code before review fixes, and record the blind evaluation.

## Safety

**Never commit, push, or merge experiment changes to `main` or `master`.** Work only on explicitly named `clear-takeoff/*` branches. Verify repository and target branch before every write.
