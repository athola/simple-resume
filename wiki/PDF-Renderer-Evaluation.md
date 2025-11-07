# PDF Renderer Evaluation

This document evaluates alternatives to WeasyPrint for PDF generation. WeasyPrint is
our current renderer, but it has rendering quirks that require workarounds. This
evaluation explores other options to determine if a migration is beneficial.

## Current State: WeasyPrint

-   **Version**: See `requirements.txt`
-   **Usage**: Renders Jinja2 HTML templates to PDF.
-   **Integration**: Flask → HTML → WeasyPrint → PDF

### Issues

1.  **Z-index and Positioned Elements**: Overlapping positioned elements can render unpredictably. For example, the sidebar background sometimes renders on top of the content. Our current workaround uses a CSS gradient on the page background.
2.  **CSS Support Gaps**: Incomplete Flexbox support; Grid layout is unavailable.
3.  **Performance**: Single-page generation is acceptable (~1–2s), but batch processing is not optimized.

### Advantages

-   Pure Python; no external binary dependencies.
-   Good HTML/CSS standards compliance.
-   Actively maintained.
-   Simple `pip` installation.

## Evaluation Criteria

We evaluated each alternative based on these criteria:

-   **HTML/CSS Fidelity**: How accurately does it render existing templates?
-   **Python Integration**: How well does it integrate with a Flask application?
-   **Maintenance**: Is the project actively maintained?
-   **Installation**: How easy is it to install?
-   **Performance**: Can it generate a typical resume in under 3 seconds?
-   **CSS Support**: Does it support modern CSS features like Flexbox and Grid?
-   **Cost**: Is it free for open-source use?
-   **Migration Effort**: How much work to migrate existing templates?

## Alternative Solutions

### 1. Playwright/Puppeteer

-   **Technology**: Headless Chromium browser automation.
-   **Pros**: Excellent rendering quality and CSS support (it's Chromium).
-   **Cons**: Heavy dependency (~170MB Chromium binary download) and slower performance (~2–3s per resume).

### 2. ReportLab

-   **Technology**: Programmatic PDF generation library.
-   **Pros**: Excellent performance (<500ms) and precise control.
-   **Cons**: No HTML rendering; requires a complete rewrite of all templates.

### 3. wkhtmltopdf

-   **Technology**: WebKit-based HTML-to-PDF converter.
-   **Pros**: Good CSS support and minimal migration effort.
-   **Cons**: Project archived in 2020 and no longer maintained.

### 4. Prince XML

-   **Technology**: Commercial HTML-to-PDF converter.
-   **Pros**: Industry-leading rendering quality and CSS support.
-   **Cons**: Expensive for our use case ($3,800/server license).

### 5. Stay with WeasyPrint

-   **Technology**: Continue with current implementation.
-   **Pros**: No migration effort; existing issues and workarounds are understood.
-   **Cons**: Requires continued maintenance of workarounds.

## Comparison Matrix

| Criterion          | Playwright | ReportLab | wkhtmltopdf | Prince    | WeasyPrint |\
| ------------------ | ---------- | --------- | ----------- | --------- | ---------- |\
| Rendering Quality  | ⭐⭐⭐⭐⭐   | ⭐⭐⭐      | ⭐⭐⭐⭐     | ⭐⭐⭐⭐⭐  | ⭐⭐⭐⭐    |\
| CSS Support        | ⭐⭐⭐⭐⭐   | N/A       | ⭐⭐⭐⭐     | ⭐⭐⭐⭐⭐  | ⭐⭐⭐      |\
| Python Integration | ⭐⭐⭐⭐    | ⭐⭐⭐⭐⭐  | ⭐⭐⭐      | ⭐⭐⭐    | ⭐⭐⭐⭐⭐   |\
| Installation Ease  | ⭐⭐        | ⭐⭐⭐⭐⭐  | ⭐⭐         | ⭐⭐⭐    | ⭐⭐⭐⭐⭐   |\
| Performance        | ⭐⭐⭐      | ⭐⭐⭐⭐⭐  | ⭐⭐⭐⭐     | ⭐⭐⭐⭐⭐  | ⭐⭐⭐      |\
| Migration Effort   | ⭐⭐⭐⭐    | ⭐          | ⭐⭐⭐⭐     | ⭐⭐⭐⭐   | ⭐⭐⭐⭐⭐   |\
| **Final Score**    | **8.5**    | **3.0**   | **2.0**     | **4.0**   | **7.0**    |\

## Recommendations

### Short-term (0–12 months)

**Stay with WeasyPrint.** The current implementation is stable, and workarounds are documented. This allows us to prioritize features over infrastructure changes.

### Long-term (12+ months)

**Migrate to Playwright.** We should create a proof-of-concept to benchmark performance and document migration steps, then execute the migration when resources allow.

### Consider migrating sooner if needed

-   WeasyPrint is no longer maintained.
-   A critical rendering bug blocks a new feature.
-   Performance degrades to over 5 seconds per resume.

## Migration Checklist (Playwright)

### 1. Preparation

-   [ ] Install Playwright in a development environment.
-   [ ] Create a proof-of-concept for PDF generation.
-   [ ] Compare WeasyPrint and Playwright output quality.
-   [ ] Benchmark performance on a large number of resumes.
-   [ ] Add Playwright to `requirements.txt` and document installation.

### 2. Implementation

-   [ ] Replace WeasyPrint calls with Playwright in the PDF generation pipeline.
-   [ ] Update CSS for print media queries if needed.
-   [ ] Add browser lifecycle management (launching and closing).
-   [ ] Add error handling and timeouts.
-   [ ] Update unit tests to mock Playwright.

### 3. Deployment

-   [ ] Deploy to a staging environment and verify output.
-   [ ] Monitor performance metrics.
-   [ ] Deploy to production with a rollback plan.
-   [ ] Keep WeasyPrint as a backup for one release cycle before removal.

### 4. Cleanup

-   [ ] Remove WeasyPrint-specific workarounds.
-   [ ] Simplify and modernize the CSS.
-   [ ] Update all related documentation.

---
**Document Version**: 1.1
**Last Updated**: 2025-10-30
