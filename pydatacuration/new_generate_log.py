import json

from docxtpl import DocxTemplate


def render_report_from_json(
    json_path: str,
    template_path: str,
    output_path: str
) -> None:
    """Render a DOCX report by repeating a table row for each JSON record.

    Args:
        json_path (str): Path to the .json file containing a list of dicts.
        template_path (str): Path to the .docx template with Jinja tags.
        output_path (str): Where to save the rendered .docx.

    Returns:
        None: The filled document is written to output_path.
    """
    with open(json_path, 'r', encoding='utf-8') as fp:
        data = json.load(fp)

    doc = DocxTemplate(template_path)
    context = {
        'data': data
    }
    # pass the list in under the name 'rows' to match the template
    doc.render(context)
    doc.save(output_path)
