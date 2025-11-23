"""Public API namespaces for simple-resume.

This module provides stable, curated API namespaces following the pandas pattern:
- `simple_resume.api.colors` - Color manipulation utilities

Symbols exported from these modules are covered by the stability contract.
Internal implementation details remain in `core.*` modules.

Example:
    >>> from simple_resume.api import colors
    >>> colors.is_valid_color("#FF0000")
    True
    >>> colors.calculate_text_color("#000000")
    '#FFFFFF'

"""

from simple_resume.api import colors

__all__ = ["colors"]
