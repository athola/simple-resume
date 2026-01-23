# Changelog

This file documents all notable project changes. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-01-22

### Added

- Parse-once architecture with `ParsedDocument` class for efficient entity extraction
  - Lazy-evaluated properties via `@cached_property` reduce redundant text processing
  - `parse()` function as main entry point for the new architecture
  - Section finding helper `find_section()` for pattern-based extraction
- `Degree` dataclass replacing dictionary representation for education data
- `BERTScorer` for semantic similarity using sentence-transformers (optional dependency)
  - Install with `uv add simple-resume[bert]` or `pip install simple-resume[bert]`
  - Adds `ScorerName.BERT_SEMANTIC` and `ScorerSelection.BERT` enums
- Score and weight validation in `ScorerResult` via `constants.py` helpers
- Comprehensive test coverage for new components

### Changed

- `EntityExtractor.extract()` now accepts both `str` and `ParsedDocument` inputs
- `ExtractedEntities.degrees` changed from `list[dict[str, str]]` to `list[Degree]`
- Internal extraction methods use `ParsedDocument` for cached preprocessing

## [0.2.0] - 2026-01-21

### Added

- ATS (Applicant Tracking System) resume scoring with tournament-style NLP algorithms
  - `TFIDFScorer` for statistical term frequency and cosine similarity analysis
  - `JaccardScorer` for n-gram phrase overlap detection
  - `KeywordScorer` for exact keyword matching with fuzzy tolerance
  - `ATSTournament` for combining multiple scoring algorithms with weighted averages
  - `score_resume()` convenience function for quick resume-job matching
  - `ATSReportGenerator` for YAML/JSON/text report generation
  - `EntityExtractor` for structured data extraction from unstructured text
  - `screen` CLI command for terminal-based resume screening against job descriptions
  - Comprehensive API documentation in `wiki/API-Reference.md`
  - Scoring methodology documented in `wiki/ATS-Scoring-Rubric.md`

### Changed

- Version bump to 0.2.0 for new ATS scoring feature (minor version per semver)
- Expanded public API with 13 new exports for ATS functionality
- Enhanced error handling with new ATS-specific exceptions

### Fixed

- Linting issues in test files (moved imports to module level, fixed long lines)

## [0.1.10] - 2026-01-20

### Changed

-   TBD (update with actual changes before release)

## [0.1.9] - 2026-01-07

### Fixed

-   Package wheel now includes all Python source files, fixing installation failure (#40)
-   Updated `pyproject.toml` build configuration to properly package source code in wheels

### Added

-   Pre-commit hook `wheel-install-test` to verify package installation and execution
-   Configurable font sizes: `description_font_size`, `date_font_size`, `sidebar_font_size`

## [0.1.8] - 2026-01-03

### Added

-   JSON Resume import support via `from_json_resume()` converter (#39)
-   Embedded JSON Schema for resume validation at `shell/assets/static/schema.json`
-   New `core/importers` subpackage for external format converters
-   Comprehensive API documentation: `wiki/API-Reference.md`, `wiki/Shell-Layer-APIs.md`
-   API Stability Policy documentation at `wiki/API-Stability-Policy.md`
-   `get_schema_path()` helper for accessing bundled schema

### Changed

-   Extended `io_utils.candidate_yaml_path()` to recognize `.json` resume files
-   Updated `normalize_resume_name()` to handle JSON file extensions
-   Enhanced Getting Started and Usage Guide documentation

### Fixed

-   Path handling for JSON files now distinguishes between resume names and file paths

## [0.1.7] - 2026-01-01

### Changed

-   Converted layout measurement fields from string (`"7.8mm"`) to numeric float types (#37)
-   Updated `ResumeConfig` dataclass with float types for icon/section layout properties
-   Simplified template rendering by handling `mm` suffix at presentation layer
-   Enhanced CSS with sidebar entry styling improvements

### Fixed

-   Type consistency in `_build_resume_config()` for layout measurement defaults

## [0.1.6] - 2025-12-30

### Changed

-   Reorganized HTML templates into `html/` subdirectory (#18)
-   Narrowed exception handling in `validate_resume_config` for clearer error messages (#30)
-   Improved `RenderPlanConfig` type safety with `__post_init__` validation (#32)
-   Reconciled layout constants to A4 standard (210×297mm) (#35)
-   Centralized default values in `apply_config_defaults()` (#36)

### Fixed

-   Profile width arithmetic corrected (41mm → 45mm) (#33)
-   Added warning logging for palette generation fallback (#31)
-   Verified comprehensive test coverage for error paths (#34)

## [0.1.5] - 2025-12-29

### Changed

-   Relocated `plan.py` to `core/render/plan.py` for better module organization
-   Consolidated render plan logic within the render subpackage
-   Migrated inline CSS styles to external stylesheet architecture
-   Updated HTML template structure for cleaner separation of concerns

### Removed

-   Deleted standalone `core/plan.py` (functionality moved to `core/render/plan.py`)

## [0.1.4] - 2025-12-28

### Added

-   External CSS architecture with bundled theme presets (modern, classic, bold, minimal, executive)
-   ThemeLoader for dynamic theme configuration and merging
-   Dynamic font sizing plus spacing/icon layout configuration options
-   Strict mode for theme loading to fail fast instead of silent fallback
-   Path traversal protection in `load_theme()` using resolve/is_relative_to
-   Input validation for negative width in `dynamic_font_size()`
-   Comprehensive visual regression testing and documentation

### Changed

-   Refactored templates to use `<link>` tags instead of inline styles
-   Core HTML/PDF generation now requires injected template locator and LaTeX renderer
-   Improved EffectExecutor with dispatch pattern and CopyFile support
-   Expanded shell/runtime tests for layout controls

### Fixed

-   RuntimeError raised on empty/invalid PDF output instead of silent failure
-   GenerationResult size units corrected
-   Makefile Python version compatibility

### Breaking Changes

-   Core HTML/PDF generation requires an injected template locator and LaTeX renderer; implicit package defaults were removed

## [0.1.3] - 2025-12-03

### Added

-   Enhanced HTML template preview support
-   Content generation utilities for shell templates
-   Improved palette file handling and test coverage

### Fixed

-   Handle YAML files without trailing newlines

## [0.1.2] - 2025-12-02

### Added

-   Automated GitHub release workflow triggered by version tags.
-   Documentation for release workflow in README and wiki.

### Changed

-   Updated release automation to include changelog generation and artifact distribution.

## [0.1.1] - 2025-12-02

### Added

-   `simple_resume.core.colors` module with stable, documented color manipulation utilities.
-   MkDocs configuration for auto-generated API reference documentation.
-   `GenerateOptions` dataclass for simplified generation configuration.
-   Type annotations with `cast()` for lazy-loaded generation functions.
-   Comprehensive docstrings with `.. versionadded::` annotations.

### Changed

-   Standardized `generate()` function signature to use `GenerateOptions` consistently.
-   Enhanced README with improved Python quickstart examples.
-   Refactored architecture to strict Functional Core / Imperative Shell pattern.
-   Updated documentation links to point to new API reference.
-   Updated architecture documentation to reflect completion of core/generate/pdf.py refactor (Effect system eliminates weasyprint import violation).
-   Core layer now at 100% purity with zero known architectural violations.

### Fixed

-   Type mismatches between lazy and core generation function signatures.
-   `preview()` return type now correctly annotated as `GenerationResult | BatchGenerationResult`.
-   Packaging now bundles HTML templates and static assets to prevent `TemplateNotFound` errors in wheels and editable installs.
-   Eliminated weasyprint import from core layer via Effect system pattern.
-   Fixed WindowsPath instantiation errors on Linux CI runners.

## [0.1.0] - 2025-11-05

Initial public release.

### Added

-   Resume generation from YAML files with HTML/PDF output.
-   Generation API now returns detailed result objects.
-   Session management system for consistent configuration.
-   Support for remote and procedurally generated color palettes.
-   LaTeX rendering support.
-   Improved template resolution with a secondary lookup path.
-   Validation system with detailed error reporting.
-   CLI tool to demonstrate random palette generation.
-   Support for multi-page resumes with correct page breaking.
-   Automatic text color calculation for readability based on contrast.
-   FontAwesome icon integration.
-   Palette registry with support for Palettable, procedural HCL, and ColourLovers.
-   Consolidated CLI entry point: `simple-resume generate`.
-   Added demo files for features:
-   `sample_multipage_demo.yaml` - Multi-page resume with proper pagination
-   `sample_palette_demo.yaml` - Color scheme demonstrations
-   `sample_dark_sidebar.yaml` - Dark theme with sidebar layout
-   `sample_latex.yaml` - LaTeX-specific formatting examples
-   `sample_contrast_demo.yaml` - Color contrast accessibility examples
-   Added functional core-shell inventory and API surface design documentation.
-   Added new guides for color schemes, migration, and PDF renderer evaluation.
-   Added LaTeX support documentation to README.md with configuration examples and compilation instructions.
-   Improved Custom Styling section with LaTeX subsection and linking to the Usage Guide.

### Changed

-   Migrated to functional core, imperative shell architecture with a redesigned API surface (commit 0a0b231).
-   Improved ResumeSession with better caching, statistics tracking, and configuration handling.
-   Refactored Resume class with a pandas-like API and method chaining support.
-   Refined exception hierarchy with more detailed error reporting.
-   Fixed template handling issues and improved the secondary lookup path.
-   Refactored core architecture to be more modular.
-   Improved CLI user experience and error messages.
-   Optimized PDF generation.
-   Simplified configuration system with default template and format settings.

### Fixed

-   Fixed sidebar pagination issues and template lookup problems.
-   Corrected color contrast calculations and palette application.
-   Improved file path handling across different operating systems.
-   Improved configuration validation with better error messages.
-   Resolved LaTeX path handling issue to ensure sample resumes compile correctly with XeLaTeX and pdflatex.
-   Fixed several edge cases in template resolution and improved error reporting.
-   Corrected color contrast calculations to improve accessibility.
-   Resolved dependency injection issues in core components.

## [Unreleased]

---

### Release Process Notes

-   Update this file before tagging a release (move entries from **Unreleased** to new version section).
-   Include release date in ISO format (`YYYY-MM-DD`).
-   Reference GitHub pull requests or issues in brackets when available (e.g., `[#[issue]]`).
