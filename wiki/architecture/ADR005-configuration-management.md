# ADR-005: Configuration Management Architecture

## Status
**Accepted** - Current implementation is production-ready with identified refactoring opportunities

## Context
The configuration management system must handle complex resume configurations while providing:

1. **Multi-layered configuration**: Global defaults → resume-specific → user overrides
2. **Color theming**: Palette-based and direct color specification with WCAG compliance
3. **Layout customization**: Extensive page layout and spacing parameters
4. **Validation**: Comprehensive input validation with helpful error messages
5. **Extensibility**: Plugin support for new configuration options and palettes
6. **Session management**: Multi-resume session configuration and inheritance

## Decision
Implemented a hierarchical configuration system with strategy pattern for palette processing:

### Configuration Architecture
```
Configuration Hierarchy:
1. Global Defaults (DEFAULT_COLOR_SCHEME)
2. Session Defaults (SessionConfig)
3. Resume YAML Configuration
4. Runtime Overrides
```

### Core Configuration Models
```python
@dataclass(frozen=True)
class ResumeConfig:
    """A normalized resume configuration with validated fields."""

    # Page dimensions
    page_width: int | None = None
    page_height: int | None = None
    sidebar_width: int | None = None

    # Layout settings
    output_mode: str = "markdown"
    template: str = "resume_no_bars"
    color_scheme: str = "default"

    # Color fields (with WCAG compliance)
    theme_color: str = "#0395DE"
    sidebar_color: str = "#F6F6F6"
    # ... additional color fields
```

### Configuration Processing Pipeline
```python
def normalize_config(
    raw_config: dict[str, Any], filename: str = ""
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Return a normalized copy of the config and optional palette metadata."""

    # 1. Deep copy configuration
    working = copy.deepcopy(raw_config)

    # 2. Apply basic validation
    sidebar_locked = prepare_config(working, filename=filename)

    # 3. Process palette using strategy pattern
    palette_meta = _apply_palette_block(working)

    # 4. Finalize configuration with validation
    finalize_config(
        working,
        filename=filename,
        sidebar_text_locked=sidebar_locked,
    )

    return working, palette_meta
```

### Palette Management Strategy
**Strategy Pattern Implementation**:
- **DirectColorProcessor**: Handles explicit color definitions
- **PaletteColorProcessor**: Manages palette-based color resolution
- **Palette Sources**: Registry, Generator, Remote API sources

```python
class ConfigurationProcessorChain:
    """Manages a chain of configuration processors."""

    def __init__(self):
        self._processors = [
            DirectColorProcessor(),
            PaletteColorProcessor(),  # Fallback processor
        ]
```

## Alternatives Considered

1. **Single configuration file per resume**
   - *Pros*: Simple to understand and debug
   - *Cons*: No configuration reuse, repetitive setups
   - *Decision*: Hierarchical approach provides better user experience

2. **JSON configuration instead of YAML**
   - *Pros*: Better validation, faster parsing
   - *Cons*: Less user-friendly, no comments
   - *Decision*: YAML's readability and comment support essential for users

3. **Configuration database or external service**
   - *Pros*: Centralized configuration, versioning
   - *Cons*: Additional dependency, complexity
   - *Decision*: File-based configuration maintains simplicity and portability

4. **Schema validation library (e.g., Pydantic)**
   - *Pros*: Automatic validation, better error messages
   - *Cons*: Additional dependency, learning curve
   - *Decision*: Manual validation provides more control and custom error messages

## Consequences

### Positive Impacts
- **Flexible configuration**: Multiple sources and override mechanisms
- **Professional defaults**: Sensible defaults for professional resume layouts
- **Color theming**: Advanced palette system with WCAG compliance
- **Extensibility**: Plugin architecture for custom palettes and configuration options
- **Validation**: Comprehensive error checking with helpful messages
- **Session management**: Multi-resume workflows with shared configuration

### Negative Impacts
- **Complexity**: Multiple configuration layers can be confusing
- **Scattered validation**: Validation logic spread across multiple files
- **Tight coupling**: Configuration processing tied to specific data structures
- **Learning curve**: Users need to understand configuration hierarchy

### Technical Details
- **Configuration sources**: 4 layers (defaults → session → resume → runtime)
- **Palette system**: 3 sources (registry, generator, remote API)
- **Validation**: 15+ validation functions across 3 modules
- **Default colors**: 11 predefined color fields with auto-contrast calculation
- **Layout parameters**: 20+ customization options for spacing and dimensions

## Configuration Hierarchy

### 1. Global Defaults
```python
DEFAULT_COLOR_SCHEME = {
    "theme_color": "#0395DE",
    "sidebar_color": "#F6F6F6",
    "sidebar_text_color": "#000000",
    # ... additional defaults
}
```

### 2. Session Configuration
```python
@dataclass
class SessionConfig:
    """Configuration for a `ResumeSession`."""

    paths: Paths | None = None
    default_template: str | None = None
    default_palette: str | None = None
    default_format: OutputFormat | str = OutputFormat.PDF
    auto_open: bool = False
    preview_mode: bool = False
    output_dir: Path | None = None
```

### 3. Resume YAML Configuration
```yaml
# sample_1.yaml
full_name: "John Doe"
template: "resume_no_bars"
config:
  theme_color: "#0395DE"
  sidebar_width: 60
  padding: 12
palette:
  source: "registry"
  name: "ocean"
```

### 4. Runtime Overrides
```python
resume.with_palette("vibrant")
resume.with_config(theme_color="#FF6B35")
```

## Palette Management System

### Palette Sources
```python
class PaletteSource(str, Enum):
    """Define supported palette sources for resume configuration."""

    REGISTRY = "registry"    # Predefined palettes
    GENERATOR = "generator"  # HCL algorithmic generation
    REMOTE = "remote"        # External API sources (ColourLovers)
```

### Palette Registry
```python
class PaletteRegistry:
    """Define an in-memory registry of named palettes."""

    def __init__(self) -> None:
        self._palettes: dict[str, Palette] = {}

    def register(self, palette: Palette) -> None:
        """Register or overwrite a palette."""

    def get(self, name: str) -> Palette:
        """Return a palette by name."""
```

### Palette Processing
```python
# Direct color definition
palette:
  theme_color: "#FF6B35"
  sidebar_color: "#F6F6F6"

# Registry palette
palette:
  source: "registry"
  name: "ocean"

# Generated palette
palette:
  source: "generator"
  hue_range: [180, 240]
  luminance_range: [0.4, 0.8]
```

## Validation Strategy

### Configuration Validation
- **Type validation**: Ensure configuration values have correct types
- **Range validation**: Validate dimensions and spacing parameters
- **Color validation**: Hex color format and WCAG compliance
- **Template validation**: Template existence and compatibility

### Error Handling
```python
class ConfigurationError(SimpleResumeError):
    """Raise when configuration is invalid."""

    def __init__(
        self,
        message: str,
        *,
        config_key: str | None = None,
        config_value: Any | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.config_value = config_value
```

### Validation Pipeline
```python
def validate_dimensions(config: dict[str, Any], filename_prefix: str) -> None:
    """Validate page and sidebar dimensions."""

def _validate_color_fields(config: dict[str, Any], filename_prefix: str) -> None:
    """Validate color fields and format."""

def _normalize_color_scheme(config: dict[str, Any]) -> None:
    """Normalize color scheme to standard format."""
```

## Performance Considerations
- **Deep copying**: Configuration processing uses deep copies for immutability
- **Palette caching**: Registry palettes cached in memory for fast access
- **Validation caching**: Validation results cached where appropriate
- **Lazy loading**: Palettes loaded on-demand from external sources

## Future Improvements

### High Priority (6 months)
1. **Configuration Schema Validation**: Implement JSON Schema for YAML validation
2. **Consolidated Validation**: Centralize validation logic in single module
3. **Configuration Builder**: Fluent API for programmatic configuration

### Medium Priority (1 year)
4. **Plugin System**: Extensible configuration for third-party extensions
5. **Configuration Versioning**: Handle configuration schema migrations
6. **Enhanced Error Messages**: Contextual error messages with suggestions

### Low Priority (18+ months)
7. **Configuration GUI**: Web interface for visual configuration editing
8. **Configuration Templates**: Predefined configuration sets for different industries
9. **Advanced Validation**: Business rule validation beyond type checking

## Testing Strategy
- **Unit Tests**: Individual validation functions and processors
- **Integration Tests**: Configuration loading and processing pipelines
- **End-to-End Tests**: Resume generation with various configuration combinations
- **Property-Based Tests**: Generate random configurations for edge case testing

## Related ADRs
- **ADR-002**: Functional core/imperative shell (configuration processing separation)
- **ADR-004**: Template system architecture (configuration integration)
- **Future**: Plugin system ADR for extensibility improvements

## Author
- **Primary**: Architecture Review
- **Date**: 2025-11-12
- **Review Status**: Accepted - current implementation validated as production-ready

---

*This ADR documents the comprehensive configuration management system that supports complex resume configurations while maintaining extensibility and validation.*
