#!/usr/bin/env python3
"""Load CV as a webpage for testing purposes."""

import os
from threading import Thread
from typing import Any, cast

from flask import Flask, render_template

from .utilities import get_content

APP = Flask(__name__)


@APP.route("/v/<name>")
@APP.route("/view/<name>")
@APP.route("/v/")
@APP.route("/view/")
def show(name: str = "", preview: bool = True) -> str:
    """Render a CV for previews.

    Args:
        name (str): Name of the data content to display.
        preview (bool): Show a preview of the data content.

    Returns:
        str: The rendered HTML template as a string.

    """
    data = get_content(name)

    # Handle missing template field gracefully
    template_name = data.get("template", "cv_no_bars")
    template = f"{template_name}.html"

    # Rename config to avoid conflict with Flask's config
    if "config" in data:
        data["cv_config"] = data.pop("config")

    return render_template(template, preview=preview, **data)


@APP.route("/print/<name>")
def mprint(name: str = "") -> str:
    """Display a CV without any frame for printing.

    Args:
        name (str): Name of the data content to display for printing.

    Returns:
        str: The rendered HTML template as a string.

    """
    return show(name, preview=False)


@APP.route("/print.html")
def print_sample() -> str:
    """Display the sample CV without any frame for printing.

    Args:
        None

    Returns:
        str: The rendered HTML template as a string.

    """
    return mprint()


@APP.route("/")
def show_sample() -> str:
    """Render the sample CV for preview.

    Args:
        None

    Returns:
        str: The rendered HTML template as a string.

    """
    return show()


def execute_app() -> None:
    """Execute an instance of the Flask application.

    Args:
        None

    Returns:
        None

    """
    APP.run(
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
        use_reloader=False,
    )


def run_app(daemon: bool = False) -> None:
    """Run the Flask application on a separate thread if daemonized.

    Args:
        daemon (bool): Optional argument to run app as a daemon.

    Returns:
        None

    """
    if daemon:
        Thread(name="flask_app", target=execute_app, daemon=True).start()
    else:
        execute_app()


if __name__ == "__main__":
    run_app()
