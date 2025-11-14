# Path Handling Guide

`simple-resume` follows the **Path-first principle** for consistent path handling:

1.  **Accept `str | Path` at API boundaries** for flexibility.
2.  **Normalize to `Path` immediately** after receiving input.
3.  **Use `Path` objects internally** throughout the codebase.
4.  **Convert to `str` only when required** by external APIs.

### When to Convert to String

Only convert `Path` to `str` when:
- External libraries require strings (e.g., WeasyPrint's `write_pdf(str)`).
- Storing in exception messages (handled automatically in exception `__init__`).
- Building error messages for display.

### Examples

```python
# Good: Accept both, normalize early
def process_file(file_path: str | Path) -> None:
    path = Path(file_path)  # Normalize immediately
    path.read_text()  # Use Path methods


# Good: Pass Path objects directly
output_path = paths.output / "resume.pdf"
resume.to_pdf(output_path)  # No conversion needed

# Good: Convert only when external API requires it
html_doc.write_pdf(str(output_path))  # WeasyPrint needs str

# Bad: Unnecessary conversions
output_path = str(paths.output) + "/resume.pdf"  # Use Path /
raise Error(f"Failed: {str(output_path)}")  # Path works in f-strings
```

### Paths Dataclass

The `Paths` dataclass stores all paths as `Path` objects:
- Immutable (`frozen=True`).
- Type-safe.
- Supports pathlib operations.

```python
paths = resolve_paths(data_dir="resume_private")
output_file = paths.output / "resume.pdf"  # Path operations
```
