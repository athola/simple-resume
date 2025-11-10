# PDF Renderer Evaluation

This document evaluates alternatives to WeasyPrint for PDF generation. WeasyPrint, the current renderer, has rendering issues requiring CSS workarounds. This evaluation explores other options to determine migration benefits.

## Current State: WeasyPrint

-   **Version**: See `uv.lock`
-   **Usage**: Renders Jinja2 HTML templates to PDF.
-   **Integration**: Flask → HTML → WeasyPrint → PDF

### Known Issues

1.  **Z-index and Positioned Elements**: Overlapping positioned elements can render unpredictably (e.g., sidebar background on top of content). Current workaround: CSS gradient on page background.
2.  **CSS Support Gaps**: Incomplete Flexbox support; Grid layout unavailable.
3.  **Performance**: Single-page generation is acceptable (~1–2 seconds), but batch processing is not optimized.

### Advantages

-   Pure Python library with no external binary dependencies.
-   Good compliance with HTML and CSS standards.
-   Actively maintained.
-   Installable with `pip`.

## Evaluation Criteria

Each alternative evaluated based on these criteria:

-   **HTML/CSS Fidelity**: Accuracy in rendering existing templates.
-   **Python Integration**: Integration with Flask application.
-   **Maintenance**: Project actively maintained?
-   **Installation**: Installation difficulty.
-   **Performance**: Generates typical resume under 3 seconds?
-   **CSS Support**: Supports modern CSS (Flexbox, Grid)?
-   **Cost**: Free for open-source use?
-   **Migration Effort**: Effort required to migrate existing templates.

## Alternative Solutions

### 1. Playwright/Puppeteer

-   **Technology**: Headless Chromium browser automation.
-   **Pros**: Excellent rendering quality, CSS support.
-   **Cons**: Heavy dependency (~170MB Chromium binary download); slower performance (~2–3 seconds per resume).

### 2. ReportLab

-   **Technology**: Library for programmatically generating PDFs.
-   **Pros**: Excellent performance (<500ms); precise output control.
-   **Cons**: Does not render HTML, requiring complete template rewrite.

### 3. wkhtmltopdf

-   **Technology**: WebKit-based HTML-to-PDF converter.
-   **Pros**: Good CSS support; minimal migration effort.
-   **Cons**: Project archived in 2020; no longer maintained.

### 4. Prince XML

-   **Technology**: Commercial HTML-to-PDF converter.
-   **Pros**: Industry-leading rendering quality, CSS support.
-   **Cons**: Expensive for this use case ($3,800 per server license).

### 5. Stay with WeasyPrint

-   **Technology**: Continue with current implementation.
-   **Pros**: No migration effort; existing issues and workarounds understood.
-   **Cons**: Requires continued maintenance of workarounds.

## Comparison Matrix

| Criterion | Playwright | ReportLab | wkhtmltopdf | Prince | WeasyPrint |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Rendering Quality | 5/5 | 3/5 | 4/5 | 5/5 | 4/5 |
| CSS Support | 5/5 | N/A | 4/5 | 5/5 | 3/5 |
| Python Integration | 4/5 | 5/5 | 3/5 | 3/5 | 5/5 |
| Installation Ease | 2/5 | 5/5 | 2/5 | 3/5 | 5/5 |
| Performance | 3/5 | 5/5 | 4/5 | 5/5 | 3/5 |
| Migration Effort | 4/5 | 1/5 | 4/5 | 4/5 | 5/5 |
| **Final Score** | **4.2** | **3.8** | **3.5** | **4.2** | **4.2** |

*Scores out of 5. Final score is an average.*

## Recommendations

### Short-term (0–12 months)

**Stay with WeasyPrint.** Current implementation is stable, workarounds documented. This prioritizes new features over infrastructure changes.

### Long-term (12+ months)

**Migrate to Playwright.** Create a proof-of-concept to benchmark performance and document migration steps. Execute migration when resources are available.

### Triggers for Early Migration

Consider early migration if any of the following occur:

-   WeasyPrint no longer actively maintained.
-   Critical rendering bug blocks new feature.
-   Performance degrades to unacceptable level (e.g., >5 seconds per resume).

## Migration Checklist (Playwright)

### 1. Preparation

-   [ ] Install Playwright in development environment.
-   [ ] Create proof-of-concept for PDF generation.
-   [ ] Compare WeasyPrint and Playwright output quality.
-   [ ] Benchmark both renderers' performance on large number of resumes.
-   [ ] Add Playwright to `requirements.txt`; document installation process.

### 2. Implementation

-   [ ] Replace WeasyPrint calls with Playwright in PDF generation pipeline.
-   [ ] Update CSS for print media queries if necessary.
-   [ ] Add browser lifecycle management (launching/closing browser).
-   [ ] Add error handling, timeouts.
-   [ ] Update unit tests to mock Playwright.

### 3. Deployment

-   [ ] Deploy changes to staging environment; verify output.
-   [ ] Monitor performance metrics.
-   [ ] Deploy to production with rollback plan.
-   [ ] Keep WeasyPrint as backup renderer for one release cycle before removal.

### 4. Cleanup

-   [ ] Remove WeasyPrint-specific CSS workarounds.
-   [ ] Simplify and modernize CSS.
-   [ ] Update all related documentation.

---
**Document Version**: 1.1
**Last Updated**: 2025-10-30
