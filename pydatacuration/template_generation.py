"""Generates a report based on a template and data from a JSON file."""
from pathlib import Path

import jinja2
import orjson
import pandas as pd
from jinja2 import Template
from openpyxl import load_workbook


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
        workdir (Path): The working directory.
    """
    # Read the template.csv file #TEMP: Change to template_new.csv
    with RES_DIR.joinpath('template_new.csv').open(encoding='ISO-8859-1') as f:
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


def generate_report_xlsx(template_dict: dict, workdir: Path) -> None:
    """Fill a formatted Excel template with data using Jinja2 for variable replacement.

    Args:
        template_dict (dict): Dictionary of data to inject into the template
        workdir (Path): Path to the generated log file
    """
    # Load the workbook with formatting
    template_path = Path(RES_DIR, 'template_new.xlsx')
    workbook = load_workbook(template_path)
    sheet = workbook.active

    # Create Jinja2 environment
    env = jinja2.Environment()

    # Process each cell in the worksheet to replace Jinja2 variables
    for row in sheet.iter_rows():
        for cell in row:
            if cell.value and isinstance(cell.value, str) and '{%' in cell.value:
                # This cell contains a Jinja2 template
                template = env.from_string(cell.value)
                try:
                    # Render the template with our data
                    cell.value = template.render(template_dict=template_dict)
                except Exception as e:
                    print(f'Error rendering template in cell {cell.coordinate}: {e}')

    # Save the modified workbook
    excel_path_obj = workdir.joinpath('log_files', 'render_log_new.xlsx')
    workbook.save(excel_path_obj)
    print(f'\nReport generated. See the {str(excel_path_obj)} file for the report.')
