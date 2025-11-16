# ADR-004: Template System Architecture

## Status
**Accepted** - Current implementation is production-ready with identified improvement areas

## Context
The template system must support multiple output formats (HTML, PDF, LaTeX) while maintaining consistency across formats and providing extensive customization options. Key requirements include:

1. **Multi-format support**: HTML for WeasyPrint rendering, LaTeX for academic publishing
2. **Professional layout**: Column-based design with sidebar and main content areas
3. **Color theming**: Dynamic color palettes with WCAG-compliant contrast
4. **Typography**: Professional fonts (Avenir) with fallback support
5. **Responsive design**: Print-optimized layouts with precise control
6. **Asset management**: Font files, icons, and static resources

## Decision
Implemented a hybrid template architecture combining Jinja2 for HTML templates and custom LaTeX rendering for PDF generation:

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
   - *Cons*: LaTeX requires specialized features, Jinja2 not ideal for LaTeX
   - *Decision*: Hybrid approach provides best of both worlds

2. **External template system (e.g., Jinja2 extensions)**
   - *Pros*: More powerful template features
   - *Cons*: Additional dependency, increased complexity
   - *Decision*: Standard Jinja2 sufficient for current needs

3. **CSS-in-JS for HTML templates**
   - *Pros*: Dynamic styling capabilities
   - *Cons*: WeasyPrint compatibility issues, complexity
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
- **Maintenance complexity**: Dual template engines require expertise
- **Inline CSS**: 860+ lines of inline styles in templates
- **Limited template ecosystem**: No third-party template marketplace
- **Testing challenges**: Visual regression testing complexity

### Technical Details
- **Template caching**: `@cache` decorator for Jinja2 environment
- **Asset paths**: Hard-coded to `static/` directory structure
- **Font support**: Limited to Avenir and Font Awesome
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
- **Dynamic font sizing**: `dynamic_font_size()` macro for responsive text
- **Icon generation**: `render_icon()` macro with color theming
- **Contact handling**: `render_contact_info()` macro for contact sections
- **Color contrast**: `get_contrasting_text_color()` for accessibility

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
- **Template environment**: Single cached instance per directory
- **File system loading**: Jinja2 `FileSystemLoader` with directory scanning
- **Memory efficiency**: Shared macros and inheritance reduce duplication
- **Asset loading**: Static assets served from `static/` directory

## Future Improvements

### High Priority (6 months)
1. **External CSS Migration**: Move inline styles to `static/css/` modules
2. **Template Validation**: Add template syntax and structure validation
3. **Asset Abstraction**: Flexible font and asset management system

### Medium Priority (1 year)
4. **Template Metadata**: Add versioning and compatibility information
5. **Visual Testing**: Automated visual regression testing pipeline
6. **Performance Optimization**: Template pre-compilation and bundling

### Low Priority (18+ months)
7. **Plugin System**: Extensible template architecture for third-party templates
8. **Template Marketplace**: Distribution system for community templates
9. **Advanced Features**: Conditional blocks, advanced layout systems

## Testing Strategy
- **Template Resolution**: BDD-style testing for template discovery
- **Rendering Tests**: End-to-end HTML/LaTeX generation validation
- **Asset Loading**: Font and static resource loading tests
- **Configuration Tests**: Template selection with different configurations

## Related ADRs
- **ADR-001**: WeasyPrint sidebar pagination (template integration)
- **ADR-002**: Functional core/imperative shell (template rendering separation)
- **Future**: Asset management ADR for font and static resource optimization

## Author
- **Primary**: Architecture Review
- **Date**: 2025-11-12
- **Review Status**: Accepted - current implementation validated as production-ready

---

*This ADR documents the successful hybrid template architecture that supports multiple output formats while maintaining professional quality and extensive customization capabilities.*
