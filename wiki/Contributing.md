# Contributing Guide

Contribute to the `simple-resume` project by reporting bugs, suggesting features, or submitting code improvements.

## Reporting Bugs and Suggesting Features

Report bugs and feature suggestions by opening a GitHub issue.

-   **[Report a bug](https://github.com/athola/simple-resume/issues)**: Provide a detailed description of the bug and steps to reproduce it.
-   **[Suggest a feature](https://github.com/athola/simple-resume/issues/new?template=feature_request.md)**: Describe your idea and explain why it would be a good addition to the project.

## Contributing Code

To contribute code:

1.  Fork the repository and clone it to your local machine.
2.  Create a new branch for your changes.
3.  Set up your development environment by following the [Development Guide](Development-Guide.md).
4.  Make your changes, and add tests and documentation as needed.
5.  Run code quality checks to verify the changes adhere to the project's style and pass all tests.

    ```bash
    make check-all
    make validate
    ```

6.  Push your changes to your fork and open a pull request against the `main` branch.

### Commit Signing Requirement

All commits must be GPG-signed so GitHub can mark them as **Verified**. Configure
your signing key before opening a pull request:

```bash
# Export or create a key, then tell git which one to use
git config user.signingkey <YOUR_KEY_FINGERPRINT>

# Sign every commit in this repo by default
git config commit.gpgsign true

# Optional: ensure the right GPG program is used (gpg vs gpg2)
git config gpg.program gpg
```

Make sure the corresponding public key is uploaded to your GitHub account under
**Settings → SSH and GPG keys**. If you use a hardware token or SSH signing,
follow GitHub's [official guide](https://docs.github.com/authentication/managing-commit-signature-verification)
to register the signer. Commits without a trusted signature will be blocked from
merging.

## Development Guidelines

-   **Code Style**: This project uses `ruff` for linting and formatting. Run `make format` before committing your changes, and maintain consistency with the existing code style.
-   **Tests**: New features must be accompanied by tests. Bug fixes must include a test that demonstrates the bug and its resolution.
-   **Documentation**: All new or changed features must be documented.
-   **Shell Scripts**: Shell scripts must follow POSIX standards (`/bin/sh` compatible) unless Bash features are explicitly required. All shell scripts must:

    - Include a shebang (`#!/usr/bin/env sh` or `#!/usr/bin/env bash`)
    - Set safety flags: `set -euo pipefail`
    - Quote all variable expansions: `"$VAR"` not `$VAR`
    - Use `|| true` or explicit exit code handling when pipeline failure is acceptable
    - Avoid Windows-specific syntax (backslash continuation, `.exe` paths, `C:\` paths)
    - Use `$(command)` for command substitution, not backticks

    Example:
    ```bash
    #!/usr/bin/env sh
    set -euo pipefail

    main() {
        input_file="${1:-default.yaml}"
        output_dir="${2:-output}"

        if ! [ -f "$input_file" ]; then
            echo "Error: Input file not found: $input_file" >&2
            exit 1
        fi

        process_file "$input_file" "$output_dir"
    }

    main "$@"
    ```

## Code Review Checklist

When submitting or reviewing code, verify the following items:

### Functional Core, Imperative Shell (FCIS) Compliance

Per [ADR-002](architecture/ADR002-functional-core-imperative-shell.md):

- [ ] **Core Layer Purity**: Core modules (`src/simple_resume/core/`) contain only pure functions with no I/O or side effects
- [ ] **No Core→Shell Dependencies**: Core modules do not import from shell layer (verify with: `grep -r "from simple_resume.shell" src/simple_resume/core/`)
- [ ] **I/O in Shell Layer**: File I/O, network requests, and subprocess calls are in shell layer (`src/simple_resume/shell/`)
- [ ] **Data Flow**: Data flows from shell → core → shell, never the reverse
- [ ] **Testing**: Core logic is tested independently of I/O operations

### Error Handling Patterns

Per [ADR-006](architecture/ADR006-error-handling-strategy.md):

- [ ] **Exception Hierarchy**: All exceptions inherit from `SimpleResumeError`, not built-in exceptions
- [ ] **Two-Tier Pattern**: Validation provides both `validate()` (inspection) and `validate_or_raise()` (action)
- [ ] **Rich Context**: Exceptions include relevant context (file paths, config keys, operation names)
- [ ] **Exception Chaining**: Use `from exc` when wrapping exceptions
- [ ] **No Palette Exception Isolation**: Palette exceptions now inherit from `PaletteError(SimpleResumeError)`, not `RuntimeError`
- [ ] **Import from Main Exceptions**: Use `from simple_resume.core.exceptions import PaletteError`, not `from simple_resume.core.palettes.exceptions`

### Code Quality

- [ ] **Type Hints**: All public functions have complete type annotations
- [ ] **Docstrings**: Public functions and classes have descriptive docstrings
- [ ] **No Dead Code**: Remove commented-out code and unused imports
- [ ] **Test Coverage**: New code has tests; coverage remains above 85%

### API Stability

Per [ADR-003](architecture/ADR003-api-surface-design.md) and [API Stability Policy](API-Stability-Policy.md):

- [ ] **Public API**: New public symbols are added to `__init__.__all__`
- [ ] **Breaking Changes**: Document breaking changes in changelog
- [ ] **Deprecation**: Use `DeprecationWarning` for deprecated features
- [ ] **Core Privacy**: Internal modules (`core.*`, `shell.*`) are considered private

## Shell Module Complexity Monitoring

Per [ADR-002](architecture/ADR002-functional-core-imperative-shell.md), shell modules naturally accumulate complexity due to I/O handling. Monitor for:

### Warning Signs

- **Duplication**: Repeated error handling patterns across shell modules
- **Long Functions**: Shell functions exceeding 50 lines may need refactoring
- **Mixed Concerns**: Shell modules containing business logic that should be in core
- **Tight Coupling**: Shell modules that depend heavily on other shell modules

### Mitigation Strategies

1. **Extract Common Patterns**: Create shared utilities in `shell/utils/` for repeated patterns
2. **Strategy Pattern**: For complex operations, use strategy pattern (see PDF generation)
3. **Protocol-Based Design**: Use protocols to define contracts between components
4. **Regular Refactoring**: Address complexity during feature development, not as separate work

## Onboarding Checklist for New Contributors

### Understand the Architecture

1. **Read Key ADRs**:
   - [ADR-002: Functional Core, Imperative Shell](architecture/ADR002-functional-core-imperative-shell.md) - Core architecture pattern
   - [ADR-003: API Surface Design](architecture/ADR003-api-surface-design.md) - Public API organization
   - [ADR-006: Error Handling Strategy](architecture/ADR006-error-handling-strategy.md) - Exception hierarchy

2. **Review Project Structure**:
   - [Architecture Guide](Architecture-Guide.md) - Overall architecture overview
   - [Functional Core, Imperative Shell Inventory](architecture/Functional-Core-Shell-Inventory.md) - Module classification
   - [Shell Layer APIs](Shell-Layer-APIs.md) - Shell layer interfaces

3. **Understand Data Flow**:
   - Core layer: Pure data transformations (no I/O)
   - Shell layer: I/O operations, external dependencies
   - Dependency flow: Shell depends on Core, never the reverse

### Development Workflow

1. **Set Up Environment**: Follow [Development Guide](Development-Guide.md)
2. **Run Tests**: `make test` for unit tests, `make test-all` for full suite
3. **Code Quality**: `make format && make lint && make typecheck`
4. **Build Verification**: `make build` to ensure package builds correctly

### Creating New Modules

When adding new modules, determine their placement:

| Module Type | Location | Characteristics |
|-------------|----------|-----------------|
| **Pure Functions** | `src/simple_resume/core/` | No I/O, no external dependencies, testable without mocks |
| **Data Models** | `src/simple_resume/core/models.py` | Frozen dataclasses, immutable |
| **I/O Operations** | `src/simple_resume/shell/` | File access, network calls, subprocesses |
| **CLI Commands** | `src/simple_resume/shell/cli/` | User interface, argument parsing |

### Common Patterns

- **Factory Methods**: Use `Resume.read_yaml()` pattern for data loading
- **Strategy Pattern**: Use for pluggable algorithms (PDF generation, ATS scoring)
- **Repository Pattern**: Use for data access abstraction (see `ResumeRepository`)
- **Dependency Injection**: Use protocols to define contracts, enable testing

### Getting Help

- **Architecture Questions**: Reference relevant ADRs first
- **Bug Reports**: Include reproduction steps and error messages
- **Feature Proposals**: Describe use case and proposed implementation
- **Code Review**: Address all checklist items before requesting review
