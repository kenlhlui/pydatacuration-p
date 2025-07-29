from pathlib import Path

import yaml
from docxtpl import DocxTemplate


def render_report_from_yaml(
    yaml_path: str,
    template_path: str,
    output_path: str
) -> None:
    """Render a DOCX report by repeating a table row for each YAML record.

    Args:
        yaml_path (str): Path to the .yaml file containing a list of dicts.
        template_path (str): Path to the .docx template with Jinja tags.
        output_path (str): Where to save the rendered .docx.

    Returns:
        None: The filled document is written to output_path.
    """
    with Path(yaml_path).open('r', encoding='utf-8') as fp:
        data = yaml.safe_load(fp)


    doc = DocxTemplate(template_path)
    context = {
        'data': data
    }
    # pass the list in under the name 'rows' to match the template
    doc.render(context)
    doc.save(output_path)
