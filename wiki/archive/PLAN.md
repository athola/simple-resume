# Project Plan

This document outlines the `simple-resume` development plan.

## Project Goals

-   Generate resumes from structured data formats (YAML, JSON).
-   Support custom templates and color schemes via YAML configuration.
-   Keep test coverage above 85%; document all public APIs.

## Phase 1: Core Functionality and Refinement (Completed)

-   [x] Initial YAML-based resume generation.
-   [x] HTML and PDF output formats.
-   [x] Basic template system.
-   [x] Initial command-line interface (CLI).
-   [x] Consolidated `README.md` with wiki links.
-   [x] `wiki/Contributing.md`
-   [x] `wiki/Usage-Guide.md`
-   [x] `wiki/Development-Guide.md`
-   [x] Enhanced external palette loading with direct color definitions.
-   [x] Optimized print-friendly color palettes for black/white contrast.
-   [x] Fixed external palette validation conflicts.

## Phase 2: Documentation and Usability (Completed)

-   [x] Expanded wiki with detailed guides.
-   [x] Published stability policy and API reference (`docs/reference.md`).
-   [x] **Major architectural refactor**: Migrated to functional core, imperative shell architecture.
-   [x] **Enhanced API surface**: Redesigned Resume class with pandas-like symmetric I/O patterns.
-   [x] **Improved session management**: Enhanced ResumeSession with caching and statistics.
-   [x] **Comprehensive sample files**: Added demo resumes showcasing all features.
-   [x] **Architecture documentation**: Added functional core-shell design docs.
-   [x] **Error handling improvements**: Enhanced exception hierarchy and validation.
-   [x] **LaTeX documentation**: Added comprehensive LaTeX support documentation with examples and compilation instructions.
-   [x] **Enhanced README**: Improved documentation structure with better LaTeX support coverage.
-   [ ] Improve error messages for user-friendliness.
-   [ ] Add "live preview" feature to web UI.

## Phase 3: Feature Expansion

-   [ ] Add at least three new resume templates.
-   [ ] Evaluate and potentially integrate new PDF rendering engine to improve quality/performance.
-   [ ] Add support for JSON Resume format to improve interoperability.
-   [ ] Add support for generating cover letters from Markdown.

## Tooling Notes

The validation process runs `ruff`, `mypy`, `ty`, and `pytest`. Markdown linting/formatting tools (`blacken-docs`, `markdownlint`) no longer run on `README.md` and `wiki/` files, as these are frequently updated from an external source. These files no longer block the `make validate` command.

To keep validation fast, README/wiki rewrites will land through doc-only branches anchored to a recorded baseline (`docs/doc-baseline.md`, refreshed via `scripts/doc_baseline.sh`). Mainline work should avoid touching those files unless the baseline is bumped first, preventing huge markdown diffs in day-to-day PRs.
