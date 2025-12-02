"""Provide a CLI entry point for generating randomized palette demo YAML files."""

from __future__ import annotations

import argparse
import random
import secrets
import string
from pathlib import Path

from oyaml import safe_dump, safe_load

from simple_resume.core.markdown import derive_bold_color
from simple_resume.core.palettes.generators import generate_hcl_palette
from simple_resume.shell.palettes.loader import get_palette_registry

DEFAULT_OUTPUT = Path("sample/input/sample_palette_demo_random.yaml")
DEFAULT_TEMPLATE = Path("sample/input/sample_palette_demo.yaml")

# Realistic word banks for generating resume content
FIRST_NAMES = [
    "Alex",
    "Jordan",
    "Morgan",
    "Taylor",
    "Casey",
    "Riley",
    "Quinn",
    "Avery",
    "Cameron",
    "Dakota",
    "Emerson",
    "Harper",
    "Hayden",
    "Jamie",
    "Kendall",
    "Logan",
    "Parker",
    "Reese",
    "Sage",
    "Skylar",
]

LAST_NAMES = [
    "Anderson",
    "Bennett",
    "Carter",
    "Davis",
    "Ellis",
    "Foster",
    "Garcia",
    "Hayes",
    "Jackson",
    "Kim",
    "Lee",
    "Martinez",
    "Nelson",
    "Parker",
    "Rivera",
    "Santos",
    "Taylor",
    "Williams",
    "Zhang",
    "Chen",
]

COMPANIES = [
    "TechCorp",
    "DataSystems",
    "CloudWorks",
    "InnovateLabs",
    "DevStack",
    "CodeCraft",
    "StreamFlow",
    "PixelPerfect",
    "ByteBridge",
    "Quantum Dynamics",
    "NexGen Solutions",
    "Vertex Technologies",
    "Horizon Digital",
    "Pulse Networks",
]

TECH_SKILLS = [
    "API design",
    "microservices architecture",
    "cloud infrastructure",
    "CI/CD pipelines",
    "performance optimization",
    "system monitoring",
    "database design",
    "caching strategies",
    "load balancing",
    "automated testing",
    "containerization",
    "orchestration",
]

ACCOMPLISHMENTS = [
    "Reduced latency by {percent}% through optimization",
    "Increased test coverage from {low}% to {high}%",
    "Led migration of {count} services to cloud infrastructure",
    "Improved deployment frequency by {mult}x using automation",
    "Architected scalable solution handling {volume} requests/day",
    "Mentored team of {size} engineers on best practices",
    "Reduced operational costs by {percent}% through efficient resource allocation",
    "Implemented monitoring system tracking {metric_count}+ metrics",
    "Streamlined development workflow reducing build time by {percent}%",
]

PROJECT_DESCRIPTIONS = [
    "Designed and implemented {feature} using {tech_stack}",
    "Built {system_type} to handle {capability}",
    "Created automated {process} reducing manual effort by {percent}%",
    "Developed {feature} integrating with {platform}",
    "Optimized {component} achieving {improvement}",
]

FEATURES = [
    "real-time analytics dashboard",
    "payment processing system",
    "user authentication service",
    "data pipeline",
    "API gateway",
    "notification system",
    "search engine",
    "content delivery network",
]

TECH_STACKS = [
    "Python and FastAPI",
    "Node.js and Express",
    "Go and gRPC",
    "Java and Spring Boot",
    "React and TypeScript",
    "Vue.js and Nuxt",
]

IMPROVEMENTS = [
    "99.9% uptime",
    "sub-100ms response times",
    "zero-downtime deployments",
    "10x throughput increase",
    "50% cost reduction",
]


def _random_words(count: int, *, word_len: int = 5) -> list[str]:
    """Generate a list of deterministic-length lowercase words."""
    if count <= 0:
        return []
    alphabet = string.ascii_lowercase
    return [
        "".join(secrets.choice(alphabet) for _ in range(max(1, word_len)))
        for _ in range(count)
    ]


def _random_name() -> str:
    """Generate a realistic random name."""
    first = secrets.choice(FIRST_NAMES)
    last = secrets.choice(LAST_NAMES)
    return f"{first} {last}"


def _random_sentence(context: str = "general") -> str:
    """Generate a realistic sentence based on context."""
    if context == "accomplishment":
        template = secrets.choice(ACCOMPLISHMENTS)
        return template.format(
            percent=secrets.randbelow(50) + 30,
            low=secrets.randbelow(30) + 40,
            high=secrets.randbelow(20) + 80,
            count=secrets.randbelow(15) + 5,
            mult=secrets.randbelow(5) + 2,
            volume=f"{secrets.randbelow(900) + 100}K",
            size=secrets.randbelow(8) + 3,
            metric_count=secrets.randbelow(50) + 50,
        )
    elif context == "project":
        template = secrets.choice(PROJECT_DESCRIPTIONS)
        return template.format(
            feature=secrets.choice(FEATURES),
            tech_stack=secrets.choice(TECH_STACKS),
            system_type=secrets.choice(
                ["distributed system", "service", "platform", "framework"]
            ),
            capability=secrets.choice(
                [
                    "high-volume traffic",
                    "real-time processing",
                    "multi-tenant operations",
                ]
            ),
            percent=secrets.randbelow(50) + 30,
            process=secrets.choice(
                ["deployment pipeline", "testing suite", "code review process"]
            ),
            platform=secrets.choice(["AWS", "GCP", "Azure", "Kubernetes"]),
            component=secrets.choice(
                [
                    "database queries",
                    "API endpoints",
                    "frontend rendering",
                ]
            ),
            improvement=secrets.choice(IMPROVEMENTS),
        )
    else:
        # General technical description
        skill = secrets.choice(TECH_SKILLS)
        return f"Experienced with {skill} and modern development practices."


def _random_description(paragraphs: int = 2) -> str:
    """Generate a realistic multi-paragraph description."""
    paras = []
    for _ in range(paragraphs):
        sentences = []
        for _ in range(2):
            sentences.append(_random_sentence("general"))
        paras.append(" ".join(sentences))
    return "\n\n".join(paras)


def _random_email(name: str) -> str:
    """Generate a random email address for the given name."""
    handle = name.lower().replace(" ", ".")
    suffix = "".join(
        secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )
    return f"{handle}.{suffix}@example.com"


def _random_linkedin(name: str) -> str:
    """Generate a random LinkedIn profile URL for the given name."""
    handle = name.lower().replace(" ", "-")
    suffix = "".join(
        secrets.choice(string.ascii_lowercase + string.digits) for _ in range(4)
    )
    return f"in/{handle}-{suffix}"


def _random_palette(seed: int | None = None, size: int = 6) -> dict[str, str]:
    """Generate a random HCL-inspired color palette.

    Args:
        seed: Optional deterministic seed for reproducibility.
        size: Number of colors in the palette.

    Returns:
        A dictionary of color key-value pairs.

    """
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
    for key, color in zip(keys, colors):
        mapping[key] = color
    if "frame_color" in mapping and "bold_color" not in mapping:
        mapping["bold_color"] = derive_bold_color(mapping["frame_color"])
    return mapping


def _random_registry_palette() -> dict[str, str] | None:
    """Select a random palette from the registered palettes.

    Returns:
        A dictionary of color key-value pairs, or None if no palettes are registered.

    """
    registry = get_palette_registry()
    palettes = registry.list()
    if not palettes:
        return None
    palette = secrets.choice(palettes)
    keys = [
        "theme_color",
        "sidebar_color",
        "sidebar_text_color",
        "bar_background_color",
        "date2_color",
        "frame_color",
    ]
    mapping = {}
    for key, color in zip(keys, palette.swatches):
        mapping[key] = color
    mapping["color_scheme"] = palette.name

    # If palette doesn't have enough swatches, generate missing colors
    if len(palette.swatches) < len(keys):
        missing_keys = keys[len(palette.swatches) :]
        additional_palette = generate_hcl_palette(
            len(missing_keys), seed=secrets.randbelow(9999) + 1
        )
        for key, color in zip(missing_keys, additional_palette):
            mapping[key] = color

    if "frame_color" in mapping and "bold_color" not in mapping:
        mapping["bold_color"] = derive_bold_color(mapping["frame_color"])
    return mapping


def generate_random_yaml(
    *,
    output_path: Path,
    template_path: Path,
    seed: int | None = None,
) -> None:
    """Generate random resume YAML with palette variations and realistic content."""
    if seed is not None:
        random.seed(seed)
        secrets.SystemRandom(seed)

    base = safe_load(template_path.read_text(encoding="utf-8"))

    # Generate realistic personal info
    name = _random_name()
    base["full_name"] = name
    base["job_title"] = secrets.choice(
        [
            "Senior Software Engineer",
            "Principal Engineer",
            "Staff Engineer",
            "Engineering Manager",
            "Technical Lead",
            "Solutions Architect",
            "DevOps Engineer",
            "Full Stack Developer",
        ]
    )
    base["phone"] = f"(512) 555-{secrets.randbelow(9000) + 1000}"
    base["email"] = _random_email(name)
    base["linkedin"] = _random_linkedin(name)
    github_handle = name.lower().replace(" ", "")
    base["github"] = github_handle
    base["web"] = f"https://{github_handle}.dev"

    # Generate realistic summary description
    base["description"] = _random_description()

    # Generate realistic work experience and project descriptions
    for section_name, section in base["body"].items():
        for entry in section:
            # Determine context based on section name
            if "experience" in section_name.lower() or "work" in section_name.lower():
                context = "accomplishment"
            elif "project" in section_name.lower():
                context = "project"
            else:
                context = "general"

            # Generate 2-4 bullet points with realistic content
            num_bullets = secrets.randbelow(3) + 2
            bullets = [_random_sentence(context) for _ in range(num_bullets)]
            entry["description"] = "- " + "\n- ".join(bullets)

            # Add realistic company names for work experience
            if "experience" in section_name.lower() and "company" in entry:
                entry["company"] = secrets.choice(COMPANIES)

    config = base.setdefault("config", {})
    config["output_mode"] = "markdown"
    config["sidebar_width"] = 60
    config["sidebar_padding_top"] = 6
    config["h3_padding_top"] = 5

    # Use palette from registry or generate one
    palette = _random_registry_palette()
    if palette is None:
        palette = _random_palette(size=6)
        palette["color_scheme"] = f"generator_{secrets.randbelow(9000) + 1000}"
    config.update(palette)
    if "bold_color" not in config and "frame_color" in config:
        config["bold_color"] = derive_bold_color(config["frame_color"])

    output_path.write_text(safe_dump(base, sort_keys=False), encoding="utf-8")


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
    print(f"Wrote {args.output}")


__all__ = ["main"]
