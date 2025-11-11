# ADR-002: Functional Core, Imperative Shell

## Status

Accepted (2025-11-09)

## Context

The original `simple-resume` design mixed file I/O, CLI orchestration, and domain logic across modules like `utilities`, `hydration`, and `generation`. This coupling caused brittle tests, slow code reviews, and cascading changes. To fix this, we are adopting the "functional core, imperative shell" pattern to separate pure, deterministic logic from I/O and other side effects.

## Decision

1.  **Define Shell Boundaries:** Place all code interacting with the outside world (e.g., filesystem access, YAML parsing, CLI I/O, LaTeX subprocesses) in "shell" modules. The shell's responsibility is to sequence operations, handle retries, log events, and translate external data (e.g., from files or CLI arguments) into simple data structures for the core.

2.  **Implement a Pure Core:** Core modules will contain only pure functions that operate on simple data structures (e.g., `GeneratePlanOptions -> list[GenerationCommand]`, `hydrate_resume(raw) -> dict`). These functions must not access the filesystem, environment variables, or other global state.

3.  **Adopt Incrementally:** Refactor incrementally, starting with frequently changing code (e.g., CLI command generation). Each step must preserve existing behavior, add fast unit tests for the new core logic, and keep the shell a thin adapter over the core. Address more stateful parts (e.g., sessions) later.

4.  **Use a Shared Command Model:** Communication between adapters (e.g., CLI) and core uses explicit command objects. This makes orchestration logic transparent and simplifies adding new adapters (e.g., API endpoints).

5.  **Document and Measure:** Maintain this ADR and `functional-core-shell-inventory.md` to document architecture. We will track metrics like code coverage and mean time to recovery (MTTR) to verify that this pattern is effective.

## Rationale

-   Moving planning logic into a pure core makes it easier and safer to unit-test than the previous CLI-dependent code.
-   Explicit command objects eliminate duplicated logic (e.g., for format iteration and overrides) and provide a single, clear interface.
-   Incremental approach avoids large-scale rewrite risks. Starting with CLI's `generate` command due to frequent regressions and existing test coverage.
-   This documentation is intended to ensure the team understands the pattern and applies it consistently.

## Consequences

### Positive

-   CLI change planning logic in `build_generation_plan` allows testing single and batch operations without filesystem access.
-   New unit tests for core logic (e.g., `tests/unit/core/test_generation_plan.py`) are fast, providing high coverage of decision-making logic.
-   This ADR and inventory file provide a clear path for future refactoring of modules like `utilities`, `hydration`, and `pdf_generation`.

### Negative

-   The shell modules still contain considerable printing and error-handling logic, which may lead to duplication. This logic should be simplified in the future.
-   Until the refactoring is complete, developers must work with both the legacy code and the new pattern, which could cause confusion.

### Monitoring

-   Track code coverage of new core modules, with a goal of >90%.
-   We will measure the time required to implement new CLI features, with a goal of a 20-30% reduction once the pattern is established.
-   We expect the explicit command objects to help identify edge cases earlier in the development process.

## Follow-up Tasks

1.  Refactor the `utilities` and `hydration` modules into pure functions with shell adapters.
2.  Create shared command execution helpers for other entry points (e.g., session API, potential future HTTP services).
3.  Update onboarding documentation with checklist for creating new core and shell modules to ensure consistency.
