# Clear Takeoff — Frozen Blind Evaluation Prompt v0.1

**Purpose:** Compare two independently generated implementations of the same accident-extraction task. Do not infer which received Clear Takeoff rules.

## Inputs
- The identical approved feature specification, public contract, glossary, and allowed edit boundary.
- Two anonymized source exports labelled **A** and **B** in randomly assigned order. Include only the changed `extraction/` code and the extractor assembly lines in `AccidentBatchExtractorBuilder.build()`.
- Shared acceptance-test outcomes, presented identically for both implementations.

Do **not** provide branch names, git history, authors, commit messages, `AGENTS.md`, or the decorator rules themselves.

## Method
1. Evaluate A on its own, then B on its own, without comparison during the individual assessments.
2. For each, score **semantic consistency**, **self-explanatory code**, **cohesive responsibilities**, and **readable execution flow** from 1 (poor) to 5 (strong).
3. Cite concrete code evidence for each judgment, including both strengths and weaknesses. Evaluate clarity within methods/classes (**zoom in**) and across the request flow (**zoom out**).
4. Check alignment with the shared glossary and existing project patterns. Flag a conflict only where code contradicts a glossary term, approved public contract, or named established pattern; a departure is justified only by a concrete requirement.
5. Consider unnecessary abstractions, hidden side effects, duplicated ownership, and unclear failure paths.
6. Compare A and B only after individual reviews. State any meaningful differences, trade-offs, and uncertain findings. A tie or insufficient evidence is valid. **Do not guess which run is baseline or decorated.**

## Interpretation
- The shared glossary is a control in both runs. Assess incremental clarity **beyond glossary compliance**, not glossary use alone.
- Shared acceptance tests provide the correctness baseline; do not conflate passing tests with readability.
- Scores are subjective, not statistical proof. No numerical success threshold applies to this one-run-per-arm exploratory trial.
- This blind assessment is primary qualitative evaluation evidence. Developer observations after the reveal are secondary context.

## Output
For each of A and B: four scores with cited source evidence, notable strengths, and concrete concerns. Then a balanced comparison, uncertainty, and a provisional conclusion without revealing or speculating about arm identity.
