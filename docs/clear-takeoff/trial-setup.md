# Clear Takeoff — Trial Preparation

**Status:** In preparation (2026-11-01)
**Repository:** `OlenaBack/vehicle-claims-extractor`
**Preparation branch:** `clear-takeoff/trial-preparation`
**Reference:** Clear Takeoff `MVP.md`; approved trial decisions take precedence where the original MVP has not yet been updated.

## Trial task

Reimplement **single-accident narrative extraction with response validation and at most one repair attempt** in these three files:

- `vehicle_accidents_extractor/extraction/accident_extractor.py`
- `vehicle_accidents_extractor/extraction/prompt_builder.py`
- `vehicle_accidents_extractor/extraction/response_validator.py`

Preserve `AccidentExtractor.extract(narrative: str) -> AccidentExtractionOutcome`, its outcome structure, and compatibility with existing callers. On the first valid response return `valid`; after a successful repair return `repaired`; after unsuccessful permitted attempts return `failed`. Unrepairable responses fail without a repair attempt.

Keep supporting schema, LLM interface, status type, glossary and batch integration unchanged. Allow the coding skill to choose internal implementation details within the approved design. No implementation files have been removed yet.

## Fixed coding setup

- **Coding agent:** OpenAI Codex.
- **Model selected:** GPT-6.1 Sol, Medium reasoning effort **subject to confirmation in the local Codex installation**. Record the model identifier and Codex version actually available before either run; if unavailable, approve a replacement and use it for both.
- **Coding skill:** Matt Pocock's `implement`, source repository [mattpocock/skills](https://github.com/mattpocock/skills), source commit `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d`. Verify the locally installed skill matches this revision.
- **Glossary:** Existing approved `GLOSSARY.md`, identical in both runs. Do not run additional design or domain-modeling workflows that would change shared inputs.
- **Decorator:** [Clear Takeoff v0.1 rules](https://github.com/OlenaBack/clear-takeoff/blob/clear-takeoff/rules-v0.1/rules/clear-takeoff-v0.1.md), branch `clear-takeoff/rules-v0.1`, latest reviewed commit `b7c4c0bb9745afe8e01b3564554f6d909723f986`. Freeze the exact rule text in the decorated run.
- **Shared project instructions:** Neutral `AGENTS.md` on this preparation branch. The baseline uses only the shared instructions; the decorated run adds the frozen rule text.

## Validation and evaluation

- **No separate prewritten deterministic acceptance-test suite** for this MVP. Let the `implement` skill perform its normal tests and review workflow; record what verification was run and whether it passed.
- Capture the **initial generated code before review-driven corrections** in each run.
- Compare the two implementations with a **blind LLM evaluation**, assessing each independently before comparing. Score semantic consistency, self-explanatory code, cohesive responsibilities, and readable execution flow (1–5 each), with concrete code evidence. Record trade-offs and a justified comparison; scores are subjective, not proof of superiority.
- Use the same task, approved public contract and design, starting source snapshot, Codex model/settings, installed skill revision, and glossary in both runs. Only the decorated run receives Clear Takeoff rules.
- Do not change either implementation based on evaluation findings before recording the comparison.

## Remaining preparation

1. Confirm the selected model and Codex version locally; verify installed `implement` skill against its frozen source.
2. Freeze the written task/design inputs and the exact common starting commit.
3. Prepare the controlled starting snapshot for reimplementation **only on a `clear-takeoff/*` branch**; check existing source-code visibility does not leak a solution into either run.
4. Create `clear-takeoff/baseline` and `clear-takeoff/decorated` from the same prepared commit. Verify their shared inputs and the decorator difference before invoking Codex.
5. Run both trials, capture code before review fixes, and record the blind evaluation.

## Safety

**Never commit, push, or merge experiment changes to `main` or `master`.** Work only on explicitly named `clear-takeoff/*` branches. Verify repository and target branch before every write.
