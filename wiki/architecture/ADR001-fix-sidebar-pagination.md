# ADR 001: WeasyPrint Sidebar Content Pagination Fix

## Status

Accepted

## Context

Multi-page resume PDF generation had a sidebar content pagination issue with WeasyPrint. Sidebar content was cut off after the first page, observed in `resume_with_bars.html` template where sections like "Expertise" and "Programming" were missing from subsequent pages.

## Problem Statement

Root cause: CSS positioning conflict with WeasyPrint's page break behavior. WeasyPrint treats each page as a separate canvas; `position: absolute; top: 0;` on the sidebar rendered content at the same absolute coordinates on every page, losing content that should have flowed to subsequent pages.

## Decision

Decision: Implement a CSS-only solution for sidebar content to flow across pages while preserving original visual layout. This approach combines `position: relative`, `float: left`, and a linear gradient background.

## Solution

### Key Changes

#### 1. Sidebar Container Positioning

Sidebar container changed from `position: absolute` to `position: relative` with `float: left`. This allows content to reflow correctly on page breaks.

**Before:**

```css
.sidebar-container {
  position: absolute;
  left: 0;
  top: 0;
  width: 58mm;
  /* ... */
}
```

**After:**

```css
.sidebar-container {
  position: relative;
  float: left;
  width: 58mm;
  page-break-inside: auto;
  break-inside: auto;
  /* ... */
}
```

#### 2. Page Background

Instead of sidebar background color, a `linear-gradient` was applied to the page background, ensuring consistent sidebar background color across all pages.

```css
.page {
  background: linear-gradient(
    to right,
    #F4F6FD 0,
    #F4F6FD 58mm,
    white 58mm,
    white 100%
  );
  /* ... */
  overflow: hidden; /* Clear floats */
}
```

#### 3. Sidebar Text Visibility

A `z-index` added to the sidebar ensures its content appears above the new page background.

```css
.sidebar {
  position: relative;
  z-index: 10;
}
```

### Technical Summary

-   `position: relative` and `float: left` enable content flow across WeasyPrint pages.
-   A `linear-gradient` on the page background provides consistent visual appearance.
-   `z-index` ensures sidebar text renders above background.

## Result

Sidebar content now flows correctly across all pages of multi-page resumes. Visual layout is preserved, and background color is consistent.

## Alternatives Considered

### 1. CSS Regions

-   **Description:** Native CSS solution for content flow.
-   **Outcome:** Attempted, but not adopted due to limited WeasyPrint support.

### 2. Dynamic Template Generation

-   **Description:** Use Python to split and place content.
-   **Outcome:** Considered, but rejected due to increased complexity.

### 3. Column-based Layout

-   **Description:** Use CSS columns for content flow.
-   **Outcome:** Tested, but introduced other layout problems.

## Decision Rationale

The chosen solution was selected for the following reasons:

1.  **Minimal Code Changes**: Only required CSS modifications.
2.  **Compatibility**: Preserved existing template structure.
3.  **WeasyPrint Native**: Uses well-supported CSS features by WeasyPrint.
4.  **Maintainability**: The CSS changes are straightforward.

## Consequences

### Positive

-   Fixes critical bug in multi-page resume generation.
-   Maintains backward compatibility with single-page resumes.
-   Solution documented for future reference.

### Negative

-   Use of `float: left` requires careful layout management to avoid float clearing issues.
-   `overflow: hidden` property on page container now required.

### Neutral

-   Underlying CSS layout approach changed, but visual output is the same.
-   Solution requires understanding WeasyPrint's specific pagination behavior.

## Implementation Details

### Files Modified

-   `src/simple_resume/templates/resume_base.html`

### Key CSS Properties

-   `position: relative`
-   `float: left`
-   `page-break-inside: auto`
-   `z-index: 10`
-   `background: linear-gradient(...)`

### Testing

Fix validated using these test cases:

-   `sample_multipage_demo.yaml`: Multi-page resume with full sidebar.
-   `sample_1.yaml`: Single-page resume to ensure no regressions.
-   Both PDF and HTML outputs generated and visually inspected.

## References

-   WeasyPrint CSS Paged Media Specification
-   CSS Float Layout and Pagination Behavior
-   WeasyPrint GitHub Issues on Position Absolute Elements

## Future Considerations

-   Monitor WeasyPrint updates for improved CSS Regions support.
-   Consider dynamic content processing if more complex multi-page layouts are needed.
-   Document this solution as a pattern for other WeasyPrint pagination issues.
