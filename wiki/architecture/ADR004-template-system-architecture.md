# ADR-004: Template System Architecture

## Status
**Accepted** - The current implementation is production-ready, with identified areas for improvement.

## Context
The template system must support multiple output formats (HTML, PDF, LaTeX). It must also maintain consistency across formats and provide extensive customization options. Key requirements include:

1. **Multi-format support**: HTML for WeasyPrint rendering, LaTeX for academic publishing
2. **Professional layout**: Column-based design with sidebar and main content areas
3. **Color theming**: Dynamic color palettes with WCAG-compliant contrast
4. **Typography**: Professional fonts (Avenir) with fallback support
5. **Responsive design**: Print-optimized layouts with precise control
6. **Asset management**: Font files, icons, and static resources

## Decision
We implemented a hybrid template architecture combining Jinja2 for HTML templates and custom LaTeX rendering for PDF generation:

### Template Engine Strategy
- **HTML Templates**: Jinja2 with template inheritance and macro system
- **LaTeX Templates**: Jinja2 preprocessing + custom LaTeX renderer
- **PDF Generation**: Dual backend (WeasyPrint for HTML→PDF, LaTeX→PDF)

### Template Organization
```
templates/
├── resume_base.html          # Base template with macros and styles
├── resume_no_bars.html       # No sidebar layout (extends base)
├── resume_with_bars.html     # With sidebar layout (extends base)
├── cover.html                # Cover letter template
└── latex/
    └── basic.tex             # LaTeX template for academic publishing
```

### Template Selection Mechanism
```python
def build_html_context(data: dict[str, Any], *, preview: bool) -> tuple[str, dict[str, Any]]:
    """Prepare a template name and context from resume data."""
    template_name = data.get("template", "resume_no_bars")
    return f"{template_name}.html", context
```

## Alternatives Considered

1. **Single template engine for all formats**
   - *Pros*: Consistent syntax, easier maintenance
   - *Cons*: LaTeX requires specialized features; Jinja2 is not ideal for LaTeX.
   - *Decision*: The hybrid approach provides the best of both worlds.

2. **External template system (e.g., Jinja2 extensions)**
   - *Pros*: Offers more powerful template features.
   - *Cons*: Introduces an additional dependency and increased complexity.
   - *Decision*: Standard Jinja2 sufficient for current needs

3. **CSS-in-JS for HTML templates**
   - *Pros*: Dynamic styling capabilities
   - *Cons*: Presents WeasyPrint compatibility issues and adds complexity.
   - *Decision*: Inline CSS maintains WeasyPrint compatibility

## Consequences

### Positive Impacts
- **Professional output**: High-quality HTML and PDF generation
- **Flexible layouts**: Multiple template variants (sidebar/no sidebar)
- **WCAG compliance**: Automatic color contrast calculation
- **Asset management**: Centralized static resources
- **Template inheritance**: Shared macros and styles reduce duplication
- **Caching performance**: Template environment caching improves rendering speed

### Negative Impacts
- **Maintenance Complexity**: Dual template engines require specialized expertise.
- **Inline CSS**: 860+ lines of inline styles in templates
- **Limited template ecosystem**: No third-party template marketplace
- **Testing Challenges**: Visual regression testing is complex.

### Technical Details
- **Template Caching**: Achieved with an `@cache` decorator for the Jinja2 environment.
- **Asset Paths**: Hard-coded to the `static/` directory structure.
- **Font Support**: Limited to Avenir and Font Awesome.
- **Color processing**: WCAG contrast calculations in template macros

## Architecture Patterns

### Template Inheritance System
```html
{%- extends "resume_base.html" -%}

{% block sidebar %}
  <!-- Sidebar content overrides -->
{% endblock %}

{% block body %}
  <!-- Main content overrides -->
{% endblock %}
```

### Macro System
- **Dynamic Font Sizing**: The `dynamic_font_size()` macro provides responsive text.
- **Icon Generation**: The `render_icon()` macro supports color theming.
- **Contact Handling**: The `render_contact_info()` macro manages contact sections.
- **Color Contrast**: `get_contrasting_text_color()` ensures accessibility.

### Configuration Integration
```yaml
# User resume configuration
template: "resume_no_bars"  # Template selection
config:
  sidebar_width: 60         # Layout parameters
  theme_color: "#0395DE"    # Color theming
  accent_color: "#FF6B35"   # Accent colors
  # ... extensive customization options
```

## Performance Considerations
- **Template Environment**: Utilizes a single cached instance per directory.
- **File System Loading**: Uses Jinja2 `FileSystemLoader` with directory scanning.
- **Memory Efficiency**: Shared macros and inheritance reduce duplication.
- **Asset Loading**: Static assets are served from the `static/` directory.

## Future Improvements

### High Priority (6 months)
1. **External CSS Migration**: Migrate inline styles to `static/css/` modules.
2. **Template Validation**: Implement template syntax and structure validation.
3. **Asset Abstraction**: Develop a flexible font and asset management system.

### Medium Priority (1 year)
4. **Template Metadata**: Include versioning and compatibility information.
5. **Visual Testing**: Implement an automated visual regression testing pipeline.
6. **Performance Optimization**: Explore template pre-compilation and bundling.

### Low Priority (18+ months)
7. **Plugin System**: Develop an extensible template architecture for third-party templates.
8. **Template Marketplace**: Create a distribution system for community templates.
9. **Advanced Features**: Investigate conditional blocks and advanced layout systems.

## Testing Strategy
- **Template Resolution**: Implement BDD-style testing for template discovery.
- **Rendering Tests**: Validate end-to-end HTML/LaTeX generation.
- **Asset Loading**: Test font and static resource loading.
- **Configuration Tests**: Test template selection with various configurations.

## Related ADRs
- **ADR-001**: WeasyPrint sidebar pagination (template integration)
- **ADR-002**: Functional core/imperative shell (template rendering separation)
- **Future**: Asset management ADR for font and static resource optimization

## Author
- **Primary**: Architecture Review
- **Date**: 2025-11-12
- **Review Status**: Accepted - The current implementation is validated as production-ready.

---

*This ADR documents the successful hybrid template architecture that supports multiple output formats while maintaining professional quality and extensive customization capabilities.*
