"""This module provides functions for exporting to YAML and word files."""

from typing import Any

import yaml

from .directory_manager import DirectoryManager
from .duck_db import DuckDB


class Exporter:
    """Class for exporting data to YAML and word formats."""

    def __init__(self, duckdb: DuckDB, dir_manager: DirectoryManager) -> None:
        """Initialize the Exports class with DuckDB and DirectoryManager instances."""
        self.duckdb = duckdb
        self.dir_manager = dir_manager

    def export_yaml(self) -> None:
        """Export YAML file from the project directory."""
        yaml_data = self.generate_yaml()
        with (self.dir_manager.outputs_dir / 'output.yaml').open('w', encoding='utf-8') as yaml_file:
            # Write the checklist results to YAML
            yaml.dump(yaml_data, yaml_file, sort_keys=False, allow_unicode=True)

    def generate_yaml(self) -> dict[str, Any]:
        """Generate YAML data by reading the database."""
        project_metadata = self.duckdb.read_project_metadata_record()
        checklist: dict[str, Any] = self.duckdb.read_checklist()

        yaml_data = {
            'project_metadata': project_metadata,
            'checklist': checklist.get('checklist', []),
        }

        return yaml_data

    def export_word(self) -> None:
        """Export word file from the project directory."""
        pass
