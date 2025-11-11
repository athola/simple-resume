# Markdown Guide

This guide explains Markdown usage for resume content formatting.

## Supported Features

Supported Markdown features:

-   **Bold**
-   *Italic*
-   Links
-   Headers
-   Fenced code blocks
-   Tables
-   Bulleted lists

## Formatting the Projects Section

The `Projects` section showcases personal or open-source work.

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

### Recommendations

-   Quantify results (e.g., "Reduced latency by 75%").
-   Include links to code or live demos.
-   Highlight technologies used with a "Tech Stack" line.

## General Formatting Tips

-   Use code blocks with language identifiers (e.g., `python`, `javascript`) for syntax highlighting in the HTML resume.
-   Quantify accomplishments with numbers (e.g., "Reduced latency by 45%", "Increased revenue by $200K").
-   Start bullet points with action verbs.

## Implementation Details

This project uses the `markdown` Python library with extensions for fenced code blocks, tables, and syntax highlighting to render Markdown.
