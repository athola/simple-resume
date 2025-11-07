# ADR 001: Fix WeasyPrint Sidebar Content Pagination

## Status

Accepted

## Context

Simple-Resume generates PDF resumes from HTML templates using WeasyPrint. A critical
issue was identified where sidebar content was not flowing properly across multiple
pages. Specifically:

- Sidebar content would stop abruptly after the "Languages/English" section
- Expertise, Programming, and Key Skills sections were not appearing on pages 2 and 3
- The issue occurred with multi-page resumes using the `resume_with_bars.html` template

## Problem Statement

The root cause was identified as a CSS positioning issue with WeasyPrint's page break
handling:

1. **`position: absolute; top: 0`** restarts positioning on each new page in
   WeasyPrint
2. WeasyPrint treats each page as a separate canvas, not as continuous flow like
   browsers
3. Sidebar content that should continue from page 1 gets "cut off" because it tries
   to render at the same absolute coordinates on subsequent pages
4. The content exists in HTML but becomes invisible in PDF output

## Decision

Implement a hybrid CSS layout solution that enables sidebar content to flow naturally
across pages while maintaining the original visual layout.

## Solution

### Key Changes Made

#### 1. Sidebar Container Positioning

**Before:**

```css
.sidebar-container {
  position: absolute;
  left: 0;
  top: 0;
  width: 58mm;
  margin: 0;
  padding: 0;
  max-height: none;
  overflow: visible;
  background-color: transparent;
}
```

**After:**

```css
.sidebar-container {
  position: relative;
  float: left;
  width: 58mm;
  margin: 0;
  padding: 0;
  /* Allow content to flow across pages */
  page-break-inside: auto;
  break-inside: auto;
}
```

#### 2. Page Background

**Before:** Individual sidebar background color

**After:** Linear gradient on the page to ensure consistent background

```css
.page {
  background: linear-gradient(
    to right,
    #F4F6FD 0,
    #F4F6FD 58mm,
    white 58mm,
    white 100%
  );
  background-repeat: no-repeat;
  background-size: 100% 100%;
  /* Clear floats to prevent layout issues */
  overflow: hidden;
}
```

#### 3. Sidebar Text Visibility

```css
.sidebar {
  position: relative;
  z-index: 10;
}
```

### Core Technical Insight

The breakthrough was understanding that:

- **`position: relative` + `float: left`** allows content to flow naturally across
  pages in WeasyPrint
- **`position: absolute` + `top: 0`** restarts positioning on each page, cutting off content flow
- **Linear gradient background** provides consistent visual background across all pages
- **`z-index`** ensures text remains visible above the background

## Result

### Before Fix

- ❌ Sidebar content stopped after "Languages/English" on page 1
- ❌ Expertise, Programming, Key Skills missing from pages 2-3
- ❌ 3 pages total but incomplete sidebar content

### After Fix

- ✅ Sidebar content flows naturally across all pages
- ✅ Expertise appears on page 2
- ✅ Programming and Key Skills appear on page 3
- ✅ Consistent background color across all pages
- ✅ Text remains visible with proper contrast
- ✅ Maintains original 3-page layout structure

## Alternatives Considered

### 1. CSS Regions Approach

- **Pros:** Native CSS solution for content flow
- **Cons:** Limited WeasyPrint support, complex implementation
- **Status:** Attempted but not fully supported

### 2. Dynamic Template Generation

- **Pros:** Complete control over content placement
- **Cons:** Complex Python logic, harder to maintain
- **Status:** Considered as fallback option

### 3. Column-based Layout

- **Pros:** Natural content flow
- **Cons:** Significant layout changes, compatibility issues
- **Status:** Tested but caused additional problems

## Decision Rationale

The selected solution was chosen because:

1. **Minimal Code Changes**: Requires only CSS modifications
2. **Maintains Compatibility**: Preserves existing template structure
3. **WeasyPrint Native**: Uses CSS features fully supported by WeasyPrint
4. **Backward Compatible**: Doesn't break existing single-page resumes
5. **Maintainable**: Clear, understandable CSS changes

## Consequences

### Positive

- ✅ Fixes critical multi-page resume functionality
- ✅ Maintains backward compatibility
- ✅ Improves overall user experience for multi-page resumes
- ✅ Documented solution for future WeasyPrint issues

### Negative

- ⚠️ Uses `float: left` which requires careful layout management
- ⚠️ Removes the original `position: absolute` sidebar approach
- ⚠️ Requires `overflow: hidden` on page container

### Neutral

- 🔄 Changes CSS layout approach but maintains visual output
- 🔄 Requires understanding of WeasyPrint pagination behavior

## Implementation Details

### Files Modified

- `src/simple_resume/templates/resume_base.html` - Core CSS layout changes

### Key CSS Properties

- `position: relative` instead of `position: absolute`
- `float: left` for natural content flow
- `page-break-inside: auto` for pagination support
- `z-index: 10` for text visibility
- Linear gradient backgrounds for consistent visuals

### Testing

- ✅ `sample_multipage_demo.yaml` - Multi-page resume with full sidebar
- ✅ `sample_1.yaml` - Single-page resume compatibility
- ✅ Generated both PDF and HTML outputs for validation

## References

- WeasyPrint CSS Paged Media Specification
- CSS Float Layout and Pagination Behavior
- WeasyPrint GitHub Issues on Position Absolute Elements

## Future Considerations

1. Monitor WeasyPrint updates for improved CSS regions support
2. Consider dynamic content processing for very complex multi-page layouts
3. Document this pattern for other WeasyPrint pagination issues
