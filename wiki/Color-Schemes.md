# Color Scheme Guide

This guide explains how to customize the colors of your resume. You can use preset color schemes, define your own colors, or use palette files for more advanced configurations.

## Color Properties

The following color properties can be set in the `config` section of your YAML file. All colors must be specified as quoted hexadecimal strings (e.g., `"#0395DE"`).

-   `theme_color`: The primary color for headings and other accent elements.
-   `sidebar_color`: The background color of the sidebar.
-   `sidebar_text_color`: The text color in the sidebar. If not provided, this color is automatically calculated based on the `sidebar_color` to ensure readability. Contact icons also use this color.
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

The easiest way to change the look of your resume is to use one of the built-in color schemes.

```yaml
config:
  color_scheme: "Professional Blue"
```

The following presets are available:

-   **Professional Blue** (default): A high-contrast blue suitable for both screen and print.
-   **Creative Purple**: A saturated purple, best for screen viewing.
-   **Minimal Dark**: A theme with charcoal and neutral grays.
-   **Energetic Orange**: A high-saturation orange.
-   **Modern Teal**: A medium-saturation teal.
-   **Classic Green**: A WCAG AA compliant green.

### Custom Schemes

You can define your own color scheme by setting the color properties directly in your YAML file.

```yaml
config:
  theme_color: "#0395DE"
  sidebar_color: "#F6F6F6"
```

## Using Palette Files

For more advanced and reusable color configurations, you can use palette files. A palette file is a YAML file that defines a set of colors.

To use a palette file, pass the path to the file using the `--palette` command-line argument.

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

You can also generate a palette of colors based on a set of parameters. This is useful for creating a consistent set of colors from a single seed color.

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

To check how your colors will look, generate the resume in both HTML and PDF formats. The HTML preview is useful for quick iteration, but the PDF will give you the most accurate representation of the final printed colors.

```bash
uv run simple-resume generate --format html --open
uv run simple-resume generate --format pdf --open
```

## Troubleshooting

-   **Colors are not being applied:** Ensure that the color values are enclosed in quotes and start with a `#`.
-   **Text is hard to read:** Check the contrast between your text and background colors. You can use an online contrast checker to ensure your color combinations are accessible.
