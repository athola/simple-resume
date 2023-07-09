"""Load data from YAML files as ordered dicts."""

from oyaml import safe_load
from markdown import markdown
from typing import Any, Dict

from .config import FILE_DEFAULT, PATH_INPUT


def _read_yaml(uri: str) -> Dict[str, Any]:
    """Auxilary function to read a yaml file."""
    with open(uri, encoding="utf-8") as file:
        return safe_load(file)


def _transform_from_markdown(data: Dict[str, Any]):
    """Transform markdown text to html"""
    # Main description of CV
    if "description" in data:
        data["description"] = markdown(data["description"])

    # Descriptions in body
    if "body" in data:
        for block_name, block_data in data["body"].items():
            for element in block_data:
                if "description" in element:
                    element["description"] = markdown(element["description"])


def get_content(name: str = ''):
    """Return content of the CV."""

    if not name:
        name = FILE_DEFAULT

    split_name = name.split(".")
    if split_name:
        name = split_name[0]

    # Read data
    out = _read_yaml(f"{PATH_INPUT}{name}.yaml")
    _transform_from_markdown(out)

    return out
