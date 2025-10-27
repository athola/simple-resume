"""Create all CVs from the input folder."""

import argparse
import os
import time

from weasyprint import CSS, HTML

from .config import PATH_INPUT, PATH_OUTPUT, URL_PRINT
from .index import run_app


def generate_pdf(data_dir: str | None = None) -> None:
    """Generate pdf from html.

    Args:
        data_dir: Path to data directory containing input/output folders

    Returns:
        None

    """
    # If data_dir is provided, update environment configuration directly
    if data_dir:
        os.environ["CV_DATA_DIR"] = data_dir

    run_app(True)

    # Create input and output directories if they don't exist
    if not os.path.exists(PATH_INPUT):
        os.makedirs(PATH_INPUT, exist_ok=True)
    if not os.path.exists(PATH_OUTPUT):
        os.makedirs(PATH_OUTPUT, exist_ok=True)

    for filename in os.listdir(PATH_INPUT):
        if "." not in filename:
            continue

        # Handle files with multiple dots properly
        parts = filename.split(".")
        if len(parts) < MIN_FILENAME_PARTS:
            continue

        extension = parts[-1].lower()
        if extension not in ["yaml", "yml"]:
            continue

        # Reconstruct name without the extension
        name = ".".join(parts[:-1])
        input_file = f"http://{URL_PRINT}{name}"
        output_file = f"{PATH_OUTPUT}{name}.pdf"

        time.sleep(1)
        print(f"\n-- Creating {name}.pdf --")
        css = CSS(string=""" @page {size: Letter; margin: 0in 0.44in 0.2in 0.44in;} """)
        HTML(input_file).write_pdf(output_file, stylesheets=[css])


MIN_FILENAME_PARTS = 2  # filename must have at least name and extension


def main() -> None:
    """Generate PDF files from CV data via command line interface."""
    parser = argparse.ArgumentParser(description="Generate PDF files from CV data")
    parser.add_argument(
        "--data-dir",
        type=str,
        help=(
            "Path to data directory containing input/output folders "
            "(default: use config)"
        ),
    )
    args = parser.parse_args()

    generate_pdf(data_dir=args.data_dir)


if __name__ == "__main__":
    main()
