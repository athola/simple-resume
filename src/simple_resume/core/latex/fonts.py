"""LaTeX font support functions (pure, no side effects)."""

from __future__ import annotations

import textwrap


def fontawesome_support_block(fontawesome_dir: str | None) -> str:
    r"""Return a LaTeX block that defines the contact icons.

    This is a pure function that generates LaTeX code for FontAwesome
    icon support. It uses either fontspec (with font files) or fallback
    text-based icons.

    Args:
        fontawesome_dir: Path to fontawesome fonts directory, or None for fallback.

    Returns:
        LaTeX code block defining icon commands.

    Examples:
        >>> block = fontawesome_support_block(None)
        >>> r"\\IfFileExists{fontawesome.sty}" in block
        True
        >>> block = fontawesome_support_block("/fonts/")
        >>> r"\\usepackage{fontspec}" in block
        True

    """
    fallback = textwrap.dedent(
        r"""
        \IfFileExists{fontawesome.sty}{%
          \usepackage{fontawesome}%
          \providecommand{\faLocation}{\faMapMarker}%
        }{
          \newcommand{\faPhone}{\textbf{P}}
          \newcommand{\faEnvelope}{\textbf{@}}
          \newcommand{\faLinkedin}{\textbf{in}}
          \newcommand{\faGlobe}{\textbf{W}}
          \newcommand{\faGithub}{\textbf{GH}}
          \newcommand{\faLocation}{\textbf{A}}
        }
        """
    ).strip()

    if not fontawesome_dir:
        return fallback

    fontspec_block = textwrap.dedent(
        rf"""
        \usepackage{{fontspec}}
        \newfontfamily\FAFreeSolid[
            Path={fontawesome_dir},
            Scale=0.72,
        ]{{Font Awesome 6 Free-Solid-900.otf}}
        \newfontfamily\FAFreeBrands[
            Path={fontawesome_dir},
            Scale=0.72,
        ]{{Font Awesome 6 Brands-Regular-400.otf}}
        \newcommand{{\faPhone}}{{%
          {{\FAFreeSolid\symbol{{"F095}}}}%
        }}
        \newcommand{{\faEnvelope}}{{%
          {{\FAFreeSolid\symbol{{"F0E0}}}}%
        }}
        \newcommand{{\faLinkedin}}{{%
          {{\FAFreeBrands\symbol{{"F08C}}}}%
        }}
        \newcommand{{\faGlobe}}{{%
          {{\FAFreeSolid\symbol{{"F0AC}}}}%
        }}
        \newcommand{{\faGithub}}{{%
          {{\FAFreeBrands\symbol{{"F09B}}}}%
        }}
        \newcommand{{\faLocation}}{{%
          {{\FAFreeSolid\symbol{{"F3C5}}}}%
        }}
        """
    ).strip()

    lines: list[str] = [r"\usepackage{iftex}", r"\ifPDFTeX"]
    fallback_lines = fallback.splitlines()
    lines.extend(f"  {line}" if line else "" for line in fallback_lines)
    lines.append(r"\else")
    fontspec_lines = fontspec_block.splitlines()
    lines.extend(f"  {line}" if line else "" for line in fontspec_lines)
    lines.append(r"\fi")
    return "\n".join(lines)


__all__ = [
    "fontawesome_support_block",
]
