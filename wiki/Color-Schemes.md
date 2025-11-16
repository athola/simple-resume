# Color Scheme Guide

This guide explains how to customize the colors of your resume using preset color schemes, custom colors, or palette files.

## Color Properties

The following color properties can be set in the `config` section of the YAML file. All colors must be specified as quoted hexadecimal strings (e.g., `"#0395DE"`).

-   `theme_color`: The primary color for headings and accents.
-   `sidebar_color`: The background color of the sidebar.
-   `sidebar_text_color`: The text color of the sidebar. If not provided, it is automatically calculated from the `sidebar_color` for readability.
-   `bar_background_color`: The background color of skill bars.
-   `date2_color`: The color for secondary date text.
-   `frame_color`: The color of the preview frame in the web preview.
-   `bold_color`: The color for bolded text. If not provided, it is derived from the `frame_color`.

```yaml
config:
  theme_color: "#0395DE"
  sidebar_color: "#F6F6F6"
  sidebar_text_color: "#000000"
  bar_background_color: "#DFDFDF"
  date2_color: "#616161"
  frame_color: "#757575"
  bold_color: "#585858"
```

## Using Color Schemes

### Preset Schemes

To use a built-in color scheme, set the `color_scheme` property in the `config` section of your YAML file.

```yaml
config:
  color_scheme: "Professional Blue"
```

The following presets are available:

-   **Professional Blue** (default): A high-contrast blue for screen and print.
-   **Creative Purple**: A saturated purple for screen viewing.
-   **Minimal Dark**: A theme with charcoal and neutral grays.
-   **Energetic Orange**: A high-saturation orange.
-   **Modern Teal**: A medium-saturation teal.
-   **Classic Green**: A WCAG AA compliant green.

### Custom Schemes

To define a custom color scheme, set the color properties directly in the `config` section of your YAML file.

```yaml
config:
  theme_color: "#0395DE"
  sidebar_color: "#F6F6F6"
```

## Using Palette Files

Palette files are YAML files that define a set of colors. They are useful for creating reusable color configurations.

To use a palette file, pass the path to the file as the `--palette` command-line argument.

```bash
uv run simple-resume generate --palette resume_private/palettes/my-theme.yaml
```

### Direct Color Palettes

A direct color palette file defines the exact colors to be used.

**`resume_private/palettes/direct-theme.yaml`**
```yaml
palette:
  theme_color: "#4060A0"
  sidebar_color: "#D0D8E8"
  bar_background_color: "#B8B8B8"
  date2_color: "#444444"
  sidebar_text_color: "#333333"
  frame_color: "#324970"
  bold_color: "#263657"
```

### Generated Palettes

A generated palette creates a set of colors from a single seed color.

**`resume_private/palettes/generated-theme.yaml`**
```yaml
palette:
  source: generator
  type: hcl
  size: 6
  seed: 42
  hue_range: [200, 220]
  luminance_range: [0.25, 0.7]
  chroma: 0.25
```

## Verifying Colors

To verify your colors, generate the resume in both HTML and PDF formats. The HTML preview is useful for quick iteration, while the PDF provides the most accurate representation of the printed colors.

```bash
uv run simple-resume generate --format html --open
uv run simple-resume generate --format pdf --open
```

## Troubleshooting

-   **Colors are not being applied**: Ensure that color values are quoted strings that start with a `#`.
-   **Text is hard to read**: Check the contrast between your text and background colors with an online contrast checker.
