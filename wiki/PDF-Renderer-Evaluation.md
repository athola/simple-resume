# PDF Renderer Evaluation

This document evaluates alternatives to WeasyPrint for PDF generation. WeasyPrint is our current PDF renderer, but it has some rendering quirks that require workarounds. This evaluation explores other options to see if a migration makes sense.

## Current State: WeasyPrint

-   **Version**: See `requirements.txt`
-   **Usage**: Renders Jinja2 HTML templates to PDF.
-   **Integration**: Flask → HTML → WeasyPrint → PDF

### Known Issues

1.  **Z-index and Positioned Elements**: Overlapping positioned elements can render unpredictably. For example, the sidebar background sometimes renders on top of the content. Our current workaround is a CSS gradient on the page background.
2.  **CSS Support Gaps**: Flexbox support is incomplete, and Grid layout is not available.
3.  **Performance**: While single-page generation is acceptable (~1–2s), batch processing is not optimized.

### Strengths

-   Pure Python, so no external binary dependencies.
-   Good (but not perfect) HTML/CSS standards compliance.
-   Actively maintained.
-   Simple `pip` installation.

## Evaluation Criteria

We evaluated each alternative based on the following criteria:

-   **HTML/CSS Fidelity**: How accurately does it render our existing templates?
-   **Python Integration**: How well does it integrate with a Flask application?
-   **Maintenance**: Is the project actively maintained?
-   **Installation**: How easy is it to install?
-   **Performance**: Can it generate a typical resume in under 3 seconds?
-   **CSS Support**: Does it support modern CSS features like flexbox and grid?
-   **Cost**: Is it free for open-source use?
-   **Migration Effort**: How much work would it be to migrate our existing templates?

## Alternative Solutions

### 1. Playwright/Puppeteer

-   **Technology**: Headless Chromium browser automation.
-   **Pros**: Excellent rendering quality and CSS support (it's Chromium).
-   **Cons**: Heavy dependency (downloads a ~170MB Chromium binary) and slower performance (~2–3s per resume).
-   **Recommendation**: **8.5/10**. The best rendering quality, but the heavy dependency is a significant drawback.

### 2. ReportLab

-   **Technology**: Programmatic PDF generation library.
-   **Pros**: Excellent performance (<500ms) and precise control.
-   **Cons**: No HTML rendering, which would require a complete rewrite of all our templates.
-   **Recommendation**: **3/10**. A great library, but the migration cost is too high.

### 3. wkhtmltopdf

-   **Technology**: WebKit-based HTML-to-PDF converter.
-   **Pros**: Good CSS support and minimal migration effort.
-   **Cons**: The project was archived in 2020 and is no longer maintained.
-   **Recommendation**: **2/10**. We can't rely on deprecated software.

### 4. Prince XML

-   **Technology**: Commercial HTML-to-PDF converter.
-   **Pros**: Industry-leading rendering quality and CSS support.
-   **Cons**: Prohibitively expensive for our use case ($3,800/server license).
-   **Recommendation**: **4/10**. Excellent quality, but not a viable option due to cost.

### 5. Stay with WeasyPrint

-   **Technology**: Continue with our current implementation.
-   **Pros**: No migration effort required, and the existing issues and workarounds are well understood.
-   **Cons**: We'll have to continue maintaining our workarounds.
-   **Recommendation**: **7/10**. The most pragmatic choice for now.

## Comparison Matrix

| Criterion          | Playwright | ReportLab | wkhtmltopdf | Prince    | WeasyPrint |
| ------------------ | ---------- | --------- | ----------- | --------- | ---------- |
| Rendering Quality  | ⭐⭐⭐⭐⭐   | ⭐⭐⭐      | ⭐⭐⭐⭐     | ⭐⭐⭐⭐⭐  | ⭐⭐⭐⭐    |
| CSS Support        | ⭐⭐⭐⭐⭐   | N/A       | ⭐⭐⭐⭐     | ⭐⭐⭐⭐⭐  | ⭐⭐⭐      |
| Python Integration | ⭐⭐⭐⭐    | ⭐⭐⭐⭐⭐  | ⭐⭐⭐      | ⭐⭐⭐    | ⭐⭐⭐⭐⭐   |
| Installation Ease  | ⭐⭐        | ⭐⭐⭐⭐⭐  | ⭐⭐         | ⭐⭐⭐    | ⭐⭐⭐⭐⭐   |
| Performance        | ⭐⭐⭐      | ⭐⭐⭐⭐⭐  | ⭐⭐⭐⭐     | ⭐⭐⭐⭐⭐  | ⭐⭐⭐      |
| Migration Effort   | ⭐⭐⭐⭐    | ⭐          | ⭐⭐⭐⭐     | ⭐⭐⭐⭐   | ⭐⭐⭐⭐⭐   |
| **Final Score**    | **8.5**    | **3.0**   | **2.0**     | **4.0**   | **7.0**    |

## Recommendations

### Short-term (0–12 months)

**Stay with WeasyPrint.** The current implementation is stable, and the workarounds are documented. This lets us focus on features instead of infrastructure.

### Long-term (12+ months)

**Migrate to Playwright.** We should create a proof-of-concept to benchmark performance and document the migration steps, then execute the migration when we have the bandwidth.

### When to Migrate Sooner

We should consider migrating sooner if:

-   WeasyPrint is no longer maintained.
-   A critical rendering bug blocks a new feature.
-   Performance degrades to more than 5 seconds per resume.

## Migration Checklist (Playwright)

### 1. Preparation

-   [ ] Install Playwright in a development environment.
-   [ ] Create a proof-of-concept for PDF generation.
-   [ ] Compare WeasyPrint and Playwright output quality.
-   [ ] Benchmark performance on a large number of resumes.
-   [ ] Add Playwright to `requirements.txt` and document the installation process.

### 2. Implementation

-   [ ] Replace WeasyPrint calls with Playwright in the PDF generation pipeline.
-   [ ] Update CSS for print media queries if needed.
-   [ ] Add browser lifecycle management (launching and closing the browser).
-   [ ] Add error handling and timeouts.
-   [ ] Update unit tests to mock Playwright.

### 3. Deployment

-   [ ] Deploy to a staging environment and verify the output.
-   [ ] Monitor performance metrics.
-   [ ] Deploy to production with a rollback plan.
-   [ ] Keep WeasyPrint as a backup option for one release cycle before removing it.

### 4. Cleanup

-   [ ] Remove WeasyPrint-specific workarounds.
-   [ ] Simplify and modernize the CSS.
-   [ ] Update all related documentation.

---
**Document Version**: 1.1
**Last Updated**: 2025-10-30
