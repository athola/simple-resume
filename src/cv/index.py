#!/usr/bin/env python3
"""Loads CV as a webpage for testing purposes."""
from threading import Thread

from flask import Flask, render_template

from .utilities import get_content


APP = Flask(__name__)


@APP.route("/v/<name>")
@APP.route("/view/<name>")
def show(name: str = '', preview: bool = True) -> str:
    """Render a CV for previews.

    Args:
        name (str): Name of the data content to display.
        preview (bool): Show a preview of the data content.

    Returns:
        str: The rendered HTML template as a string.

    """
    data = get_content(name)
    template = f"{data['template']}.html"

    return render_template(template, preview=preview, **data)


@APP.route("/print/<name>")
def mprint(name: str = '') -> str:
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
    APP.run(debug=True, use_reloader=False)


def run_app(daemon: bool = False) -> None:
    """Run the Flask application on a separate thread if daemonized.

    Args:
        daemon (bool): Optional argument to run app as a daemon.

    Returns:
        None

    """
    if daemon:
        Thread(name='flask_app', target=execute_app, daemon=True).start()
    else:
        execute_app()


if __name__ == "__main__":
    run_app()
