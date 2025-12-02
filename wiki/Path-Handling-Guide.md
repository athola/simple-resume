# Path Handling

`simple-resume` adopts a **path-first principle** for consistent path handling.

1.  Accept `str | Path` at API boundaries for flexibility.
2.  Normalize to `Path` objects immediately after receiving input.
3.  Use `Path` objects internally throughout the codebase.
4.  Convert to `str` only when required by an external API.

### When to Convert to a String

Convert a `Path` object to a string only when an external library requires it.

- **External libraries**: Some external libraries, such as WeasyPrint, require string paths (e.g., `write_pdf(str(output_path))`).
- **Exception messages**: A `Path` object automatically converts to a string when used in an exception message.
- **Error messages**: Use a `Path` object directly in an f-string when building an error message for display.

### Examples

```python
# Good: Accept both `str` and `Path` objects, and normalize early.
def process_file(file_path: str | Path) -> None:
    path = Path(file_path)  # Normalize immediately.
    path.read_text()  # Use Path methods.


# Good: Pass `Path` objects directly.
output_path = paths.output / "resume.pdf"
resume.to_pdf(output_path)  # No conversion is needed.

# Good: Convert to a string only when an external API requires it.
html_doc.write_pdf(str(output_path))  # WeasyPrint requires a string.

# Bad: Unnecessary conversions.
output_path = str(paths.output) + "/resume.pdf"  # Use the / operator instead.
raise Error(f"Failed: {str(output_path)}")  # `Path` objects work in f-strings.
```

### The `Paths` Dataclass

The `Paths` dataclass stores all paths as `Path` objects. It is immutable (`frozen=True`), type-safe, and supports all `pathlib` operations.

```python
paths = resolve_paths(data_dir="resume_private")
output_file = paths.output / "resume.pdf"  # Path operations
```
