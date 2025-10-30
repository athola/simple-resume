# EasyResume

Turn structured YAML into polished, print-ready resumes using pure Python and WeasyPrint.

![Generated resume preview](assets/preview.jpg)

The full sample PDF lives in `assets/sample.pdf`.

## Highlights

- Generate PDFs from templated HTML with a single command.
- Leverage Markdown inside YAML entries for rich formatting (bold, links, tables, code blocks).
- Ship-ready automation: CI, type checking, linting, and security scans are wired up out of the box.

## Documentation

All project guides live in the repo wiki (mirroring the GitHub wiki at <https://github.com/athola/easyresume/wiki>):

- `wiki/Markdown-Guide.md` – author Markdown-rich CV content.
- `wiki/Color-Schemes.md` – customize colors with preset themes or create your own.
- `wiki/Workflows.md` – understand the CI/CD pipeline and quality gates.

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

1. Copy `sample/input/sample_1.yaml` into your data directory and replace the
   placeholder content with your own information.
2. Customize colors by editing the `config` section in your YAML file (see
   `wiki/Color-Schemes.md` for preset themes).
3. Generate HTML resumes: `uv run python src/easyresume/generate_html.py`.
   - Pass `--open` (optionally `--browser firefox`) to launch in Firefox or Chromium.
4. Generate PDFs for every YAML file:
   `uv run python src/easyresume/generate_pdf.py`.
   - Pass `--open` to launch each PDF with your system viewer
     (`xdg-open`/`open`/`start`).

Configuration values (input/output locations, URLs) live in `src/easyresume/config.py`.

## Development

- `make install` – install dependencies (including tooling extras).
- `make test` – run the full pytest suite.
- `make lint` / `make format` – lint and format with Ruff.
- `make typecheck` – run mypy and ty.
- `make generate-pdf` – create PDFs using the configured data directory.
  - For HTML output, run `uv run generate-html`.

See `wiki/Workflows.md` for the full CI matrix and quality gates.

## Contributing

Issues and pull requests are welcome. Please review the wiki guidelines and
ensure all tests and linters pass before opening a PR.

## License

This project is released under the [MIT License](https://opensource.org/licenses/MIT).
