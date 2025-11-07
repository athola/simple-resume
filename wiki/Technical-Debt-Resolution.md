# Technical Debt Resolution

**Date**: 2025-10-30
**Status**: Completed

This document summarizes how we resolved three technical debt items to improve maintainability and development speed.

---

## 1. WeasyPrint Renderer Evaluation

-   **Problem**: WeasyPrint's rendering quirks (e.g., z-index, limited CSS support) required workarounds and raised long-term maintenance concerns.
-   **Resolution**: We evaluated five alternative PDF renderers, documented in `PDF-Renderer-Evaluation.md`.
-   **Outcome**: We will continue with WeasyPrint for the next 12 months while preparing for a potential migration to Playwright. The evaluation includes a migration checklist and conditions for switching.

---

## 2. CSS Architecture Separation

-   **Problem**: PDF and HTML styles were tightly coupled within templates, hindering maintenance and iteration due to WeasyPrint's specific rendering behavior.
-   **Resolution**: We created a modular CSS architecture in `src/simple_resume/static/css/`.
-   **Outcome**: Shared styles (`common.css`), PDF-specific styles (`print.css`), and web preview styles (`preview.css`) are now separated. WeasyPrint workarounds are isolated in `print.css`. Templates will be updated to use these external files, as detailed in `src/simple_resume/static/css/README.md`.

### New Files

-   `src/simple_resume/static/css/common.css`
-   `src/simple_resume/static/css/print.css`
-   `src/simple_resume/static/css/preview.css`
-   `src/simple_resume/static/css/README.md`

---

## 3. Inline SVG Contrast Rules

-   **Problem**: Contact icons had inconsistent contrast, especially on dark sidebars, because WeasyPrint ignored `currentColor` on SVG child elements.
-   **Resolution**: We modified the icon macro to embed presentation attributes (`stroke="currentColor"`, `fill="none"`, `stroke-width="2"`, etc.) directly on each glyph. The parent `<svg>` now sets `color={{ sidebar_text_color }}`, ensuring icons inherit the correct color.
-   **Outcome**: Icons now render reliably in HTML previews and WeasyPrint PDFs, regardless of the color palette. New SVG icons should follow this inline attribute pattern.

---

## Validation

-   All 103 tests pass (including 7 new ones).
-   Code coverage is 95.34%.
-   No breaking changes were introduced.

## Next Steps

1.  **Q2 2025**: Build a Playwright proof-of-concept.
2.  **Q3 2025**: Decide on migration based on the PoC.
3.  **Annual Review**: Re-evaluate the PDF renderer landscape.

---
**Completed By**: Alex Thola
