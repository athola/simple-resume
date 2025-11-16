# ADR-006: Error Handling Strategy

## Status
**Accepted** - Current implementation is production-ready with identified integration improvements

## Context
The error handling system must provide:

1. **User-friendly error messages**: Clear, actionable feedback for resume generation failures
2. **Rich error context**: File paths, configuration details, and debugging information
3. **Graceful degradation**: Fallback behaviors and recovery mechanisms
4. **Domain-specific errors**: Specialized exception types for different failure modes
5. **Two-tier handling**: Validation inspection vs. action-oriented error raising
6. **Security considerations**: Safe error handling that doesn't expose sensitive information

## Decision
Implemented a hierarchical exception system with two-tier error handling pattern:

### Exception Hierarchy
```python
class SimpleResumeError(Exception):
    """Base exception for all simple-resume errors."""

class ValidationError(SimpleResumeError):
    """Raise when resume data validation fails."""

class ConfigurationError(SimpleResumeError):
    """Raise when configuration is invalid."""

class TemplateError(SimpleResumeError):
    """Raise when template processing fails."""

class GenerationError(SimpleResumeError):
    """Raise when PDF/HTML generation fails."""

class PaletteError(SimpleResumeError):
    """Raise when color palette operations fail."""

class FileSystemError(SimpleResumeError):
    """Raise when file system operations fail."""

class SessionError(SimpleResumeError):
    """Raise when session management fails."""
```

### Two-Tier Error Handling Pattern

#### Tier 1: Inspection (Non-Exception Based)
```python
def validate(self) -> ValidationResult:
    """Validate resume data and return result without raising exceptions."""

result = resume.validate()
if result.warnings:
    log.warning(result.warnings)
if not result.is_valid:
    print(f"Validation errors: {result.errors}")
```

#### Tier 2: Action (Exception-Based)
```python
def validate_or_raise(self) -> None:
    """Validate resume data and raise exceptions on failures."""

resume.validate_or_raise()  # Raises ValidationError if invalid
resume.to_pdf("output.pdf")  # Fails fast on validation errors
```

### Error Context and Metadata
```python
class SimpleResumeError(Exception):
    def __init__(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        filename: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.context = context or {}
        self.filename = filename

class FileSystemError(SimpleResumeError):
    def __init__(
        self,
        message: str,
        *,
        path: Path | str | None = None,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.path = str(path) if path else None
        self.operation = operation
```

## Alternatives Considered

1. **Single exception type with error codes**
   - *Pros*: Simpler hierarchy, easier to manage
   - *Cons*: Less specific error handling, less Pythonic
   - *Decision*: Exception hierarchy provides better specificity and Python idioms

2. **No two-tier pattern (always raise exceptions)**
   - *Pros*: Simpler API design
   - *Cons*: No way to inspect validation without crashing
   - *Decision*: Two-tier pattern supports both validation and fail-fast workflows

3. **Custom error result objects instead of exceptions**
   - *Pros*: More control over error information
   - *Cons*: Non-standard, breaks Python exception handling
   - *Decision*: Standard exception handling provides better integration

4. **Global error handler with logging only**
   - *Pros*: Centralized error handling
   - *Cons*: Loss of error context, difficult debugging
   - *Decision*: Exception propagation preserves context and stack traces

## Consequences

### Positive Impacts
- **User-friendly errors**: Specific exception types with clear error messages
- **Rich debugging context**: File paths, configuration details, and stack traces
- **Flexible handling**: Both inspection and exception-based workflows supported
- **Graceful degradation**: Fallback behaviors and cleanup mechanisms
- **Security awareness**: Safe error handling without information leakage

### Negative Impacts
- **Exception hierarchy complexity**: Multiple exception types to understand
- **Palette exception isolation**: Separate hierarchy not integrated with base class
- **Inconsistent context**: Some exceptions lack sufficient contextual information
- **Testing complexity**: Need to test multiple exception paths and scenarios

### Technical Details
- **Exception types**: 7 main exception classes plus palette-specific hierarchy
- **Context preservation**: Filename, path, operation, and custom context fields
- **Error chaining**: Consistent use of `from exc` for exception wrapping
- **Exit codes**: CLI uses specific exit codes for different error categories

## Error Handling Patterns by Domain

### Configuration Errors
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

### Generation Errors
```python
# Exception wrapping pattern in generation.py
try:
    # PDF/HTML generation logic
    pass
except Exception as exc:
    if isinstance(exc, (GenerationError, ValidationError, ConfigurationError, FileSystemError)):
        raise
    raise GenerationError(f"Failed to generate {error_label}: {exc}", format_type=format_type) from exc
```

### Palette Errors (Separate Hierarchy)
```python
# palettes/exceptions.py - Not integrated with main hierarchy
class PaletteError(RuntimeError):
    """Base class for palette-related errors."""

class PaletteLookupError(PaletteError):
    """Raised when a palette cannot be found."""

class PaletteGenerationError(PaletteError):
    """Raised when palette generation fails."""
```

## CLI Error Handling Strategy

### Error Classification and User Experience
```python
def _handle_unexpected_error(exc: Exception, context: str) -> int:
    """Classify and handle unexpected exceptions with user-friendly messages."""

    if isinstance(exc, (PermissionError, OSError)):
        error_type = "File System Error"
        exit_code = 2
        suggestion = "Check file permissions and disk space"

    elif isinstance(exc, (KeyError, AttributeError, TypeError)):
        error_type = "Internal Error"
        exit_code = 3
        suggestion = "This may be a bug - please report it"

    print(f"{error_type}: {exc}")
    if suggestion:
        print(f"Suggestion: {suggestion}")

    return exit_code
```

### Exit Code Strategy
- **Exit Code 1**: General/simple_resume errors (ValidationError, ConfigurationError)
- **Exit Code 2**: File system errors (permissions, disk space)
- **Exit Code 3**: Internal errors (unexpected exceptions)
- **Exit Code 4**: Usage errors (invalid command-line arguments)

## Error Recovery Strategies

### Graceful Degradation
```python
# LaTeX compilation with log preservation
try:
    compile_latex_to_pdf(tex_file, output_path)
except LatexCompilationError as exc:
    # Preserve compilation log for debugging
    if exc.log_path and exc.log_path.exists():
        shutil.move(exc.log_path, output_path.with_suffix('.log'))
    raise

# File cleanup in finally blocks
try:
    # File operations
    pass
finally:
    # Cleanup temporary files
    if temp_file.exists():
        temp_file.unlink()
```

### Fallback Behaviors
- **Default palette**: Fallback to default color scheme when custom palette fails
- **Template fallback**: Use default template when specified template unavailable
- **Path resolution**: Try multiple path resolution strategies

## Security Considerations

### Safe Error Handling
- **Path sanitization**: Validate file paths before including in error messages
- **URL validation**: Security-focused validation in palette remote operations
- **Information leakage**: Avoid exposing sensitive configuration details in error messages

### Palette Security Example
```python
# palettes/sources.py - Secure URL validation
def validate_url(url: str) -> None:
    """Validate palette URL for security."""
    parsed = urlparse(url)

    # Only allow HTTPS and HTTP schemes
    if parsed.scheme not in ('https', 'http'):
        raise PaletteRemoteError(f"Invalid URL scheme: {parsed.scheme}")

    # Block localhost and private networks
    if parsed.hostname in ('localhost', '127.0.0.1') or parsed.hostname.startswith('192.168.'):
        raise PaletteRemoteError(f"Blocked URL: {parsed.hostname}")
```

## Testing Strategy

### Exception Testing Patterns
```python
# Test specific exception types
def test_invalid_color_validation(self):
    with pytest.raises(ValidationError, match="Invalid hex color"):
        validate_color_field("not-a-color")

# Test error context
def test_file_system_error_context(self):
    with pytest.raises(FileSystemError) as exc_info:
        validate_file_path("/nonexistent/path")

    assert exc_info.value.path == "/nonexistent/path"
    assert "does not exist" in str(exc_info.value)
```

### Coverage Requirements
- **All exception types**: Unit tests for each exception class
- **Error contexts**: Test that exceptions capture appropriate context
- **Error propagation**: Test exception wrapping and chaining
- **CLI handling**: Test exit codes and user messages

## Performance Considerations
- **Exception creation cost**: Minimal impact, exceptions used for exceptional cases
- **Context collection**: Only collect context when exceptions are raised
- **Error logging**: Structured logging for debugging without performance impact
- **Memory usage**: Exception objects are short-lived and garbage collected

## Future Improvements

### High Priority (6 months)
1. **Integrate Palette Hierarchy**: Unify palette exceptions with main SimpleResumeError base
2. **Enhanced Error Context**: Ensure all exceptions capture relevant context
3. **Consistent Exception Chaining**: Standardize `from exc` usage across all modules

### Medium Priority (1 year)
4. **Error Recovery Framework**: Systematic approach to recovery strategies
5. **Advanced User Messages**: Contextual suggestions and auto-fix suggestions
6. **Error Analytics**: Anonymous error reporting for improvement

### Low Priority (18+ months)
7. **Internationalization**: Multi-language error messages
8. **Error Visualization**: Visual error reports for complex failures
9. **Machine Learning**: Automated error classification and resolution suggestions

## Related ADRs
- **ADR-002**: Functional core/imperative shell (error handling separation)
- **ADR-005**: Configuration management (configuration validation errors)
- **Future**: Security ADR for enhanced error handling security considerations

## Author
- **Primary**: Architecture Review
- **Date**: 2025-11-12
- **Review Status**: Accepted - current implementation validated as production-ready

---

*This ADR documents the comprehensive error handling strategy that provides user-friendly error messages, rich debugging context, and graceful recovery mechanisms while maintaining security considerations.*
