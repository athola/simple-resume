"""CLI entry point for generating randomized palette demo YAML files."""

from __future__ import annotations

import argparse
import random
import secrets
import string
from pathlib import Path

import yaml

from .palettes.generators import generate_hcl_palette
from .palettes.registry import get_global_registry

DEFAULT_OUTPUT = Path("sample/input/sample_palette_demo_random.yaml")
DEFAULT_TEMPLATE = Path("sample/input/sample_palette_demo.yaml")


def _random_words(count: int, *, word_len: int = 6) -> list[str]:
    alphabet = string.ascii_lowercase
    return [
        "".join(secrets.choice(alphabet) for _ in range(word_len)) for _ in range(count)
    ]


def _random_sentence(words: int = 12) -> str:
    parts = _random_words(words)
    sentence = " ".join(parts)
    return sentence.capitalize() + "."


def _random_description(paragraphs: int = 2) -> str:
    paras = [
        " ".join(_random_sentence(secrets.randbelow(7) + 8) for _ in range(2))
        for _ in range(paragraphs)
    ]
    return "\n\n".join(paras)


def _random_email(name: str) -> str:
    handle = name.lower().replace(" ", ".")
    suffix = "".join(
        secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )
    return f"{handle}.{suffix}@example.com"


def _random_linkedin(name: str) -> str:
    handle = name.lower().replace(" ", "-")
    suffix = "".join(
        secrets.choice(string.ascii_lowercase + string.digits) for _ in range(4)
    )
    return f"in/{handle}-{suffix}"


def _random_palette(seed: int | None = None, size: int = 6) -> dict[str, str]:
    colors = generate_hcl_palette(size, seed=seed or secrets.randbelow(9999) + 1)
    keys = [
        "theme_color",
        "sidebar_color",
        "sidebar_text_color",
        "bar_background_color",
        "date2_color",
        "frame_color",
    ]
    mapping = {}
    for key, color in zip(keys, colors, strict=False):
        mapping[key] = color
    return mapping


def _random_registry_palette() -> dict[str, str] | None:
    registry = get_global_registry()
    palettes = registry.list()
    if not palettes:
        return None
    palette = secrets.choice(palettes)
    mapping = {}
    keys = [
        "theme_color",
        "sidebar_color",
        "sidebar_text_color",
        "bar_background_color",
        "date2_color",
        "frame_color",
    ]
    for key, color in zip(keys, palette.swatches, strict=False):
        mapping[key] = color
    mapping["color_scheme"] = palette.name
    return mapping


def generate_random_yaml(
    *,
    output_path: Path,
    template_path: Path,
    seed: int | None = None,
) -> None:
    """Generate random resume YAML with palette variations for testing."""
    if seed is not None:
        random.seed(seed)

    base = yaml.safe_load(template_path.read_text(encoding="utf-8"))

    name = f"Casey {_random_words(1, word_len=5)[0].title()}"
    base["full_name"] = name
    base["job_title"] = secrets.choice(
        [
            "Design Technologist",
            "Principal Engineer",
            "Product Strategist",
            "Data Storyteller",
            "Accessibility Specialist",
        ]
    )
    base["phone"] = f"(512) 555-{secrets.randbelow(9000) + 1000}"
    base["email"] = _random_email(name)
    base["linkedin"] = _random_linkedin(name)
    github_handle = name.lower().replace(" ", "")
    base["github"] = github_handle
    base["web"] = f"https://{github_handle}.dev"

    base["description"] = _random_description()

    for section in base["body"].values():
        for entry in section:
            entry["description"] = "- " + "\n- ".join(
                _random_sentence(secrets.randbelow(4) + 6)
                for _ in range(secrets.randbelow(2) + 2)
            )

    config = base.setdefault("config", {})
    config["output_mode"] = "markdown"
    config["sidebar_width"] = 60
    config["sidebar_padding_top"] = 6
    config["h3_padding_top"] = 5

    palette = _random_registry_palette()
    if palette is None:
        palette = _random_palette(size=6)
        palette["color_scheme"] = f"generator_{secrets.randbelow(9000) + 1000}"
    config.update(palette)

    output_path.write_text(yaml.safe_dump(base, sort_keys=False), encoding="utf-8")


def main() -> None:
    """Run the random palette demo generator CLI."""
    parser = argparse.ArgumentParser(
        description="Generate random resume content + palette demo YAML"
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument(
        "--seed", type=int, help="Deterministic seed for reproducibility"
    )
    args = parser.parse_args()

    generate_random_yaml(
        output_path=args.output,
        template_path=args.template,
        seed=args.seed,
    )
    print(f"✓ Wrote {args.output}")


__all__ = ["generate_random_yaml", "main"]
