# Functional Core and Imperative Shell Inventory

This document inventories modules refactored to follow the "functional core, imperative shell" pattern.

| Module | Side Effects | Core Logic | Proposed Shell Adapter | Notes |
| --- | --- | --- | --- | --- |
| `src/simple_resume/utilities.py` | Reads YAML, accesses filesystem for palettes, mutates config dictionaries, invokes Markdown renderer. | Validate and normalize resume data. | A `utilities_shell.load_resume(name, paths)` handles filesystem/palette lookups, then calls pure `normalize_resume(raw)`. | Normalizer function exists in same module as I/O code. Separating them allows testing data rules without filesystem access. |
| `src/simple_resume/hydration.py` | Reads YAML, expands Markdown, derives colors, builds asset paths. | Convert raw YAML structure into hydrated data structure. | Shell module loads raw data, determines template paths, then calls pure `hydrate_resume(raw, config)`. | Logic currently intertwined; lazy import previously mitigated some coupling. |
| `src/simple_resume/cli.py` | Parses CLI arguments, validates files, constructs `GenerationConfig`, calls generation backends, prints to console. | Provide user interface for generation commands. | CLI remains a shell. Decision-making logic (e.g., formats, single vs. batch processing) moves to pure planner function returning command objects. | First module being refactored. |
| `src/simple_resume/core/pdf_generation.py` | Writes `.tex` and `.pdf` files, calls LaTeX as subprocess, measures file sizes. | Determine PDF content and metadata. | Shell adapter manages filesystem I/O and subprocesses; pure core function describes render content. | Current function mixes all concerns. Future refactoring can have core function return "render actions" for shell execution. |
| `src/simple_resume/session.py` | Manages temporary directories, caches, open file handles. | Provide high-level orchestration API. | Shell will be thin context manager for filesystem/session state; core produces operations for execution. | Single-resume commands use generation planner. Batch and session APIs still mix orchestration with I/O. |
| `src/simple_resume/shell/generation.py` | Executes generation via subprocesses (e.g., LaTeX). | Module is already shell-like but not coordinated with a core planner. | Module should update to use new command objects, making it common execution path for CLI, sessions, and future services. | Align `shell` and `core` module naming during rollout to avoid confusion. |

## Next Steps

The following steps should be taken for each module being refactored:

1.  Define clear inputs and outputs (plain dictionaries or dataclasses) for pure core functions.
2.  Identify callers that will become shells (e.g., CLI, session, services).
3.  Add unit tests for pure functions before refactoring I/O code.
4.  Track refactoring status in ADR to provide visibility into modules still mixing concerns.
