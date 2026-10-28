# Engineering preferences

- Choose precise names that reflect actual behavior, domain, and scope. Use generic names only for genuinely reusable behavior.
- Define what each module or class owns before implementing it. Keep responsibilities explicit and cohesive, and prefer simple solutions: add abstractions, files, or configuration only when a real requirement justifies them.
- Check semantic consistency between names, interfaces, data, and behavior; working code alone is not enough.
- Explain design decisions in plain language with their benefits, costs, and main alternative. Challenge assumptions, including mine; don't agree with a design just because I suggested it.
- Follow the project's existing conventions and domain vocabulary in code, documentation, and messages; when a glossary exists, follow it.
- Describe code behavior directly in comments and docstrings.
- Pass dependencies such as paths, clients, and configuration from the entry point into modules.
- Make the caller's code read as the flow: name helpers after the work they do, and use fluent chaining for setup choices where it reads better than named arguments. A builder must make its required settings explicit and fail clearly when one is missing.
- Fail clearly when assumptions are violated; no silent fallbacks or swallowed errors without a stated reason.
- Verify changes against the intended behavior and requirements, not only that the code runs.
- Work incrementally: change one file or settle one decision at a time, and wait for approval before moving to the next.
