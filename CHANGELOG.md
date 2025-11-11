# Changelog

This file documents all notable project changes. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-05

Initial public release.

### Added

-   Resume generation from YAML files with HTML/PDF output.
-   Generation API returns structured result objects with execution metadata.
-   Session management system for consistent configuration.
-   Support for remote and procedurally generated color palettes.
-   LaTeX rendering support.
-   Template resolution mechanism with secondary lookup path.
-   Validation system with detailed error reporting.
-   CLI tool to demonstrate random palette generation.
-   Support for multi-page resumes with correct page breaking.
-   Automatic text color calculation for readability based on contrast.
-   FontAwesome icon integration.
-   Palette registry with support for Palettable, procedural HCL, and ColourLovers.
-   Consolidated CLI entry point: `simple-resume generate`.
-   **New sample resumes**: Added comprehensive demo files showcasing features:
-   `sample_multipage_demo.yaml` - Multi-page resume with proper pagination
-   `sample_palette_demo.yaml` - Color scheme demonstrations
-   `sample_dark_sidebar.yaml` - Dark theme with sidebar layout
-   `sample_latex.yaml` - LaTeX-specific formatting examples
-   `sample_contrast_demo.yaml` - Color contrast accessibility examples
-   **Architecture documentation**: Added functional core-shell inventory and API surface design documentation.
-   **Enhanced wiki**: Added new guides for color schemes, migration, and PDF renderer evaluation.

### Changed

-   **Major architectural refactor**: Migrated to functional core, imperative shell architecture with redesigned API surface (commit 0a0b231)
-   **Enhanced session management**: Improved ResumeSession with better caching, statistics tracking, and configuration handling
-   **Core resume functionality**: Refactored Resume class with pandas-like API and method chaining support
-   **Improved error handling**: Enhanced exception hierarchy with more detailed error reporting
-   **Template resolution**: Fixed template handling issues and improved secondary lookup path mechanism
-   Refactored core architecture to be more modular.
-   Improved CLI user experience and error messages.
-   Optimized PDF generation.
-   Simplified configuration system with default template and format settings.

### Fixed

-   **Template resolution**: Fixed sidebar pagination issues and template lookup problems
-   **Color handling**: Corrected color contrast calculations and palette application
-   **Path resolution**: Improved file path handling across different operating systems
-   **Validation**: Enhanced configuration validation with better error messages
-   Resolved LaTeX path handling issue to ensure sample resumes compile correctly with XeLaTeX and pdflatex.
-   Fixed several edge cases in template resolution; improved error reporting.
-   Corrected color contrast calculations to improve accessibility.
-   Resolved dependency injection issues in core components.

## [Unreleased]

---

### Release Process Notes

-   Update this file before tagging a release (move entries from **Unreleased** to new version section).
-   Include release date in ISO format (`YYYY-MM-DD`).
-   Reference GitHub pull requests or issues in brackets when available (e.g., `[#[issue]]`).
