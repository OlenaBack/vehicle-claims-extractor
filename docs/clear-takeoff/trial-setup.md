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

- **Coding agent:** OpenAI Codex (selected instead of Claude Code). Record the exact Codex version and selected OpenAI model before either run; the model is **not yet pinned**.
- **Skill source:** Matt Pocock's [Skills for Real Engineers](https://github.com/mattpocock/skills), commit `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d` (repository revision checked 2026-11-01).
- **Coding workflow candidate:** `implement` (builds from a spec/tickets and invokes `tdd` and `code-review`). Confirm compatibility with the approved MVP's requirement to compare *initial generated code before review fixes*, and avoid creating extra uncontrolled inputs.
- **Glossary skill:** Matt Pocock's `domain-modeling`; document any limitations and approve the glossary before either run.
- **Supporting discipline (subject to fit):** `codebase-design` and `tdd`. Keep the **same frozen skill set** in both baseline and decorated runs.
- **Superseded selection:** Anthropic `feature-dev` v1.0.1 and Claude Sonnet 5.5 were previously considered, but are **not** the planned toolchain after the switch to Codex.
- **Installation:** The Matt Pocock repository documents Codex support using `npx skills@latest add mattpocock/skills`. Verify installed files match the frozen source revision; do not permit later updates to change either run.
- The baseline and decorated runs must use identical coding skill instructions, model, approved glossary, design, and tests. Only the decorated run adds the frozen Clear Takeoff engineering rules.

## Controls and open preparation work

1. Verify the coding skill meets the approved MVP fit criteria, and record source/revision; document glossary skill limitations.
2. Prepare approved feature requirements, glossary, design note identifying the public entry point, and prewritten acceptance tests.
3. Review existing `AGENTS.md` engineering guidance so it does not contaminate the baseline. Establish identical shared context for both runs.
4. Freeze the starting commit, model and skill revisions, approved inputs, Clear Takeoff rules commit, and exact decorated `AGENTS.md` rules section.
5. When the preparation state is ready, create `clear-takeoff/baseline` and `clear-takeoff/decorated` from the **same prepared commit**. Capture generated code before review corrections and record run questions and answers.

## Repository safety guardrail

**Never commit, push, or merge experiment changes to `main` or `master`.** All trial preparation and experiment changes must stay on explicitly named `clear-takeoff/*` branches. Verify the repository and target branch before every write. The existing default branch is not an experiment destination.
