# Markdown Guide for CV Content

This guide explains how to use Markdown in your CV YAML files.

## Supported Features

- **Bold**: `**text**`
- *Italic*: `*text*`
- Links: `[text](url)`
- Headers: `# h1`, `## h2`, etc.

### Code Blocks

Use fenced code blocks with language identifiers for syntax highlighting.

```yaml
description: |
  ```python
def fetch_data(url):
    response = requests.get(url)
    return response.json()
```

```yaml

### Tables

Use tables for skills, experience, or other structured data.

```yaml
description: |
  | Technology | Level | Experience |
  |------------|-------|------------|
  | Python     | Expert| 5+ years   |
  | Docker     | Expert| 4 years    |
```

**Note**: Table separator lines (`---`) must be present for all columns.

### Lists

Use bulleted lists for achievements and responsibilities.

```yaml
description: |
  - Increased sales by 45% through strategic partnerships.
  - Reduced operational costs by 30% by optimizing processes.
```

## Best Practices

### Technical CVs

1. **Code Blocks**: Use correct language identifiers (`python`, `javascript`, `bash`).
2. **Tables**: Include quantifiable metrics.
3. **Skills**: Be specific about expertise (e.g., "Expert: 5+ years, multiple production projects").

### Business CVs

1. **Quantify Results**: Use numbers and metrics (e.g., "+45%", "$200K savings").
2. **Action Verbs**: Start bullet points with strong verbs (e.g., "Managed," "Led," "Developed").
3. **Currency**: Use standard symbols (`$`, `€`, `£`).

## Common Pitfalls

### Table Formatting

A common mistake is forgetting the separator line for the last column.

❌ **Incorrect**:

```markdown
| Feature | Status |
|---------|
| Testing | Complete |
```

✅ **Correct**:

```markdown
| Feature | Status |
|---------|--------|
| Testing | Complete |
```

### Indentation

Preserve indentation within code blocks.

❌ **Incorrect**:

```python
def example():
    print("Mismatched indentation")
```

✅ **Correct**:

```python
def example():
    print("Correct indentation")
```

## Markdown Implementation

The CV generator uses Python's `markdown` library with the following extensions:

- `fenced_code`
- `tables`
- `codehilite`
- `nl2br`
- `attr_list`
