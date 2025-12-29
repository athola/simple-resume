# CSS Architecture for Simple Resume

This directory contains the external CSS files for the resume templates.

## File Structure

```text
static/css/
├── README.md      # This file
├── fonts.css      # @font-face declarations for Avenir fonts
├── common.css     # Shared styles for PDF and web preview
├── print.css      # PDF-specific styles and WeasyPrint workarounds
└── preview.css    # Web browser preview enhancements
```

## CSS Files

### fonts.css

Font-face declarations for the Avenir font family. Uses relative paths
to load fonts from `../fonts/`.

### common.css

All shared layout and component styles. Uses CSS custom properties
(variables) for theme customization. These variables must be injected
via an inline `<style>` block in the template.

### print.css

PDF/print-specific styles including `@page` rules and WeasyPrint
workarounds. Applied only for PDF generation.

### preview.css

Web browser enhancements for the preview mode. Adds shadows, smooth
scrolling, and responsive adjustments.

## CSS Custom Properties

The template must inject CSS custom properties for theme values.
Required properties:

```css
:root {
  /* Colors */
  --sidebar-color: #2c3e50;
  --sidebar-text-color: #ffffff;
  --theme-color: #3498db;
  --date2-color: #7f8c8d;
  --bar-background-color: #bdc3c7;
  --frame-color: #f5f5f5;
  --heading-icon-color: #ffffff;
  --section-icon-color: #2c3e50;
  --section-header-color: #2c3e50;

  /* Dimensions (use mm for print compatibility) */
  --page-width: 210mm;
  --page-height: 297mm;
  --sidebar-width: 60mm;
  --body-width: 150mm;
  --padding: 5mm;

  /* Layout spacing */
  --sidebar-padding-top: 5mm;
  --sidebar-padding-bottom: 5mm;
  --sidebar-padding-left: 5mm;
  --sidebar-padding-right: 5mm;
  --pitch-padding-top: 10mm;
  --pitch-padding-bottom: 5mm;
  --pitch-padding-left: 5mm;
  --h2-padding-left-full: 25mm;
  --h2-width: 140mm;
  --h3-padding-top: 3mm;
  --date-container-width: 25mm;
  --description-container-padding-left: 5mm;
  --skill-container-padding-top: 2mm;
  --profile-image-padding-bottom: 5mm;
  --profile-width: 50mm;
  --frame-padding: 10mm;

  /* Section icon styling */
  --section-icon-circle-size: 10mm;
  --section-icon-circle-x-offset: 0mm;
  --section-icon-design-size: 5mm;
  --section-icon-design-x-offset: 0;
  --section-icon-design-y-offset: 0;
  --section-heading-text-margin: 5mm;
  --section-heading-marker-margin-left: -10mm;
  --section-heading-marker-line-height: 15mm;
}
```

## Usage in Templates

### Loading CSS Files

From templates in `templates/html/`:

```html
<head>
  <!-- Load external CSS -->
  <link rel="stylesheet" href="../static/css/fonts.css">
  <link rel="stylesheet" href="../static/css/common.css">

  <!-- Print styles (for PDF) -->
  <link rel="stylesheet" href="../static/css/print.css">

  <!-- Preview styles (browser only) -->
  {% if preview %}
  <link rel="stylesheet" href="../static/css/preview.css">
  {% endif %}

  <!-- Inject CSS custom properties from YAML config -->
  <style>
    :root {
      --sidebar-color: {{ resume_config["sidebar_color"] }};
      --theme-color: {{ resume_config["theme_color"] }};
      /* ... other properties ... */
    }
  </style>
</head>
```

### Path Resolution

CSS files use relative paths. From `static/css/`:

- Fonts: `../fonts/AvenirLTStd-Light.otf`
- Images: `../images/...`

Templates link to CSS from `templates/html/`:

- CSS: `../static/css/common.css`

WeasyPrint's `base_url` is set to the templates directory, so all
relative paths resolve from there.

## Migration Status

### Phase 1: External CSS with Fallback (Complete)

- [x] CSS files created and documented
- [x] CSS custom properties defined
- [x] Templates updated to use external CSS (`<link>` tags added)
- [x] Font paths fixed in templates (`../static/fonts/`)
- [x] All 1014 tests passing
- [x] Font embedding verified (Avenir fonts in PDFs)

### Phase 2: Visual Regression Testing (Complete)

- [x] All 8 sample PDFs generated successfully
- [x] Fonts properly embedded in all PDFs (verified with `pdffonts`):
  - Avenir-35-Light
  - Avenir-45
  - Avenir-55-Medium
  - Avenir-65-Bold
  - Avenir-35-Light-Oblique
- [x] Layout renders correctly across all samples
- [x] Dark sidebar theme verified
- [x] Multipage layouts verified
- [x] Palette variations verified

### Phase 3: Remove Inline Styles (Complete)

- [x] Remove inline fallback styles from `resume_base.html`
- [x] Remove inline fallback font styles from `cover.html`
- [x] Final visual regression testing (all 8 PDFs generated, fonts verified)
- [x] All 1014 tests passing
- [x] Documentation updated

**Note:** `cover.html` retains cover-specific inline styles that use `resume_config`
variables (e.g., `cover_padding_top`). These are not duplicates of external CSS
but template-specific styles that require Jinja variable injection.

## Testing

After making changes:

1. Generate PDF: `uv run simple-resume generate --format pdf`
2. Compare output visually with previous version
3. Check fonts are embedded: `pdffonts output.pdf`
4. Run test suite: `uv run pytest`

## WeasyPrint Notes

WeasyPrint has some CSS limitations:

- `calc()` with CSS variables may not work in all contexts
- Some flexbox edge cases render differently
- Font loading requires proper path resolution via `base_url`

The styles in this directory have been tested with WeasyPrint.

## Theme Presets

For ready-to-use theme configurations, see the **[Theme Gallery](../themes/README.md)**:

| Theme | Description |
|-------|-------------|
| `modern.yaml` | Clean, contemporary design |
| `classic.yaml` | Traditional professional look |
| `bold.yaml` | High-contrast, vibrant colors |
| `minimal.yaml` | Light and airy |
| `executive.yaml` | Sophisticated dark with gold |

Each theme provides a complete `config:` block you can copy into your resume YAML.

## Related Documentation

- [Theme Gallery](../themes/README.md) - Pre-built themes and customization guide
- [Path Handling Guide](../../../../wiki/Path-Handling-Guide.md)
- [PDF Renderer Evaluation](../../../../wiki/PDF-Renderer-Evaluation.md)
