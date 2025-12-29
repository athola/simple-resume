# Changelog

This file documents all notable project changes. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
