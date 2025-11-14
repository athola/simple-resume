# ADR-007: Color Palette System Architecture

## Status
**Accepted** - Current implementation is production-ready with accessibility enhancements planned

## Context
The application requires a color system that can source colors from multiple places, ensures text is readable, and handles errors gracefully. Key requirements include:

*   **Multiple Sources**: Support for pre-defined palettes, generating palettes from HCL, and fetching them from remote APIs.
*   **Accessibility**: Automatic calculation of color contrast to meet WCAG 2.1 guidelines.
*   **Automation**: Intelligent selection of contrasting text colors to ensure readability without manual configuration.
*   **Flexibility**: Allow users to define colors directly or use theme-based palettes.
*   **Error Handling**: Provide a default color scheme when a configured palette cannot be resolved.
*   **Security**: Validate remote API URLs and sanitize color inputs to prevent vulnerabilities.

## Decision
Implemented a multi-source palette system with WCAG-compliant color calculations and intelligent contrast management:

### Palette Architecture
```python
@dataclass(frozen=True)
class Palette:
    """Define palette metadata and resolved swatches."""
    name: str
    swatches: tuple[str, ...]  # Hex color strings
    source: str
    metadata: dict[str, object] = field(default_factory=dict)

class PaletteSource(str, Enum):
    """Define supported palette sources for resume configuration."""
    REGISTRY = "registry"      # Named palettes from registry
    GENERATOR = "generator"    # HCL-generated palettes
    REMOTE = "remote"          # Remote API (ColourLovers)
```

### Processing Pipeline
```python
def _resolve_palette_block(block: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    """Resolve palette block based on source type."""
    source = PaletteSource.normalize(block.get("source"))

    if source is PaletteSource.REGISTRY:
        # Look up named palette from registry
        registry = get_palette_registry()
        palette = registry.get(str(name))
        return list(palette.swatches), {"attribution": palette.metadata}

    elif source is PaletteSource.GENERATOR:
        # Generate HCL-based palette
        swatches = generate_hcl_palette(size, seed, hue_range, chroma, luminance_range)
        return swatches, {"seed": seed, "hue_range": hue_range, "chroma": chroma}

    elif source is PaletteSource.REMOTE:
        # Fetch from ColourLovers API
        client = ColourLoversClient()
        palettes = client.fetch(keywords, num_results, order_by)
        return list(palettes[0].swatches), {"attribution": palettes[0].metadata}
```

## Alternatives Considered

1. **Single source palette system**
   - *Pros*: Simpler implementation, easier to maintain
   - *Cons*: Limited flexibility, no user customization
   - *Decision*: Multi-source approach provides better user experience

2. **Manual color management only**
   - *Pros*: Full control, predictable results
   - *Cons*: Requires color expertise, no accessibility guarantees
   - *Decision*: Automatic management with accessibility features

3. **Third-party color library integration**
   - *Pros*: Rich feature set, professional color tools
   - *Cons*: Additional dependency, complexity overhead
   - *Decision*: Custom implementation provides better integration and control

## Consequences

### Positive
*   **Improved Readability**: Text colors are now automatically calculated to meet WCAG 2.1 contrast ratios against their background, making the output more accessible.
*   **Flexible Color Theming**: Users can choose from three palette sources (pre-defined, generated, or remote), offering more customization.
*   **Consistent Generation**: The HCL-based generator uses a deterministic algorithm, ensuring that generated color palettes are reproducible.
*   **Secure API Access**: Remote API calls are validated, cached, and executed with timeouts to prevent network issues from blocking generation.

### Negative
*   **Increased Complexity**: The logic for handling multiple palette sources is more complex than a single-source system.
*   **Network Dependency**: Fetching remote palettes introduces a dependency on network connectivity and the third-party API's availability.
*   **Incomplete Enforcement**: The system calculates contrast ratios but does not yet prevent the user from choosing non-compliant color combinations. This is noted as future work.
*   **Cascading Failures**: A failure to resolve a palette may cause rendering issues downstream if not handled correctly by the caller.

### Technical Details
- **Palette sources**: 3 types with strategy pattern for extensibility
- **WCAG calculations**: Full sRGB linearization with BT.709 coefficients
- **Luminance thresholds**: Empirically tuned for optimal text contrast
- **Caching**: 12-hour TTL for remote palette data
- **Deterministic generation**: Seed-based HCL palette generation

## WCAG Compliance Implementation

### Color Luminance Calculations
```python
def _calculate_luminance_from_rgb(rgb: tuple[int, int, int]) -> float:
    """Calculate relative luminance using WCAG 2.1 formula."""
    r, g, b = rgb

    def _linearize(component: int) -> float:
        value = component / 255.0
        return (
            value / WCAG_LINEARIZATION_DIVISOR
            if value <= WCAG_LINEARIZATION_THRESHOLD
            else ((value + WCAG_LINEARIZATION_OFFSET) / (1 + WCAG_LINEARIZATION_OFFSET)) ** WCAG_LINEARIZATION_EXPONENT
        )

    # BT.709 coefficients for relative luminance
    return 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear
```

### Contrast Ratio Calculation
```python
def calculate_contrast_ratio(color1: str, color2: str) -> float:
    """Return WCAG contrast ratio between two hex colors."""
    lum1 = _calculate_luminance_from_rgb(hex_to_rgb(color1))
    lum2 = _calculate_luminance_from_rgb(hex_to_rgb(color2))
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)
```

### Automatic Text Color Generation
```python
def get_contrasting_text_color(background_color: str) -> str:
    """Return a readable text color for the given background."""
    luminance = calculate_luminance(background_color)

    # Empirical luminance buckets for WCAG compliance
    if luminance <= LUMINANCE_VERY_DARK:      # ≤ 0.15
        return "#F5F5F5"  # Very light text
    if luminance <= LUMINANCE_DARK:           # ≤ 0.5
        return "#FFFFFF"  # White text
    if luminance >= LUMINANCE_VERY_LIGHT:     # ≥ 0.8
        return "#333333"  # Dark gray text
    return "#000000"  # Black text
```

### Color Calculation Service
```python
class ColorCalculationService:
    """Encapsulate Law-of-Demeter-friendly color decisions."""

    @staticmethod
    def calculate_sidebar_text_color(config: dict[str, Any]) -> str:
        sidebar_color = config.get("sidebar_color")
        if isinstance(sidebar_color, str) and is_valid_color(sidebar_color):
            return get_contrasting_text_color(sidebar_color)
        return DEFAULT_COLOR_SCHEME["sidebar_text_color"]

    @staticmethod
    def calculate_heading_icon_color(config: dict[str, Any]) -> str:
        theme_color = config.get("theme_color", DEFAULT_COLOR_SCHEME["theme_color"])
        sidebar_color = config.get("sidebar_color", DEFAULT_COLOR_SCHEME["sidebar_color"])
        if calculate_contrast_ratio(theme_color, sidebar_color) >= ICON_CONTRAST_THRESHOLD:
            return theme_color
        return get_contrasting_text_color(sidebar_color)

    @staticmethod
    def ensure_color_contrast(background_color: str, text_color: str | None = None) -> str:
        if text_color and is_valid_color(text_color):
            ratio = calculate_contrast_ratio(text_color, background_color)
            if ratio >= ICON_CONTRAST_THRESHOLD:
                return text_color
        return get_contrasting_text_color(background_color)
```

## Color Management Strategy

### Default Color Scheme
```python
DEFAULT_COLOR_SCHEME = {
    "theme_color": "#0395DE",      # Primary accent
    "sidebar_color": "#F6F6F6",   # Light sidebar background
    "sidebar_text_color": "#000000", # Black text for contrast
    "bar_background_color": "#DFDFDF", # Neutral gray bars
    "date2_color": "#616161",      # Dark gray dates
    "frame_color": "#757575",      # Medium gray frame
    "heading_icon_color": "#0395DE", # Matches theme
    "bold_color": "#585858",       # Darkened frame
}
```

### Color Field Application Order
```python
COLOR_FIELD_ORDER = [
    "accent_color",      # Primary theme color
    "sidebar_color",     # Sidebar background
    "text_color",        # Main text (calculated)
    "emphasis_color",    # Secondary accents
    "link_color",        # Hyperlink colors
]
```

### Configuration Processing Strategy
```python
def apply_palette_block(config: dict[str, Any]) -> dict[str, Any] | None:
    """Resolve a user-provided palette block into normalized colors."""

    block = config.get("palette")
    if not block:
        return None

    if _has_direct_colors(block):
        config.update(block)
        return None

    return _process_palette_colors(config, block)


def finalize_config(config: dict[str, Any], *, filename: str = "") -> None:
    """Apply WCAG-aware defaults via ColorCalculationService."""

    _validate_color_fields(config, filename_prefix=filename)
    _auto_calculate_sidebar_text_color(config)
    _handle_sidebar_bold_color(config, filename)
    _handle_icon_color(config, filename)
```

## HCL Palette Generation

### Deterministic Color Generation
```python
def generate_hcl_palette(
    size: int,
    seed: int | None = None,
    hue_range: tuple[float, float] = (0.0, 360.0),
    chroma: float = 0.12,
    luminance_range: tuple[float, float] = (0.35, 0.85),
) -> list[str]:
    """Generate deterministic palette using HCL-inspired algorithm."""
    rng = DeterministicRNG(seed or DEFAULT_SEED)

    # Generate evenly distributed hues with controlled variation
    hues = _generate_hues(start=hue_start, end=hue_end, count=size, rng=rng)
    luminances = _generate_luminance_values(start=lum_start, end=lum_end, count=size)

    # Convert to HSL then to hex using proper color space conversion
    colors = []
    for hue, luminance in zip(hues, luminances):
        colors.append(_hsl_to_hex(hue, saturation, _clamp(luminance, 0.0, 1.0)))
    return colors
```

## Remote Palette Integration

### Secure API Access
```python
class ColourLoversClient:
    """Provide secure wrapper around ColourLovers palette API."""

    API_BASE = "https://www.colourlovers.com/api/palettes"

    def fetch(self, **kwargs) -> list[Palette]:
        """Fetch palettes with security validation."""
        # URL validation - only HTTPS/HTTP allowed
        _validate_url(url)

        # 12-hour TTL caching with file-based storage
        cached = self._read_cache(cache_path)
        if cached is not None:
            return [self._palette_from_payload(entry) for entry in cached]
```

### Configuration Examples
```yaml
# Registry palette
palette:
  source: "registry"
  name: "ocean"

# Generated palette
palette:
  source: "generator"
  size: 6
  seed: 42
  hue_range: [200, 220]    # Blue hues
  luminance_range: [0.3, 0.8]  # Good contrast range
  chroma: 0.2              # Moderate saturation

# Remote palette
palette:
  source: "remote"
  keywords: "professional"
  num_results: 1
  order_by: "score"
```

## Performance Considerations
- **Registry Caching**: Singleton registry with LRU cache for palette lookups
- **Remote Caching**: 12-hour TTL for remote palette data to reduce API calls
- **Deterministic Generation**: Seed-based generation ensures reproducible results
- **Lazy Loading**: Palettes loaded on-demand rather than at startup

## Security Considerations
- **URL Validation**: Only HTTPS/HTTP schemes allowed for remote APIs
- **Path Validation**: Prevents directory traversal in palette file loading
- **Input Sanitization**: All color inputs validated before processing
- **Network Isolation**: Remote API calls isolated with timeouts and error handling

## Future Improvements

### High Priority (6 months)
1. **WCAG Validation Layer**: Add automatic contrast ratio validation with suggestions
2. **Contrast Optimization**: Automatic color adjustment to meet WCAG AA/AAA standards
3. **Enhanced Error Recovery**: More robust error handling if a palette fails to load

### Medium Priority (1 year)
4. **Accessibility Scoring**: Built-in palette accessibility evaluation and metadata
5. **Color Blindness Support**: Alternative color schemes for different vision types
6. **Advanced Generation**: Machine learning-based palette generation with accessibility constraints

### Low Priority (18+ months)
7. **Real-time Preview**: Interactive palette selection with live contrast feedback
8. **Advanced Remote Sources**: Integration with additional design APIs
9. **Palette Evolution**: Dynamic palette adjustment based on content and context

## Related ADRs
- **ADR-004**: Template system architecture (palette integration)
- **ADR-005**: Configuration management (palette processing)
- **ADR-006**: Error handling strategy (palette exception hierarchy)
- **Future**: Accessibility ADR for comprehensive WCAG compliance

## Author
- **Primary**: Architecture Review
- **Date**: 2025-11-12
- **Review Status**: Accepted - current implementation provides solid foundation for color management
