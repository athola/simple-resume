# Markdown Guide for Resume Content

This guide explains how to use Markdown to add rich formatting to the content of your resume.

## Supported Features

-   **Bold**: `**text**`
-   *Italic*: `*text*`
-   Links: `[text](url)`
-   Headers: `# h1`, `## h2`
-   Fenced code blocks: ` ```python `
-   Tables
-   Bulleted lists

## Formatting Your Projects

The `Projects` section is a great place to showcase your personal or open-source work.

### Example

```yaml
Projects:
  -
    start: ""
    end: 2024
    title: "My Awesome Project"
    title_link: "https://github.com/username/repo-name"
    company: "Personal Project"
    company_link: "https://github.com/username"
    description: |
      Reduced latency by 75% by implementing a caching layer.

      - Developed a Python script to process and aggregate data.
      - Deployed the application using Docker and Kubernetes.
      - **Tech Stack:** Python, Docker, Kubernetes
```

### Tips for Writing Great Project Descriptions

-   Lead with measurable results (e.g., "Reduced latency by 75%").
-   Link to your code or a live demo.
-   Include a "Tech Stack" line to highlight the technologies you used.

## General Formatting Tips

-   **Use code blocks** with language identifiers (e.g., `python`, `javascript`) to get syntax highlighting in the HTML version of your resume.
-   **Quantify your accomplishments** with specific numbers (e.g., "Reduced latency by 45%", "Increased revenue by $200K").
-   **Start bullet points with action verbs** that describe the outcome of your work (e.g., "Automated testing, which reduced bug reports by 20%").

## How It Works

We use the `markdown` Python library with extensions for fenced code blocks, tables, and syntax highlighting to render your Markdown content.