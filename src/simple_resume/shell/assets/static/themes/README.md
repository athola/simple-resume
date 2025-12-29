# Theme Gallery for Simple Resume

This directory contains pre-built theme presets that you can use as-is or customize to create your own unique resume style.

## Available Themes

| Theme | Description | Best For |
|-------|-------------|----------|
| **modern** | Clean, contemporary design with soft blue-gray tones | Tech, startups, creative roles |
| **classic** | Traditional professional design with navy/burgundy | Finance, law, consulting |
| **bold** | High-contrast with vibrant accents | Design, marketing, standout applications |
| **minimal** | Light and airy with maximum whitespace | Academic, research, writing |
| **executive** | Sophisticated dark with gold accents | C-suite, senior leadership |

## Quick Start

### Option 1: Copy and Customize

1. Copy a theme file (e.g., `modern.yaml`) to your project
2. Rename it (e.g., `my-theme.yaml`)
3. Modify the values you want to change
4. Reference it in your resume YAML:

```yaml
# In your resume.yaml, copy the config section from the theme
config:
  palette:
    source: generator
    type: hcl
    size: 5
    seed: 2024
    hue_range: [200, 220]
    luminance_range: [0.35, 0.75]
    chroma: 0.12
  # ... rest of config
```

### Option 2: Use Theme Values Directly

Copy just the `config:` block from any theme into your resume YAML:

```yaml
# my_resume.yaml
template: resume_with_bars
full_name: Jane Developer
job_title: Software Engineer

# Paste the config block from modern.yaml, classic.yaml, etc.
config:
  palette:
    source: generator
    type: hcl
    size: 5
    seed: 2024
    hue_range: [200, 220]
    luminance_range: [0.35, 0.75]
    chroma: 0.12

  page_width: 210
  page_height: 297
  # ... etc
```

## Customization Guide

### Color Palette

The palette generator creates harmonious colors automatically:

```yaml
config:
  palette:
    source: generator
    type: hcl                    # HCL color space (perceptually uniform)
    size: 5                      # Number of colors to generate
    seed: 2024                   # Change this for different colors!
    hue_range: [200, 220]        # Color hue range (0-360)
    luminance_range: [0.35, 0.75]  # Light to dark range (0-1)
    chroma: 0.12                 # Color saturation (0-1)
```

**Quick color adjustments:**

- Want different colors? → Change `seed` to any number
- Want warmer colors? → Use `hue_range: [0, 60]` (red-yellow)
- Want cooler colors? → Use `hue_range: [180, 270]` (cyan-purple)
- Want darker sidebar? → Lower `luminance_range` (e.g., `[0.10, 0.30]`)
- Want more vibrant? → Increase `chroma` (e.g., `0.25`)

### Hue Reference Chart

| Hue Range | Colors |
|-----------|--------|
| 0-30 | Red, Orange |
| 30-60 | Orange, Yellow |
| 60-120 | Yellow, Green |
| 120-180 | Green, Cyan |
| 180-240 | Cyan, Blue |
| 240-300 | Blue, Purple |
| 300-360 | Purple, Red |

### Layout Dimensions

All dimensions are in millimeters (mm) for print accuracy:

```yaml
config:
  # Page size (A4 default)
  page_width: 210
  page_height: 297
  padding: 12                    # Overall page padding

  # Sidebar
  sidebar_width: 60              # Width of left sidebar
  sidebar_padding_top: 5
  sidebar_padding_bottom: 5
  sidebar_padding_left: 5
  sidebar_padding_right: 5

  # Profile image
  profile_width: 50              # Profile photo width
  profile_image_padding_bottom: 6

  # Main content
  pitch_padding_top: 10          # Space above summary
  pitch_padding_bottom: 5
  pitch_padding_left: 5
  h2_padding_left: 5             # Section header indent
  h2_width: 140                  # Section header width

  # Experience entries
  h3_padding_top: 3              # Space above job titles
  date_container_width: 25       # Date column width
  description_container_padding_left: 5
  skill_container_padding_top: 2
```

### Section Icons

Customize the circular icons next to section headings:

```yaml
config:
  section_icon_circle_size: "10mm"       # Circle diameter
  section_icon_circle_x_offset: "0mm"    # Horizontal adjustment
  section_icon_design_size: "5mm"        # Icon size inside circle
  section_icon_design_x_offset: "0mm"    # Icon horizontal position
  section_icon_design_y_offset: "0mm"    # Icon vertical position
  section_heading_text_margin: "-5mm"    # Text margin from icon
  section_heading_marker_margin_left: "-10mm"
  section_heading_marker_line_height: "15mm"
```

## Creating Your Own Theme

1. **Start from an existing theme** - Copy the one closest to your vision
2. **Change the seed** - Get new colors instantly with a different `seed` value
3. **Adjust hue_range** - Pick your brand colors
4. **Fine-tune luminance** - Control light/dark balance
5. **Test with preview** - Use `--preview` flag to see changes in browser

### Example: Creating a "Tech Startup" Theme

```yaml
config:
  # Vibrant purple-pink tech colors
  palette:
    source: generator
    type: hcl
    size: 5
    seed: 42
    hue_range: [280, 330]        # Purple to pink
    luminance_range: [0.30, 0.70]
    chroma: 0.20                 # Vibrant but professional

  # Compact modern layout
  sidebar_width: 55
  padding: 10
  h3_padding_top: 3
  date_container_width: 12

  # Smaller, subtle icons
  section_icon_circle_size: "7mm"
  section_icon_design_size: "3.5mm"
```

## Tips for Great Themes

1. **Contrast matters** - Ensure text is readable on sidebar backgrounds
2. **Consistency** - Keep padding values proportional (e.g., all multiples of 5)
3. **Test with real content** - Long names and descriptions reveal layout issues
4. **Print preview** - Colors look different on screen vs paper
5. **PDF check** - Always generate a PDF to verify final output

## Sharing Your Theme

Created a great theme? Consider contributing it back!

1. Add your theme YAML to this directory
2. Include a descriptive header comment
3. Test with multiple sample resumes
4. Submit a pull request

## See Also

- [CSS Architecture](../css/README.md) - How CSS styling works
- [Palette Generator](../../../../wiki/Palette-Generator.md) - Deep dive on color generation
- [Sample Resumes](../../../../../../sample/input/) - Example resumes using different themes
