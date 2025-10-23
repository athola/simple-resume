# Markdown Guide for CV Content

This guide explains how to use markdown formatting in your CV YAML files to create rich, professional content.

## Supported Markdown Features

### Basic Formatting

- **Bold text**: Use `**text**` for **bold emphasis**
- *Italic text*: Use `*text*` for *italic emphasis*
- Links: Use `[link text](url)` format
- Headers: Use `# Header 1`, `## Header 2`, etc.

### Code Blocks (Technical CVs)

For technical CVs, you can include code blocks with syntax highlighting:

```yaml
description: |
  ## Python Development

  Here's an example function:

  ```python
  import requests

  def fetch_data(url):
      """Fetch data from API endpoint."""
      response = requests.get(url)
      return response.json()
  ```
```

**Result**: Code will be displayed with proper syntax highlighting and formatting.

### Tables (Business & Technical CVs)

Create professional tables for skills, experience, education, or project details:

```yaml
description: |
  ## Technical Skills

  | Technology | Level | Experience | Projects |
  |------------|-------|------------|----------|
  | Python | Expert | 5+ years | 15+ projects |
  | Docker | Expert | 4 years | 20+ containers |
  | AWS | Advanced | 3 years | 5+ deployments |
```

**Important**: Table separator lines must have dashes (`---`) for ALL columns, including the last one.

### Lists

Use bullet points for achievements, responsibilities, or skills:

```yaml
description: |
  ## Key Achievements

  - **Revenue Growth**: Increased sales by 45% through strategic partnerships
  - **Cost Reduction**: Reduced operational costs by 30% through process optimization
  - **Team Leadership**: Managed team of 12+ professionals
```

## Best Practices

### For Technical CVs

1. **Code Blocks**: Use proper language identifiers for syntax highlighting
   - ` ```python ` for Python code
   - ` ```javascript ` for JavaScript
   - ` ```bash ` for shell commands

2. **Technical Tables**: Include metrics and quantifiable achievements
   ```yaml
   | Project | Technology | Performance | Impact |
   |---------|------------|-------------|--------|
   | API Redesign | FastAPI | 10x faster | $50K savings |
   ```

3. **Skill Levels**: Be specific about expertise levels
   - Expert: 5+ years, multiple production projects
   - Advanced: 3-5 years, independent contributor
   - Intermediate: 1-3 years, requires guidance

### For Business CVs

1. **Quantifiable Results**: Always include numbers and metrics
   ```yaml
   | Achievement | Metric | Period |
   |-------------|--------|--------|
   | Sales Growth | +45% | Q4 2023 |
   | Cost Savings | $200K | 2023 |
   ```

2. **Action Verbs**: Start bullet points with strong action verbs
   - **Managed**, **Led**, **Developed**, **Implemented**
   - **Increased**, **Reduced**, **Optimized**, **Streamlined**

3. **Currency Formatting**: Use standard currency symbols
   - `$500K` for USD amounts
   - `€250K` for EUR amounts
   - `£100K` for GBP amounts

## Common Pitfalls

### Table Formatting

❌ Incorrect (missing dashes for last column):
```markdown
| Feature | Status |
|---------|--------|
| Testing | Complete |
```

✅ Correct (dashes for all columns):
```markdown
| Feature | Status |
|---------|--------|
| Testing | Complete |
```

### Code Block Indentation

❌ Incorrect (inconsistent indentation):
```markdown
```python
def example():
  print("Hello")
```
```

✅ Correct (proper indentation):
```markdown
```python
def example():
    print("Hello")
```
```

### Special Characters

For currency symbols and special characters in tables, they work automatically:

```yaml
description: |
  | Budget | Amount | Currency |
  |--------|--------|----------|
  | Project A | $500K | USD |
  | Project B | €250K | EUR |
```

## Examples

### Technical CV Example

```yaml
Projects:
  - title: "API Development"
    description: |
      ## RESTful API Development

      Developed a high-performance API using FastAPI:

      ```python
      from fastapi import FastAPI

      app = FastAPI()

      @app.get("/api/v1/data")
      async def get_data():
          return {"status": "success"}
      ```

      ### Performance Metrics

      | Metric | Before | After | Improvement |
      |--------|--------|-------|-------------|
      | Response Time | 500ms | 50ms | 90% faster |
      | Throughput | 100 req/s | 1000 req/s | 10x increase |
```

### Business CV Example

```yaml
Experience:
  - company: "Tech Solutions Inc."
    role: "Senior Project Manager"
    duration: "2021-Present"
    description: |
      ## Project Leadership & Results

      Led strategic initiatives that delivered measurable business impact:

      ### Key Achievements

      - **Revenue Growth**: Increased sales by 45% ($2.5M additional revenue)
      - **Cost Optimization**: Reduced operational costs by 30% ($500K annual savings)
      - **Team Expansion**: Grew team from 8 to 15 members while maintaining performance

      ### Project Portfolio

      | Project | Budget | Timeline | ROI | Status |
      |---------|--------|----------|-----|--------|
      | Digital Transformation | $1.2M | 6 months | 250% | Completed |
      | Process Automation | $300K | 3 months | 180% | Completed |
      | Market Expansion | $800K | 12 months | 145% | In Progress |
```

## Testing Your Markdown

To preview how your markdown will render, you can:

1. Use online markdown editors like [Markdown Live Preview](https://markdownlivepreview.com/)
2. Test with the CV generation tools
3. Check the generated HTML output

The CV system uses Python's `markdown` library with these extensions:
- `fenced_code`: For code blocks with language identifiers
- `tables`: For pipe-based tables
- `codehilite`: For syntax highlighting
- `nl2br`: For line break preservation
- `attr_list`: For element attributes

This ensures your markdown content renders as professional, well-formatted HTML in the final CV.