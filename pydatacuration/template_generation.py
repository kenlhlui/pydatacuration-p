"""Generates a report based on a template and data from a JSON file."""
from pathlib import Path

import orjson
import pandas as pd
from jinja2 import Template

RES_DIR = Path('res')

def read_template_json() -> dict:
    """Reads the template.json file and returns it as a dictionary.

    Returns:
        dict: The template as a dictionary.
    """
    with RES_DIR.joinpath('template.json').open(encoding='utf-8') as file:
        return orjson.loads(file.read())

def generate_report(template_dict: dict, workdir: Path) -> None:
    """Generates a report based on the provided template dictionary.

    Args:
        template_dict (dict): The template dictionary.
    """
    # Read the template.csv file
    with RES_DIR.joinpath('template.csv').open(encoding='ISO-8859-1') as f:
        template_string = f.read()
    report = Template(template_string)

    # Render the template with the template_dict
    rendered = report.render(template_dict=template_dict)
    with workdir.joinpath('log_files', 'temp_data', 'render_log.csv').open('w', encoding='utf-8') as f:
        f.write(rendered)

    # Convert the rendered csv file to an Excel file
    csv_path_obj = workdir.joinpath('log_files', 'temp_data', 'render_log.csv')
    excel_path_obj = workdir.joinpath('log_files', 'render_log.xlsx')
    pd.read_csv(csv_path_obj, keep_default_na=False).to_excel(excel_path_obj, index=False, na_rep='NA')

    print(f'\nReport generated. See the {str(excel_path_obj)} file for the report.')
