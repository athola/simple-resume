""" Create all CVs from the input folder."""

import os
import time
from weasyprint import HTML

from .config import PATH_INPUT, URL_PRINT, PATH_OUTPUT, STATIC_LOC
from .index import run_app
from .utilities import get_content


def generate_pdf():
    run_app(True)
    for filename in os.listdir(PATH_INPUT):

        name, extension = filename.split(".")

        if extension not in ["yaml", "yml"]:
            continue
        
        input_file = f"http://{URL_PRINT}{name}"
        output_file = f"{PATH_OUTPUT}{name}.pdf"
        time.sleep(2)
        print(f"\n-- Creating {name}.pdf --")
        HTML(input_file).write_pdf(output_file)


if __name__ == "__main__":
    generate_pdf()
