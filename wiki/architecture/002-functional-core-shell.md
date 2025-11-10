# ADR-002: Functional Core, Imperative Shell

## Status

Accepted (2025-11-09)

## Context

Original `simple-resume` design mixed file I/O, CLI orchestration, and domain logic within modules (e.g., `utilities`, `hydration`, `cli`, `generation`). This tight coupling led to brittle tests, slow code reviews, and widespread changes. Adopting "functional core, imperative shell" pattern separates deterministic logic from I/O side effects.

## Decision

1.  **Define Shell Boundaries:** Place all code interacting with the outside world (e.g., filesystem access, YAML parsing, CLI I/O, LaTeX subprocesses) in "shell" modules. Shell's responsibility: sequence operations, handle retries, log events, translate external events into simple data structures.

2.  **Implement a Pure Core:** Core modules expose deterministic functions operating on plain data structures (e.g., `GeneratePlanOptions -> list[GenerationCommand]`, `hydrate_resume(raw) -> dict`). These functions will not access the filesystem or global state.

3.  **Adopt Incrementally:** Refactor incrementally, starting with frequently changing code (e.g., CLI command generation). Each step must preserve existing behavior, add unit tests for new core logic, and keep the shell as a thin adapter. Address more stateful parts (e.g., sessions) later.

4.  **Use a Shared Command Model:** Communication between adapters (e.g., CLI) and core uses explicit command objects. This makes orchestration logic transparent and simplifies adding new adapters (e.g., API endpoints).

5.  **Document and Measure:** Maintain this ADR and `functional-core-shell-inventory.md` to document architecture. Track metrics like code coverage and mean time to recovery (MTTR) to verify pattern effectiveness.

## Rationale

-   Separating planning logic into a pure core makes unit testing easier and safer than CLI code.
-   Explicit command objects eliminate duplicated logic (e.g., for format iteration and overrides) and provide a single, clear interface.
-   Incremental approach avoids large-scale rewrite risks. Starting with CLI's `generate` command due to frequent regressions and existing test coverage.
-   Documentation ensures team understanding and consistent pattern application.

## Consequences

### Positive

-   CLI change planning logic in `build_generation_plan` allows testing single and batch operations without filesystem access.
-   New unit tests for core logic (e.g., `tests/unit/core/test_generation_plan.py`) are fast, providing high coverage of decision-making logic.
-   This ADR and inventory file provide a clear path for future refactoring of modules like `utilities`, `hydration`, and `pdf_generation`.

### Negative

-   Shell modules still contain significant printing and error handling logic. Future simplification needed to avoid duplication.
-   Until refactoring is complete, developers will work with both legacy code and new core/shell pattern, potentially causing confusion.

### Monitoring

-   Track code coverage of new core modules, with a goal of >90%.
-   Measure time to implement new CLI features, expecting 20-30% reduction once new pattern established.
-   Monitor defect rate in shell code. Explicit commands expected to help identify edge cases earlier.

## Follow-up Tasks

1.  Refactor the `utilities` and `hydration` modules into pure functions with shell adapters.
2.  Create shared command execution helpers for other entry points (e.g., session API, potential future HTTP services).
3.  Update onboarding documentation with checklist for creating new core and shell modules to ensure consistency.
