# Easy CV

Create a `pdf` CV based on some `html` templates and data from `yaml`.

Screenshot of the result:
![home](assets/preview.jpg)

You can view the full pdf [here](assets/sample.pdf).

## Installation

### 0. Install with uv

This project uses [uv](https://github.com/astral-sh/uv) for package management. First, install uv:

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

Then install the project dependencies:

```bash
uv sync
```

### 1. Install additional development tools (optional)

For development, you can install additional tools:

```bash
uv sync --group utils
```

### 2. Install [wkhtmltopdf](https://wkhtmltopdf.org/)

## Usage

### 1. Create your CVs

Copy `input/sample_1.yaml` and rename it to whatever you like. For example `input/cv1.yaml`.

### 2. Start Flask
Start the `flask` server from the root folder with:

```bash
uv run python src/cv/index.py
```

### 3. Preview the result
Open `http://localhost:5000/` to preview the result

You can also view any file (like `cv1.yml`) from the `input` folder with the url `http://localhost:5000/v/cv1`.

### 4. Create the pdf

To create the pdf for all `yaml` files inside the `input/` folder run from the main path:

```bash
uv run python src/cv/generate_pdf.py
```

> You should change the `wkhtmltopdf` path inside `config.py` and/or `create_sample.sh`.

> Also you need to have `flask` running

## Development with uv

### Common uv commands

```bash
# Install dependencies
uv sync

# Install with optional development dependencies
uv sync --group utils

# Run scripts
uv run python src/cv/index.py
uv run python src/cv/generate_pdf.py

# Run tests (if available)
uv run pytest

# Run linting and formatting
uv run ruff check src/cv/          # Lint code
uv run ruff format src/cv/         # Format code
uv run ruff check --fix src/cv/    # Auto-fix linting issues

# Run type checking
uv run mypy src/cv/                # Static type checking
uv run ty src/cv/                  # Runtime type checking

# Add a new dependency
uv add flask
uv add --group utils ruff mypy ty  # for dev dependencies
```

### Makefile commands

This project includes a Makefile for common development tasks:

```bash
# Install all dependencies
make install

# Run linting
make lint

# Format code
make format

# Auto-fix linting issues
make lint-fix

# Run type checking (both mypy and ty)
make typecheck

# Run all checks (lint + typecheck)
make check-all

# Format code and fix auto-fixable issues
make fix-all

# Run the Flask development server
make run-server

# Generate PDFs
make generate-pdf

# Clean up cache and build files
make clean

# Set up development environment
make dev-setup

# Run CI checks
make ci

# See all available commands
make help
```

### Ruff Integration

This project uses [Ruff](https://github.com/astral-sh/ruff) as an extremely fast linter and formatter, replacing pylint, mypy, and black for better performance.

#### Key Ruff Features:
- **10-100x faster** than pylint and mypy
- **Integrated linter and formatter** in one tool
- **Drop-in replacement** for black, isort, pylint, and many other tools
- **Excellent IDE integration** with real-time feedback

#### Common Ruff Commands:
```bash
# Check for linting issues
uv run ruff check src/cv/

# Format code
uv run ruff format src/cv/

# Auto-fix issues where possible
uv run ruff check --fix src/cv/

# Run both check and format
uv run ruff check src/cv/ && uv run ruff format src/cv/

# See available rules
uv run ruff rule --all

# Explain a specific rule
uv run ruff rule PLR0913
```

### Type Checking with mypy and ty

This project uses both **mypy** (static type checker) and **ty** (runtime type checker) for comprehensive type safety:

#### Type Checker Features:
- **mypy**: Fast static type checking that catches type errors before runtime
- **ty**: Runtime type validation that ensures correct types during execution
- **Comprehensive coverage**: Catches both static and runtime type issues

#### Type Checking Commands:
```bash
# Run static type checking
uv run mypy src/cv/

# Run runtime type checking
uv run ty src/cv/

# Run both type checkers
make typecheck

# Run all checks (lint + typecheck)
make check-all
```

#### Type Configuration:
- **Strict type checking**: Enabled with `disallow_untyped_defs = true`
- **Python 3.10+**: Targeted version for type annotations (Ubuntu 22.04 LTS default)
- **Library compatibility**: Configured to handle external libraries (oyaml, weasyprint, flask)

### Virtual environment

uv automatically creates and manages a virtual environment. You can activate it manually:

```bash
source .venv/bin/activate  # On macOS/Linux
.venv\Scripts\activate     # On Windows
```

## Configuration
There are two files to `input/sample_1.yaml` and `src/config.yaml`.

The first one (`sample_1.yaml`) has the actual content of the CV.
The second (`config.yaml`) allow users to change some parts of the template.

If you want further configuration you can edit the templates (`src/templates/base.html` and `src/templates/cv.html`) directly or create your own templates (recommended).

## Authors
* [Arnau Villoro](villoro.com)

## License
The content of this repository is licensed under a [MIT](https://opensource.org/licenses/MIT).
