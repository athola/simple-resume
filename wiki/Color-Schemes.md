# Color Scheme Guide

This guide explains how to customize the colors of your resume by defining them in
the `config` section of your YAML file.

## Color Properties

Here are the available color properties and what they control:

```yaml
config:
  theme_color: "#0395DE"          # Headings and accent elements
  sidebar_color: "#F6F6F6"        # Sidebar background
  sidebar_text_color: "#000000"   # Sidebar text (auto-calculated if omitted)
  bar_background_color: "#DFDFDF"  # Progress bar background in `resume_with_bars` template
  date2_color: "#616161"          # Secondary date text
  frame_color: "#757575"          # Preview frame in web preview
```

The contact icons automatically use the `sidebar_text_color`, so you don't need to
worry about them when using a dark sidebar.

## Using Color Schemes

You can use one of our preset color schemes, create your own custom scheme, or use
external palette files.

### Preset Schemes

To use a preset scheme, simply add the `color_scheme` property to your `config` section:

```yaml
config:
  color_scheme: "Professional Blue"
```

Here are the available presets:

- **Professional Blue (Default)**: A high-contrast blue suitable for both screen and print.
- **Creative Purple**: A saturated purple, best for screen viewing.
- **Minimal Dark**: Charcoal and neutral grays.
- **Energetic Orange**: A high-saturation orange.
- **Modern Teal**: A medium-saturation teal.
- **Classic Green**: A WCAG AA compliant green.

### Custom Schemes

To create your own scheme, define the individual color properties in your `config` section.
A good way to start is to copy a preset and modify it.

```yaml
config:
  theme_color: "#0395DE"
  sidebar_color: "#F6F6F6"
  # ... and so on
```

All colors must be quoted hexadecimal strings (e.g., `"#0395DE"`).

## Standalone Palette Files

For more complex or reusable color configurations, you can use standalone palette files. This is useful for creating multiple color variations of the same resume or sharing color schemes.

### Creating a Palette File

A palette file is a YAML file that contains a `palette` object. There are two ways to define a palette:

#### 1. Direct Color Definitions

You can define colors directly using key-value pairs. This is useful for matching brand colors or creating print-optimized palettes.

**`palettes/direct-theme.yaml`**

```yaml
palette:
  theme_color: "#4060A0"
  sidebar_color: "#D0D8E8"
  bar_background_color: "#B8B8B8"
  date2_color: "#444444"
  sidebar_text_color: "#333333"
```

#### 2. Generated Palettes

You can also generate a palette procedurally using the HCL-based generator.

**`palettes/generated-theme.yaml`**

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

### Using a Palette File

To use a palette file, pass it to the `--palette` option when generating your resume:

```bash
uv run simple-resume generate --palette palettes/direct-theme.yaml
```

The colors in the palette file will be merged with your resume's configuration.

## Testing Your Colors

To see your color scheme in action, you can:

- **Generate an HTML preview**: `uv run simple-resume generate --format html --open`
- **Generate a PDF**: `uv run simple-resume generate --format pdf --open`

Always generate a test PDF, as colors can render differently in print.

## Troubleshooting

- **Colors not appearing**: Make sure your color values are quoted strings with a leading `#`.
- **Poor readability**: Check the contrast between your text and background colors.
