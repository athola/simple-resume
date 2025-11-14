# Functional Core and Imperative Shell Inventory

This document inventories modules refactored to follow the "functional core, imperative shell" pattern.

| Module | Side Effects | Core Logic | Proposed Shell Adapter | Notes |
| --- | --- | --- | --- | --- |
| `src/simple_resume/utilities.py` (+ `src/simple_resume/utils/*.py`) | Still loads YAML, reads palette files, mutates caller-provided dicts, renders Markdown. | Config normalization, palette resolution, Markdown-to-HTML transforms. | Keep `utilities.py` as orchestration shell that calls pure helpers in `core.config_core`, `core.hydration_core`, and `core.colors`. All file/CLI access moves into `simple_resume.utils.io`. | New `simple_resume.utils` package now owns filesystem helpers and exposes deprecation shims. Remaining work is to finish migrating palette + Markdown I/O out of the core helpers. |
| `src/simple_resume/hydration.py` | Opens YAML files, expands Markdown, locates template assets. | `core.hydration_core.build_skill_group_payload` and related helpers hydrate dicts deterministically. | Thin loader that resolves paths, then forwards raw yaml + config into `core.hydration_core`. | Core helpers exist but CLI/session callers still import `hydration.py` directly. Documenting the split helps reviewers ensure new logic lands in the core module first. |
| `src/simple_resume/cli.py` | Parses CLI args, prints to stdout/stderr, triggers generation with side effects. | Command planning and batch orchestration logic. | CLI stays a shell, but should delegate to `core.plan`/`generation_plan` for decision making so tests stay pure. | Planner exists (`core.plan` + `generation_plan`), yet several subcommands fall back to inline logic. Tracking here keeps refactor momentum. |
| `src/simple_resume/core/pdf_generation_strategy.py` | Pure strategies (WeasyPrint, LaTeX) now compute actions but still reference shell utilities for filesystem validation in a few spots. | Strategy selection + orchestration decisions now live here. | Shell adapter in `shell/generation.py` should own subprocess + filesystem work, invoking strategies only for planning. | File replaces the monolithic `core/pdf_generation.py` behavior. Remaining TODO: remove the last direct file writes from strategy implementations. |
| `src/simple_resume/session/session.py` | Manages context managers, caches, stats, and dependency wiring. | Session policies (paths resolution, config defaults) and repository coordination. | Provide an imperative wrapper (`ResumeSession`) over a pure `ResumeRepository` facade plus injected loaders. | Session now builds on `simple_resume.dependencies.ResumeRepository`, but cache invalidation and telemetry live inside the class. Future state machines (batch ops, telemetry exporters) should move into dedicated shells. |
| `src/simple_resume/shell/generation.py` | Spawns subprocesses, writes LaTeX files, opens PDFs. | Currently thin layer over `generation_plan`, but lacks awareness of repo/session abstractions. | Make this the single execution shell for CLI + `ResumeSession`, so strategies never need to know about subprocesses. | Aligning shells keeps future adapters (HTTP, background jobs) from duplicating subprocess management logic. |

## Next Steps

The following steps should be taken for each module being refactored:

1.  Define clear inputs and outputs (plain dictionaries or dataclasses) for pure core functions.
2.  Identify callers that will become shells (e.g., CLI, session, services).
3.  Add unit tests for pure functions before refactoring I/O code.
4.  Track refactoring status in ADR to provide visibility into modules still mixing concerns.
