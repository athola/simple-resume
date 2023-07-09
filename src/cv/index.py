"""Loads CV as a webpage for testing purposes."""

from threading import Thread
import time

from flask import Flask, render_template

from .utilities import get_content


APP = Flask(__name__)


@APP.route("/v/<name>")
@APP.route("/view/<name>")
def show(name='', preview=True):
    """Render a CV for previews."""

    data = get_content(name)
    template = f"{data['template']}.html"

    return render_template(template, preview=preview, **data)


@APP.route("/print/<name>")
def mprint(name=''):
    """Display a CV without any frame for printing."""
    return show(name, preview=False)


@APP.route("/print.html")
def print_sample():
    """Display the sample CV without any frame for printing."""
    return mprint()


@APP.route("/")
def show_sample():
    """Render the sample CV for preview."""
    return show()


def execute_app():
    APP.run(debug=True, use_reloader=False)


def run_app(daemon=False):
    if daemon:
        Thread(name='flask_app', target=execute_app, daemon=True).start()
    else:
        execute_app()


if __name__ == "__main__":
    run_app()
