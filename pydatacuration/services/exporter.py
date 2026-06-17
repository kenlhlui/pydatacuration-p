"""This module provides functions for exporting to YAML and word files."""

import re
from pathlib import Path
from typing import Any

import yaml
from docxtpl import DocxTemplate
from loguru import logger
from sqlmodel import SQLModel

from pydatacuration.db.base import DatabaseBackend
from pydatacuration.utils.directory_manager import DirectoryManager
from pydatacuration.utils.utils import get_name_initials


def _strip_markup(text: str) -> str:
    """Strip HTML tags and markdown bold markers from a string."""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text, flags=re.DOTALL)
    return text


class Exporter:
    """Class for exporting data to YAML and word formats."""

    def __init__(self, db: DatabaseBackend, dir_manager: DirectoryManager, res_dir: Path | None = None) -> None:
        """Initialize the Exports class with a database backend and DirectoryManager instances."""
        self.db = db
        self.dir_manager = dir_manager
        self.res_dir = res_dir if res_dir is not None else Path.cwd() / 'res'

        self.project_metadata = self.db.read_project_metadata_record()
        self.checklist: list[SQLModel] = self.db.read_checklist()

    def get_docx_file_name(self) -> str:
        """Generate a file name for the exported word document based on the project metadata."""
        project_number = self.project_metadata.get('project_number', '')
        curator_initials = get_name_initials(self.project_metadata.get('curator_name', ''))
        logger.debug(f'Generated docx file name: {project_number}_{curator_initials}_curation_report.docx')
        return f'{project_number}_{curator_initials}_curation_report.docx'

    def generate_yaml(self) -> dict[str, Any]:
        """Generate YAML data by reading the database."""
        # Merge checklist results into checklist
        for row in self.checklist:
            row_dict = row.model_dump()
            # Unpack the automated check results to the checklist item
            if row_dict.get('automated_check_ids') and row_dict.get('automated_check_ids') != []:
                for check_id in row_dict['automated_check_ids']:
                    result = self.db.read_row(self.db.models.check_results(), 'check_id', check_id)
                    if result:
                        check_name = result.get('check_name', '')
                        row_dict.setdefault('automated_check_results', {})[check_name] = result.get('results')

        checklist_items = [row.model_dump() for row in self.checklist]

        # Sort the checklist items by id, ensuring that items without an id are placed at the end
        checklist_items.sort(key=lambda x: x['id'])

        yaml_data = {
            'project_metadata': self.project_metadata,
            'checklist': checklist_items,
        }

        return yaml_data

    def export_yaml(self) -> None:
        """Export YAML file from the project directory."""
        yaml_data = self.generate_yaml()
        with (self.dir_manager.outputs_dir / 'output.yaml').open('w', encoding='utf-8') as yaml_file:
            # Write the checklist results to YAML
            yaml.dump(yaml_data, yaml_file, sort_keys=False, allow_unicode=True)

    def render_word(self, word_template_name: str | None = None) -> DocxTemplate:
        """Export word file from the project directory."""
        yaml_data = self.generate_yaml()

        # Get the word template
        template_path = self.res_dir / (word_template_name or 'curation_log_template.docx')

        # Get the checklist items
        checklist_items = yaml_data.get('checklist', [])

        # Get the metadata
        metadata = yaml_data.get('project_metadata', {})

        doc = DocxTemplate(template_path)

        # Strip HTML tags and markdown from string fields so docxtpl doesn't corrupt the XML
        for item in checklist_items:
            for field, value in item.items():
                if isinstance(value, str):
                    item[field] = _strip_markup(value)

        context = {
            'checklist': checklist_items,
            'project_metadata': metadata,
        }

        # pass the list in under the name 'rows' to match the template
        doc.render(context)
        return doc

    def export_word(self, word_template_name: str | None = None) -> None:
        """Export word file from the project directory."""
        doc = self.render_word(word_template_name)
        logger.info(f'Exporting word to {self.dir_manager.outputs_dir / "curation_report.docx"}')
        output_path = self.dir_manager.outputs_dir / 'curation_report.docx'
        doc.save(output_path)
