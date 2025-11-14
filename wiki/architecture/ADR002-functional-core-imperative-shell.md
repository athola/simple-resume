# ADR-002: Functional Core, Imperative Shell

## Status
**Accepted** (2025-11-09) - Implementation ongoing with strategy pattern refactoring (2025-11-12)

## Context
The original `simple-resume` design mixed file I/O, CLI orchestration, and domain logic across modules like `utilities`, `hydration`, and `generation`. This coupling caused brittle tests, slow code reviews, and cascading changes.

Specific areas of concern included:

1. **PDF Generation**: The `Resume.to_pdf()` method (lines 217-305) was 88 lines of code handling multiple concerns including validation, path resolution, PDF generation, and error handling.

2. **Configuration Processing**: The `_apply_palette_block()` function (lines 207-276) in utilities.py contained deeply nested conditional logic mixing configuration validation with I/O operations.

3. **Mixed Responsibilities**: CLI logic, file I/O, and business logic were tightly coupled across multiple modules, making unit testing difficult and changes risky.

To fix this, we are adopting the "functional core, imperative shell" pattern to separate pure, deterministic logic from I/O and other side effects.

## Decision

1. **Define Shell Boundaries**: Place all code interacting with the outside world (e.g., filesystem access, YAML parsing, CLI I/O, LaTeX subprocesses) in "shell" modules. The shell's responsibility is to sequence operations, handle retries, log events, and translate external data into simple data structures for the core.

2. **Implement a Pure Core**: Core modules will contain only pure functions that operate on simple data structures (e.g., `GeneratePlanOptions -> list[GenerationCommand]`, `hydrate_resume(raw) -> dict`). These functions must not access the filesystem, environment variables, or other global state.

3. **Adopt Incrementally**: Refactor incrementally, starting with frequently changing code. Each step must preserve existing behavior, add fast unit tests for the new core logic, and keep the shell a thin adapter over the core.

4. **Use a Shared Command Model**: Communication between adapters (e.g., CLI) and core uses explicit command objects. This makes orchestration logic transparent and simplifies adding new adapters.

5. **Implement Strategy Pattern for Complex Operations**: For areas like PDF generation and configuration processing, use the Strategy pattern to further separate concerns:

#### PDF Generation Strategy
- **Extract**: `PdfGenerationStrategy` abstract base class with `WeasyPrintStrategy` and `LatexStrategy` implementations
- **Orchestrate**: `PdfGenerationOrchestrator` to manage strategy selection and execution flow
- **Simplify**: Reduce `Resume.to_pdf()` method from 88 lines to 25 lines by delegating to orchestrator

#### Configuration Processing Strategy
- **Extract**: Pure helpers in `core.config_core` encapsulate palette resolution, layout defaults, and validation without touching the filesystem
- **Chain**: Color + palette processing flows through `_process_palette_colors() -> apply_palette_block() -> finalize_config()`, giving us an explicit pipeline
- **Separate**: Color math and WCAG thresholds now live in `core.colors` / `ColorCalculationService`, with I/O helpers moved into `simple_resume.utils.io`

## Rationale

- **Moving planning logic into a pure core** makes it easier and safer to unit-test than the previous CLI-dependent code
- **Explicit command objects** eliminate duplicated logic (e.g., for format iteration and overrides) and provide a single, clear interface
- **Strategy pattern** provides the best balance of separation, testability, and discoverability while maintaining backward compatibility
- **Incremental approach** avoids large-scale rewrite risks while delivering immediate benefits
- **Clear boundaries** between functional core and imperative shell improve maintainability and testability

## Alternatives Considered

1. **Keep existing monolithic implementation**
   - *Pros*: No refactoring effort required
   - *Cons*: Continued maintenance burden, poor testability, high cognitive load

2. **Extract to smaller methods within same class**
   - *Pros*: Simpler refactoring
   - *Cons*: Still mixes concerns, doesn't improve testability significantly

3. **Create separate service classes**
   - *Pros*: Clean separation
   - *Cons*: More complex dependency management, harder to discover

4. **Large-scale rewrite**
   - *Pros*: Complete architectural reset
   - *Cons*: High risk, long timeline, potential for lost functionality

**Chosen approach**: Combined functional core/imperative shell with strategy pattern provides the best balance of separation, testability, and discoverability while maintaining backward compatibility and allowing incremental adoption.

## Consequences

### Positive Impacts
- **Improved Testability**: Core business logic can now be tested independently of I/O operations
- **Reduced Complexity**: `Resume.to_pdf()` method reduced from 88 to 25 lines (72% reduction)
- **Better Separation**: Configuration processing logic separated from validation and I/O
- **Enhanced Maintainability**: Strategy pattern makes it easier to add new PDF backends or configuration processors
- **Cleaner Architecture**: Clear boundaries between functional core and imperative shell
- **CLI change planning logic** in `build_generation_plan` allows testing single and batch operations without filesystem access
- **New unit tests** for core logic (e.g., `tests/unit/core/test_generation_plan.py`) are fast, providing high coverage of decision-making logic
- **Explicit command objects** eliminate duplicated logic and provide a single, clear interface

### Negative Impacts
- **Increased File Count**: Added new files for strategy implementations and core modules
- **Import Complexity**: Required careful management of circular imports
- **Learning Curve**: Team needs to understand Strategy pattern and functional core concepts
- **Shell module complexity**: Shell modules still contain considerable printing and error-handling logic, which may lead to duplication
- **Mixed patterns**: Until refactoring is complete, developers must work with both legacy code and new patterns

### Technical Details
- **Backward Compatibility**: All existing APIs maintained unchanged
- **Performance**: No measurable performance impact on PDF generation
- **Error Handling**: Preserved existing error handling patterns
- **Type Safety**: Maintained strong type hints throughout
- **Incremental Adoption**: Pattern can be applied module by module without disrupting existing functionality

## Implementation Details

### Files Modified
- `src/simple_resume/core/resume.py`: Refactored `to_pdf()` method to use strategy pattern
- `src/simple_resume/utilities.py`: Extracted configuration processing logic
- Various CLI and shell modules to use new core functions

### Files Added / Refactored
- `src/simple_resume/core/pdf_generation_strategy.py`: Houses the Strategy/Orchestrator types extracted from `Resume.to_pdf()`
- `src/simple_resume/core/config_core.py`: Refactored to contain the pure configuration pipeline (`prepare_config`, `apply_palette_block`, `finalize_config`)
- `src/simple_resume/core/color_service.py`: Introduces `ColorCalculationService` relied on by the config pipeline
- `src/simple_resume/utils/io.py` and `src/simple_resume/utils/colors.py`: Path-handling helpers plus backwards-compatible shims
- `src/simple_resume/session/`: New session management module following functional core pattern
- `src/simple_resume/core/generation_plan.py`: Command generation logic extracted from CLI

### Key Classes
```python
# PDF Generation Strategy Pattern
abstract PdfGenerationStrategy
├── WeasyPrintStrategy
└── LatexStrategy
└── (future) HeadlessBatchStrategy

# Configuration Pipeline Helpers
core.config_core.prepare_config()
    → apply_palette_block()
    → finalize_config()
    → ColorCalculationService (sidebar/icon color decisions)

# Generation Commands
GeneratePlanOptions -> list[GenerationCommand]
├── SingleResumeCommand
└── BatchResumeCommand

# Orchestrators
├── PdfGenerationOrchestrator
└── shell.generation execution wrapper
```

## Monitoring
- **Test Coverage**: Target >85% coverage for new strategy classes, >90% for core modules
- **Performance**: Monitor PDF generation time before/after refactoring
- **Code Quality**: Reduced cyclomatic complexity in affected methods
- **Development Velocity**: Measure time required to implement new CLI features, targeting 20-30% reduction
- **Bug Detection**: Track whether explicit command objects help identify edge cases earlier

## Follow-up Tasks

1. **Continue Refactoring**: Complete refactoring of `utilities` and `hydration` modules into pure functions with shell adapters
2. **Session Management**: Apply pattern to session management and stateful operations
3. **Shared Execution**: Create shared command execution helpers for other entry points (e.g., session API, potential future HTTP services)
4. **Documentation**: Update onboarding documentation with checklist for creating new core and shell modules
5. **Template System**: Apply pattern to template processing and rendering pipeline

## Related ADRs
- **[ADR-001]**: WeasyPrint sidebar pagination fix (PDF strategy supports this)
- **[ADR-003]**: API surface design (builds on functional core pattern)
- **[ADR-007]**: Color palette system (integrates with core color service)
- **[ADR-008]**: Constants consolidation (follows same separation principles)
- **Future**: Template system architecture ADR should reference this pattern

## Documentation
This ADR is maintained alongside the `Functional-Core-Shell-Inventory.md` to document architecture progress and track the new pure modules (`core.pdf_generation_strategy`, `core.config_core`, `session/`) so we can quantify progress.

## Author
- **Primary**: Development Team
- **Initial Date**: 2025-11-09
- **Updated**: 2025-11-12 (Strategy pattern implementation)
- **Review Status**: Accepted and implementation ongoing

---

*This ADR documents the successful adoption of the functional core, imperative shell pattern to improve maintainability, testability, and development velocity while preserving all existing functionality.*
