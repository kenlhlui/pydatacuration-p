"""This module provides functions for exporting to YAML and word files."""

import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import yaml
from docxtpl import DocxTemplate
from docxtpl import RichText
from sqlmodel import SQLModel

from pydatacuration.db.base import DatabaseBackend
from pydatacuration.utils.custom_logging import logger
from pydatacuration.utils.directory_manager import DirectoryManager


_HTML_RICH_TEXT_FIELDS = ('action', 'instructions', 'curator_check_item')


class _HTMLRichTextParser(HTMLParser):
    """Parses an HTML string into a docxtpl RichText object."""

    def __init__(self, doc: DocxTemplate) -> None:
        """Initialize with the DocxTemplate used to build URL IDs."""
        super().__init__()
        self.doc = doc
        self.rt = RichText()
        self._href: str | None = None
        self._underline = False
        self._bold = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        """Handle opening HTML tags."""
        if tag == 'a':
            self._href = dict(attrs).get('href', '')
        elif tag == 'u':
            self._underline = True
        elif tag in ('b', 'strong'):
            self._bold = True

    def handle_endtag(self, tag: str) -> None:
        """Handle closing HTML tags."""
        if tag == 'a':
            self._href = None
        elif tag == 'u':
            self._underline = False
        elif tag in ('b', 'strong'):
            self._bold = False

    def handle_data(self, data: str) -> None:
        """Append a text run with the current formatting state."""
        kwargs: dict[str, Any] = {}
        if self._bold:
            kwargs['bold'] = True
        if self._underline:
            kwargs['underline'] = True
        if self._href:
            kwargs['url_id'] = self.doc.build_url_id(self._href)
        self.rt.add(data, **kwargs)


def _to_richtext(doc: DocxTemplate, text: str) -> RichText:
    """Convert a string with HTML tags and **markdown bold** to a RichText object."""
    # Convert **markdown bold** to <b> tags so HTMLParser can handle them uniformly
    normalised = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    parser = _HTMLRichTextParser(doc)
    parser.feed(normalised)
    return parser.rt


class Exporter:
    """Class for exporting data to YAML and word formats."""

    def __init__(self, db: DatabaseBackend, dir_manager: DirectoryManager, res_dir: Path | None = None) -> None:
        """Initialize the Exports class with a database backend and DirectoryManager instances."""
        self.db = db
        self.dir_manager = dir_manager
        self.res_dir = res_dir if res_dir is not None else Path.cwd() / 'res'

    def generate_yaml(self) -> dict[str, Any]:
        """Generate YAML data by reading the database."""
        project_metadata = self.db.read_project_metadata_record()
        checklist: list[SQLModel] = self.db.read_checklist()

        # Merge checklist results into checklist
        for row in checklist:
            row_dict = row.model_dump()
            # Unpack the automated check results to the checklist item
            if row_dict.get('automated_check_ids') and row_dict.get('automated_check_ids') != []:
                for check_id in row_dict['automated_check_ids']:
                    result = self.db.read_row(self.db.models.check_results(), 'check_id', check_id)
                    if result:
                        check_name = result.get('check_name', '')
                        row_dict.setdefault('automated_check_results', {})[check_name] = result.get('results')

        yaml_data = {
            'project_metadata': project_metadata,
            'checklist': [item.model_dump() for item in checklist],
        }

        return yaml_data

    def export_yaml(self) -> None:
        """Export YAML file from the project directory."""
        yaml_data = self.generate_yaml()
        with (self.dir_manager.outputs_dir / 'output.yaml').open('w', encoding='utf-8') as yaml_file:
            # Write the checklist results to YAML
            yaml.dump(yaml_data, yaml_file, sort_keys=False, allow_unicode=True)

    def export_word(self, word_template_name: str | None = None) -> None:
        """Export word file from the project directory."""
        yaml_data = self.generate_yaml()

        # Get the word template
        template_path = self.res_dir / (word_template_name or 'curation_log_template.docx')

        # Get the checklist items
        checklist_items = yaml_data.get('checklist', [])

        # Get the metadata
        metadata = yaml_data.get('project_metadata', {})

        doc = DocxTemplate(template_path)

        # Convert HTML/markdown fields to RichText so docxtpl doesn't corrupt the XML
        for item in checklist_items:
            for field in _HTML_RICH_TEXT_FIELDS:
                if isinstance(item.get(field), str):
                    item[field] = _to_richtext(doc, item[field])

        context = {
            'checklist': checklist_items,
            'project_metadata': metadata,
        }

        # pass the list in under the name 'rows' to match the template
        doc.render(context)
        logger.info(f'Exporting word to {self.dir_manager.outputs_dir / "curation_report.docx"}')
        output_path = self.dir_manager.outputs_dir / 'curation_report.docx'
        doc.save(output_path)
