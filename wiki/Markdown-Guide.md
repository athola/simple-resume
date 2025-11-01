# Markdown Guide for Resume Content

Use Markdown to format the content of your Resume YAML files.

## Supported Features

- **Bold**: `**text**`
- *Italic*: `*text*`
- Links: `[text](url)`
- Headers: `# h1`, `## h2`
- Fenced code blocks (e.g., ` ```python `)
- Tables
- Bulleted lists

## Projects Section

Use the `Projects` section for personal or open-source work.

### Structure

```yaml
Projects:
  -
    start: ""
    end: 2024
    title: Project Name
    title_link: https://github.com/username/repo-name
    company: Personal Project
    company_link: https://github.com/username
    description: |
      Reduced latency by 75% by implementing a caching layer.

      - Developed a Python script to process and aggregate data.
      - Deployed the application using Docker and Kubernetes.
      - **Tech Stack:** Python, Docker, Kubernetes
```

### Guidelines

- Start with measurable results (e.g., "Reduced latency by 75%")
- Link to repositories or live demos
- Use a "Tech Stack" line to list key technologies
- Choose projects relevant to your target role

## Formatting Tips

- **Code Blocks**: Use language identifiers (e.g., `python`, `javascript`) for syntax highlighting.
- **Tables**: Use for structured data like benchmarks.
- **Metrics**: Quantify results with numbers (e.g., "+45%", "$200K savings").
- **Action Verbs**: Start bullet points with strong verbs (e.g., "Managed," "Led").

## Common Issues

- **Table Formatting**: Ensure the separator line (`---`) is present for all columns.
- **Indentation**: Preserve indentation within code blocks.

## Implementation

The Resume generator uses Python's `markdown` library with extensions for fenced
code blocks, tables, and syntax highlighting.
