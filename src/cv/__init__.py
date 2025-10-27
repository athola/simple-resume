#!/usr/bin/env python3
"""Manage imports for cv project."""

from . import generate_pdf, index

__all__ = ("__version__", "generate_pdf", "index", "run_app")

__version__ = "2.0.1"

run_app = index.run_app
