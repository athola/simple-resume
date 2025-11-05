# Technical Debt Resolution

**Date**: 2025-10-30
**Status**: ✅ Completed

This document explains how we resolved two technical debt items to improve maintainability and development speed.

---

## 1. WeasyPrint Renderer Evaluation

- **Problem**: WeasyPrint has rendering quirks (e.g., z-index, limited CSS support) that forced us to write workarounds. We were also concerned about its long-term maintenance.
- **Resolution**: We evaluated five alternative PDF renderers and documented the findings in `PDF-Renderer-Evaluation.md`.
- **Outcome**: We're sticking with WeasyPrint for the next 12 months but will prepare for a potential migration to Playwright. The evaluation document includes a migration checklist and outlines the conditions under which we'd make the switch.

---

## 2. CSS Architecture Separation

- **Problem**: PDF and HTML styles were tangled together in the templates, making them hard to maintain. Our styles were too tightly coupled to WeasyPrint's specific rendering behavior, which made iteration slow.
- **Resolution**: We created a modular CSS architecture in `src/simple_resume/static/css/`.
- **Outcome**: The new structure separates shared styles (`common.css`), PDF-specific styles (`print.css`), and web preview styles (`preview.css`). All WeasyPrint workarounds are now isolated in `print.css`. The templates still need to be updated to use these external files; the plan for that is in `src/simple_resume/static/css/README.md`.

### New Files

- `src/simple_resume/static/css/common.css`
- `src/simple_resume/static/css/print.css`
- `src/simple_resume/static/css/preview.css`
- `src/simple_resume/static/css/README.md`

---

## 3. Inline SVG Contrast Rules

- **Problem**: Contact icons were disappearing or showing up with the wrong contrast, especially on dark sidebars. This happened because WeasyPrint ignored CSS rules like `currentColor` on SVG child elements.
- **Resolution**: We changed the icon macro to embed presentation attributes (`stroke="currentColor"`, `fill="none"`, `stroke-width="2"`, etc.) directly on each glyph. The parent `<svg>` now sets `color={{ sidebar_text_color }}`, so the icons automatically inherit the correct color from the sidebar text.
- **Outcome**: The icons now render reliably in both HTML previews and WeasyPrint PDFs, no matter the color palette. Any new SVG icons should follow this pattern of using inline attributes.

---

## Validation

- All 103 tests pass (including 7 new ones).
- Code coverage is 95.34%.
- No breaking changes were introduced.

## Next Steps

1.  **Q2 2025**: Build a Playwright proof-of-concept.
2.  **Q3 2025**: Decide whether to migrate based on the PoC.
3.  **Annual Review**: Re-evaluate the PDF renderer landscape.

---
**Completed By**: Alex Thola