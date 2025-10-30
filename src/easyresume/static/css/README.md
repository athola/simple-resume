# CV Stylesheet Architecture

This directory contains the modular stylesheets for the CV generator.

## File Structure

- **`common.css`**: Shared styles for both PDF and web previews.
- **`print.css`**: PDF-specific styles and WeasyPrint workarounds.
- **`preview.css`**: Web preview enhancements (e.g., hover effects, debug helpers).

## CSS Custom Properties

Theming is handled via CSS custom properties, which are injected by the template
engine from the YAML configuration. See the top of `common.css` for a list of
available variables.

## Implementation

Currently, styles are inlined in `cv_base.html` for compatibility with
WeasyPrint. The long-term goal is to link to these external stylesheets.

To do this, modify `cv_base.html` to conditionally load the appropriate CSS files:

```html
<head>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/common.css') }}">
  {% if not preview %}
  <link rel="stylesheet" href="{{ url_for('static', filename='css/print.css') }}">
  {% else %}
  <link rel="stylesheet" href="{{ url_for('static', filename='css/preview.css') }}">
  {% endif %}

  <style>
    :root {
      --theme-color: {{ cv_config["theme_color"] }};
      /* ... etc ... */
    }
  </style>
</head>
```

## WeasyPrint Workarounds

`print.css` contains workarounds for two main WeasyPrint issues:

1. **Z-index Bug**: A CSS gradient is used for the sidebar background instead of a
   `<div>` to prevent it from rendering on top of main content.
2. **Limited Flexbox Support**: Floats and absolute positioning are used for
   layout instead of flexbox.

When migrating to a new renderer, these workarounds should be the first thing to remove.

---
**Last Updated**: 2025-10-30
