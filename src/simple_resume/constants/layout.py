"""Layout and measurement constants for simple-resume."""

from __future__ import annotations

from typing import Final

# Default page dimensions in millimeters
DEFAULT_PAGE_WIDTH_MM: Final[int] = 190
DEFAULT_PAGE_HEIGHT_MM: Final[int] = 270

# Default sidebar width in millimeters
DEFAULT_SIDEBAR_WIDTH_MM: Final[int] = 60

# Default padding values in points/millimeters
DEFAULT_PADDING: Final[int] = 12
DEFAULT_SIDEBAR_PADDING_ADJUSTMENT: Final[int] = -2
DEFAULT_SIDEBAR_PADDING: Final[int] = 12

# Frame padding values
DEFAULT_FRAME_PADDING: Final[int] = 10

# Cover letter specific padding
DEFAULT_COVER_PADDING_TOP: Final[int] = 10
DEFAULT_COVER_PADDING_BOTTOM: Final[int] = 20
DEFAULT_COVER_PADDING_HORIZONTAL: Final[int] = 25

# Validation constraints
MIN_PAGE_WIDTH_MM: Final[int] = 100
MAX_PAGE_WIDTH_MM: Final[int] = 300
MIN_PAGE_HEIGHT_MM: Final[int] = 150
MAX_PAGE_HEIGHT_MM: Final[int] = 400

MIN_SIDEBAR_WIDTH_MM: Final[int] = 30
MAX_SIDEBAR_WIDTH_MM: Final[int] = 100

MIN_PADDING: Final[int] = 0
MAX_PADDING: Final[int] = 50

__all__ = [
    "DEFAULT_PAGE_WIDTH_MM",
    "DEFAULT_PAGE_HEIGHT_MM",
    "DEFAULT_SIDEBAR_WIDTH_MM",
    "DEFAULT_PADDING",
    "DEFAULT_SIDEBAR_PADDING_ADJUSTMENT",
    "DEFAULT_SIDEBAR_PADDING",
    "DEFAULT_FRAME_PADDING",
    "DEFAULT_COVER_PADDING_TOP",
    "DEFAULT_COVER_PADDING_BOTTOM",
    "DEFAULT_COVER_PADDING_HORIZONTAL",
    "MIN_PAGE_WIDTH_MM",
    "MAX_PAGE_WIDTH_MM",
    "MIN_PAGE_HEIGHT_MM",
    "MAX_PAGE_HEIGHT_MM",
    "MIN_SIDEBAR_WIDTH_MM",
    "MAX_SIDEBAR_WIDTH_MM",
    "MIN_PADDING",
    "MAX_PADDING",
]
