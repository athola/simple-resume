# Markdown Guide

This guide explains how to use Markdown to format the content of your resume.

## Supported Features

The following Markdown features are supported:

-   **Bold**
-   *Italic*
-   Links
-   Headers
-   Fenced code blocks
-   Tables
-   Bulleted lists

## Formatting the Projects Section

The `Projects` section is for showcasing personal or open-source work.

### Example

```yaml
Projects:
  -
    # The start and end dates of the project.
    start: ""
    end: 2024
    # The title of the project.
    title: "My Awesome Project"
    # A link to the project's repository or website.
    title_link: "https://github.com/username/repo-name"
    # The name of the company or organization.
    company: "Personal Project"
    # A link to the company's website.
    company_link: "https://github.com/username"
    # A description of the project.
    description: |
      Reduced latency by 75% by implementing a caching layer.

      - Developed a Python script to process and aggregate data.
      - Deployed the application using Docker and Kubernetes.
      - **Tech Stack:** Python, Docker, Kubernetes
```

### Recommendations

-   Quantify your results (e.g., "Reduced latency by 75%").
-   Include links to code repositories or live demos.
-   Highlight the technologies you used with a "Tech Stack" line.

## General Formatting Tips

-   Use code blocks with language identifiers (e.g., `python`, `javascript`) to enable syntax highlighting in the HTML version of your resume.
-   Quantify your accomplishments with numbers (e.g., "Reduced latency by 45%", "Increased revenue by $200K").
-   Begin bullet points with action verbs.

## Implementation Details

This project uses the 'markdown' Python library to render Markdown. We enable the 'fenced_code', 'tables', and 'codehilite' extensions.
