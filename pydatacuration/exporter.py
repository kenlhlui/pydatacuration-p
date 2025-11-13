"""This module provides functions for exporting to YAML and word files."""

from pathlib import Path
from typing import Any

import yaml
from docxtpl import DocxTemplate

from .custom_logging import logger
from .directory_manager import DirectoryManager
from .duck_db import DuckDB
from .sqlmodels import DuckDBmodels


class Exporter:
    """Class for exporting data to YAML and word formats."""

    def __init__(self, duckdb: DuckDB, dir_manager: DirectoryManager, res_dir: Path | None = None) -> None:
        """Initialize the Exports class with DuckDB and DirectoryManager instances."""
        self.duckdb = duckdb
        self.dir_manager = dir_manager
        self.res_dir = res_dir if res_dir is not None else Path.cwd() / 'res'

    def generate_yaml(self) -> dict[str, Any]:
        """Generate YAML data by reading the database."""
        project_metadata = self.duckdb.read_project_metadata_record()
        checklist: dict[str, Any] = self.duckdb.read_checklist()
        # check_results: dict[str, Any] = self.duckdb.read_check_results()

        # Merge checklist results into checklist
        for item in checklist.get('checklist', []):
            if item.get('automated_check_ids') and item.get('automated_check_ids') != []:
                for check_id in item['automated_check_ids']:
                    result = self.duckdb.sql_read_row(
                        DuckDBmodels(self.duckdb.schema_name).check_results(), 'check_id', check_id
                    )
                    if result:
                        check_name = result.get('check_name', '')
                        item.setdefault('automated_check_results', {})[check_name] = result.get('results')

        yaml_data = {
            'project_metadata': project_metadata,
            'checklist': checklist.get('checklist', []),
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

        context = {
            'checklist': checklist_items,
            'project_metadata': metadata,
        }

        # pass the list in under the name 'rows' to match the template
        logger.debug('Rendering word document with checklist and metadata')
        doc.render(context)
        logger.debug(f'Exporting word to {self.dir_manager.outputs_dir / "curation_report.docx"}')
        output_path = self.dir_manager.outputs_dir / 'curation_report.docx'
        doc.save(output_path)
