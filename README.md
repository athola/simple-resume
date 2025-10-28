# Easy CV

Turn structured YAML into polished, print-ready resumes using Flask and WeasyPrint.

![Generated resume preview](assets/preview.jpg)

The full sample PDF lives in `assets/sample.pdf`.

## Highlights

- Generate consistent PDFs from templated HTML with a single command.
- Leverage Markdown inside YAML content for rich formatting.
- Ship-ready automation: CI, type checking, and linting configured out of the box.

## Documentation

All project guides are maintained in the repo wiki (mirroring the GitHub wiki at <https://github.com/athola/cv/wiki>):

- `wiki/Markdown-Guide.md` – author Markdown-rich CV content.
- `wiki/Workflows.md` – understand the GitHub Actions pipeline.

## Installation

We use [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install dependencies
uv sync

# (Optional) install tooling extras
uv sync --group utils
```

You also need a local copy of [wkhtmltopdf](https://wkhtmltopdf.org/).

## Quick Start

1. Copy `sample/input/sample_1.yaml` into your data directory and adjust the content.
2. Start the preview server: `uv run python src/cv/index.py` then visit `http://localhost:5000/`.
3. Generate PDFs for every YAML file: `uv run python src/cv/generate_pdf.py`.

Configuration values (input/output locations, URLs) live in `src/cv/config.py`.

## Development

- `make install` – install dependencies (including tooling extras).
- `make test` – run the full pytest suite.
- `make lint` / `make format` – lint and format with Ruff.
- `make typecheck` – run mypy and ty.
- `make generate-pdf` – create PDFs using the configured data directory.

See `wiki/Workflows.md` for the full CI matrix and quality gates.

## Contributing

Issues and pull requests are welcome. Please review the wiki guidelines and ensure all tests
and linters pass before opening a PR.

## License

This project is released under the [MIT License](https://opensource.org/licenses/MIT).
