# Changelog

This file documents all notable changes to the project. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-05

Initial public release.

### Added

- YAML-driven resume generation with HTML and PDF outputs
- Unified generation API with rich result objects and metadata tracking
- Session management system for consistent configuration across operations
- Enhanced palette system with remote sources and procedural generation
- LaTeX rendering support for academic and research-focused resumes
- Advanced template resolution with fallback mechanisms
- Comprehensive validation system with detailed error reporting
- Random palette demo CLI tool for showcasing color scheme capabilities
- Multi-page resume support with proper page breaking
- Contrast-aware text color calculation for optimal readability
- FontAwesome icon integration for enhanced visual elements
- Palette registry (Palettable, procedural HCL, ColourLovers adapter)
- CLI entry point consolidated: use `simple-resume generate` for all formats

### Changed

- Refactored core architecture with modular design for better maintainability
- Improved error handling with structured exception hierarchy
- Enhanced CLI with better user experience and error messages
- Optimized PDF generation with improved performance and reliability
- Streamlined configuration system with sensible defaults

### Fixed

- Resolved LaTeX path handling so XeLaTeX/pdflatex compile sample resumes reliably
- Fixed template resolution edge cases and improved error reporting
- Corrected color contrast calculations for better accessibility
- Resolved dependency injection issues in core components

## [Unreleased]

---

### Release Process Notes

- Update this file before tagging a release (move entries from **Unreleased** to a new version section).
- Include the release date in ISO format (`YYYY-MM-DD`).
- Reference GitHub pull requests or issues in brackets when available (e.g., `[#[issue]]`).
