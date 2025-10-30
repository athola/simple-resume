# Color Scheme Guide

Customize CV colors by defining them in your YAML `config` section.

## Color Properties

```yaml
config:
  theme_color: "#0395DE"          # Headings, icons, and accents
  sidebar_color: "#F6F6F6"        # Sidebar background
  bar_background_color: "#DFDFDF"  # Progress bar background (in `cv_with_bars` template)
  date2_color: "#616161"          # Secondary date text
  frame_color: "#757575"          # Preview frame (web preview only)
```

## Preset Schemes

Copy a preset into your YAML `config` section.

### Professional Blue (Default)
High-contrast blue for on-screen and print readability.

```yaml
config:
  theme_color: "#0395DE"
  sidebar_color: "#F6F6F6"
  bar_background_color: "#DFDFDF"
  date2_color: "#616161"
  frame_color: "#757575"
```

### Creative Purple
Saturated purple, best for screen viewing.

```yaml
config:
  theme_color: "#7B3FF2"
  sidebar_color: "#F5F3FF"
  bar_background_color: "#E9D5FF"
  date2_color: "#6B21A8"
  frame_color: "#9333EA"
```

### Minimal Dark
Charcoal and neutral grays for reliable printing.

```yaml
config:
  theme_color: "#1F2937"
  sidebar_color: "#F9FAFB"
  bar_background_color: "#E5E7EB"
  date2_color: "#6B7280"
  frame_color: "#374151"
```

### Energetic Orange
High-saturation orange. May lose detail on lower-quality paper.

```yaml
config:
  theme_color: "#EA580C"
  sidebar_color: "#FFF7ED"
  bar_background_color: "#FFEDD5"
  date2_color: "#9A3412"
  frame_color: "#C2410C"
```

### Modern Teal
Medium saturation teal with good screen-to-print consistency.

```yaml
config:
  theme_color: "#0891B2"
  sidebar_color: "#F0FDFA"
  bar_background_color: "#CCFBF1"
  date2_color: "#134E4A"
  frame_color: "#0E7490"
```

### Classic Green
WCAG AA compliant green for text on white backgrounds.

```yaml
config:
  theme_color: "#059669"
  sidebar_color: "#F0FDF4"
  bar_background_color: "#D1FAE5"
  date2_color: "#065F46"
  frame_color: "#047857"
```

## Guidelines

### Color Format
All colors must be quoted hexadecimal strings with a leading `#`.

-   `"#0395DE"` (Correct)
-   `"#000"` (Short form is valid)
-   `"0395DE"` (Invalid: missing `#`)
-   `"rgb(3, 149, 222)"` (Invalid: RGB not supported)
-   `"blue"` (Invalid: named colors not supported)

### Testing
1.  **Web Preview**: Run `uv run python src/easyresume/index.py` and open `http://localhost:5000/`.
2.  **PDF Generation**: Run `uv run python src/easyresume/generate_pdf.py`.
3.  **Print Test**: Print a sample page to check paper output.

## Template-Specific Colors
-   **`cv_no_bars`**: Uses `theme_color`, `sidebar_color`, and `date2_color`.
-   **`cv_with_bars`**: Uses all colors. `bar_background_color` sets the empty portion of skill bars.
-   **`frame_color`**: Only used in the web preview border.

## Creating Custom Schemes
Start with a `theme_color`. Choose a neutral `sidebar_color`. Derive other colors from the primary, such as a desaturated `bar_background` or a darker `date2_color`. Tools like [Coolors.co](https://coolors.co) or [Adobe Color](https://color.adobe.com) can help build a palette.

## Troubleshooting
-   **Colors not appearing**: Ensure values are quoted strings with a leading `#`.
-   **Poor readability**: Check contrast between text and background colors.
-   **PDF color differences**: Colors can render differently in PDFs. Always generate a test PDF.
