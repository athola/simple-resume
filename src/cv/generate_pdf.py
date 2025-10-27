"""Create all CVs from the input folder."""

import argparse
import os
import subprocess
import sys
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
    # If data_dir is provided, restart the script with the environment variable set
    if data_dir:
        env = os.environ.copy()
        env["CV_DATA_DIR"] = data_dir

        # Restart the script without the data_dir argument
        result = subprocess.run(
            [sys.executable, "-m", "cv.generate_pdf"],
            env=env,
            capture_output=False,
            text=True,
            check=False,
        )

        # Exit with the same code as the subprocess
        sys.exit(result.returncode)

    run_app(True)

    # Create output directory if it doesn't exist (check once, not in loop)
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
    """Main entry point for command line interface."""
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
