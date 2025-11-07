# Markdown Guide

This guide explains how to use Markdown for rich formatting in your resume content.

## Supported Features

-   **Bold**
-   *Italic*
-   Links
-   Headers
-   Fenced code blocks
-   Tables
-   Bulleted lists

## Formatting Projects

The `Projects` section is ideal for showcasing personal or open-source work.

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

### Tips

-   Quantify results (e.g., "Reduced latency by 75%").
-   Include links to code or demos.
-   Highlight technology used with a "Tech Stack" line.

## General Formatting

-   Use code blocks with language identifiers (e.g., `python`, `javascript`) for syntax highlighting in HTML resumes.
-   Quantify accomplishments with numbers (e.g., "Reduced latency by 45%", "Increased revenue by $200K").
-   Start bullet points with action verbs that describe outcomes.

## How It Works

We use the `markdown` Python library with extensions for fenced code blocks, tables, and syntax highlighting to render your Markdown.
