# Clear Takeoff — Trial Preparation

**Status:** In preparation (2026-11-01)  
**Repository:** `OlenaBack/vehicle-claims-extractor`  
**Preparation branch:** `clear-takeoff/trial-preparation`  
**Reference:** Approved Clear Takeoff MVP and PLAN.md in `OlenaBack/clear-takeoff`.

## Trial feature

Reimplement **single-accident text extraction with response validation and one repair attempt**.

Proposed implementation files to remove *later*, only on the preparation branch:

- `vehicle_accidents_extractor/extraction/accident_extractor.py`
- `vehicle_accidents_extractor/extraction/prompt_builder.py`
- `vehicle_accidents_extractor/extraction/response_validator.py`

Keep supporting models, schema, LLM client interface, and tests. Use a fake LLM client for deterministic tests; no live LLM calls in acceptance tests. No implementation files have been removed as part of recording this document.

## Coding setup

- Coding skill candidate: **Anthropic `feature-dev` plugin v1.0.1**, official source `anthropics/claude-plugins-official`, path `plugins/feature-dev`, repository commit `a7ba5b93db0c7c8d17f3f1d25853adca79598a1a` (verified 2026-11-01). Source: https://github.com/anthropics/claude-plugins-official/tree/a7ba5b93db0c7c8d17f3f1d25853adca79598a1a/plugins/feature-dev . **Installed plugin revision and model behavior in the execution environment still need verification.**
- Glossary skill candidate: `domain-modeling`. **Exact source, revision, and limitations: pending verification.**
- Coding model selection: **Claude Sonnet 5.5**, model ID `claude-sonnet-5-5` (verified in Anthropic documentation, 2026-11-01). Confirm this ID is available in the actual Claude Code environment before the experiment. Use the same model and effort setting for both runs. Source: https://platform.claude.com/docs/en/models/sonnet-5-5/overview
- The baseline and decorated runs must use identical skill instructions and model versions. The decorated run adds only frozen Clear Takeoff rules.

## Controls and open preparation work

1. Verify the coding skill meets the approved MVP fit criteria, and record source/revision; document glossary skill limitations.
2. Prepare approved feature requirements, glossary, design note identifying the public entry point, and prewritten acceptance tests.
3. Review existing `AGENTS.md` engineering guidance so it does not contaminate the baseline. Establish identical shared context for both runs.
4. Freeze the starting commit, model and skill revisions, approved inputs, Clear Takeoff rules commit, and exact decorated `AGENTS.md` rules section.
5. When the preparation state is ready, create `clear-takeoff/baseline` and `clear-takeoff/decorated` from the **same prepared commit**. Capture generated code before review corrections and record run questions and answers.

## Repository safety guardrail

**Never commit, push, or merge experiment changes to `main` or `master`.** All trial preparation and experiment changes must stay on explicitly named `clear-takeoff/*` branches. Verify the repository and target branch before every write. The existing default branch is not an experiment destination.
