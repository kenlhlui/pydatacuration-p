# pylint: disable=C0114, C0301, C0116
import orjson
import pandas as pd
from jinja2 import Template

def read_template_json():
    with open('./res/template.json', 'r', encoding='utf-8') as file:
        template = orjson.loads(file.read()) # pylint: disable=E1101
    return template

def generate_report(template_dict):
    # Read the template.csv file
    with open('./res/template.csv', 'r', encoding='ISO-8859-1') as f:
        template_string = f.read()
    report = Template(template_string)

    # Render the template with the template_dict
    rendered = report.render(template_dict=template_dict)
    with open('./workdir/log_files/temp_data/render_log.csv', 'w', encoding='utf-8') as f:
        f.write(rendered)

    # Convert the rendered csv file to an Excel file
    pd.read_csv('./workdir/log_files/temp_data/render_log.csv', keep_default_na=False).to_excel('./workdir/log_files/render_log.xlsx', index=False, na_rep='NA')
    print('\nReport generated. See the workdir/log_files/render_log.xlsx file for the report.')
