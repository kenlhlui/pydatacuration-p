"""Helper functions for NiceGUI components."""

import re
from pathlib import Path
from typing import Any

import markdown2
import yaml
from nicegui import app
from nicegui import ui
from sqlmodel import SQLModel

from pydatacuration.custom_logging import logger
from pydatacuration.custom_logging import setup_logging
from pydatacuration.directory_manager import DirectoryManager
from pydatacuration.duck_db import DuckDB
from pydatacuration.sqlmodels import DuckDBmodels
from pydatacuration.exporter import Exporter


setup_logging()

Checklist: type[SQLModel] = DuckDBmodels('temp').checklist()


class NiceGUIHelper:
    """Helper class for NiceGUI components."""

    def __init__(self, duckdb: DuckDB, ticket_number: str) -> None:
        """Initialize NiceGUIHelper.

        Args:
            duckdb (DuckDB): Instance of DuckDB.
            ticket_number (str): Ticket number to work with.
        """
        self.duckdb: DuckDB = duckdb
        self.ticket_number: str = ticket_number

    def get_checklist_items(self) -> list:
        """Get all checklist items from the DuckDB database for the specified ticket.

        The checklist type is determined by what was stored in the database during setup.

        Args:
            ticket_number (str): Ticket number to get checklist items for.

        Returns:
            list: List of checklist items with their details.

        """
        duck_db_data = self.duckdb.read_checklist()
        items = []
        for item in duck_db_data.get('checklist', []):
            checklist_item = Checklist(
                id=item['id'],
                action=item['action'],
                instructions=markdown2.markdown(item['instructions']) if item['instructions'] else '',
                priority=item['priority'],
                section=item.get('section', ''),
                automated_check_ids=item.get('automated_check_ids', []),
                status=item.get('status', ''),
                comments=item.get('comments', ''),
                time_spent=item.get('time_spent', ''),
                information_location=markdown2.markdown(  # Convert Markdown to HTML
                    item.get('information_location', '')
                )
                if item.get('information_location')
                else '',  # Handle missing information_location
                check_type=item.get('check_type', 'Manual'),  # Optional field for check type
            )
            items.append(checklist_item)
        return items

    def handle_status_change(self, item_id: str, new_status: str) -> None:
        """Handle status change with auto-save."""
        self.duckdb.sql_update_checklist_item(item_id=item_id, status=new_status)
        ui.notify(f'Status updated for {item_id}', type='positive', position='top-right', close_button=True)

    def handle_comments_change(self, item_id: str, new_comments: str) -> None:
        """Handle comments change."""
        self.duckdb.sql_update_checklist_item(item_id=item_id, comments=new_comments)
        ui.notify(f'Comments updated for {item_id}', type='positive', position='top-right', close_button=True)

    def handle_time_change(self, item_id: str, new_time: str) -> None:
        """Handle time change with validation."""
        if self.validate_time_format(new_time):
            self.duckdb.sql_update_checklist_item(item_id=item_id, time_spent=new_time)
            ui.notify(f'Time updated for {item_id}', type='positive', position='top-right', close_button=True)
        else:
            ui.notify('Please enter time in MM:SS format', type='negative')

    @staticmethod
    def calculate_total_time(items: list) -> None:
        """Calculate total time spent."""
        total_minutes = 0
        for item in items:
            if item.time_spent:
                try:
                    parts = item.time_spent.split(':')
                    total_minutes += int(parts[0]) * 60 + int(parts[1])
                except (ValueError, IndexError):
                    continue

        hours = total_minutes // 60
        minutes = total_minutes % 60
        ui.notify(f'Total Time Spent: {hours}:{minutes:02d}', type='info', position='top')

    @staticmethod
    def validate_time_format(time_str: str) -> bool:
        """Validate MM:SS format."""
        return bool(re.match(r'^[0-9]{1,2}:[0-5][0-9]$', time_str)) if time_str else True

    @staticmethod
    def confirm_new_dataset() -> None:
        """Confirm and navigate to new dataset."""

        def handle_confirm() -> None:
            app.storage.user.clear()
            ui.navigate.to('/')

        with ui.dialog() as dialog, ui.card():
            ui.label('This will clear the current session and start a new dataset. Continue?').classes('text-lg')
            with ui.row():
                ui.button('Yes', on_click=lambda: [dialog.close(), handle_confirm()])
                ui.button('No', on_click=dialog.close)
        dialog.open()

    @staticmethod
    def get_all_schemas(main_dir: Path) -> list[dict]:
        """Get all available schemas (projects) from DuckDB.

        Returns:
            list[dict]: List of schemas with metadata
        """
        try:
            db_dir = Path(main_dir) / 'db'
            db_file = db_dir / 'duckdb.db'

            if not db_file.exists():
                return []

            # Create a DuckDB instance to get schemas
            duck_db = DuckDB(schema_name='temp', db_file=db_file)
            schema_names = duck_db.get_all_schema_names()

            # Get additional metadata for each schema
            schemas_with_metadata = []
            for schema_name in schema_names:
                try:
                    # Try to get project metadata for last modified date
                    schema_duck_db = DuckDB(schema_name=schema_name, db_file=db_file)
                    metadata = schema_duck_db.read_project_metadata_record()

                    last_modified = 'Unknown'
                    if metadata and 'log_last_update_date' in metadata:
                        last_modified = metadata['log_last_update_date']
                    elif metadata and 'log_init_date' in metadata:
                        last_modified = metadata['log_init_date']

                    # Prune the schema, removing the prefixes
                    schema_name_display = schema_name.replace('duckdb.', '').replace('"', '')

                    schemas_with_metadata.append(
                        {
                            'display_name': schema_name_display,
                            'name': schema_name,
                            'last_modified': last_modified,
                            'checklist_type': metadata.get('checklist_type', 'unknown'),
                            'has_metadata': bool(metadata and metadata.get('dataset_pid')),
                            'curator_name': metadata.get('curator_name', ''),
                            'dataset_title': metadata.get('dataset_title', 'N/A'),
                        }
                    )
                except Exception as e:
                    print(f'Could not get metadata for schema {schema_name}: {e}')
                    schema_name_display = schema_name.replace('duckdb.', '').replace('"', '')
                    schemas_with_metadata.append(
                        {
                            'display_name': schema_name_display,
                            'name': schema_name,
                            'last_modified': 'Unknown',
                            'has_metadata': False,
                        }
                    )

            # Sort by last modified (most recent first)
            schemas_with_metadata.sort(key=lambda x: x['last_modified'], reverse=True)

            return schemas_with_metadata

        except Exception as e:
            print(f'Error fetching schemas: {e}')
            return []

    @staticmethod
    def delete_project(schema_name: str | None, main_dir: Path) -> tuple[bool, str]:
        """Delete a specific project by removing its schema and the project directory.

        Args:
            schema_name (str | None): Name of the schema to delete (includes duckdb. prefix)
            main_dir (Path): Main directory where the database, logs, and project directories are stored.

        """
        if not schema_name:
            return False, 'Invalid schema name'
        schema_name_pruned = schema_name.replace('duckdb.', '').replace('"', '')

        def delete_schema(schema_name_pruned: str) -> tuple[bool, str]:
            """Delete a specific schema from DuckDB.

            Args:
                schema_name_pruned (str): Name of the schema to delete (without duckdb. prefix)

            Returns:
                tuple[bool, str]: Success status and message
            """
            try:
                db_dir = Path(main_dir) / 'db'
                db_file = db_dir / 'duckdb.db'

                if not db_file.exists():
                    return False, 'Database file not found'

                # Create a DuckDB instance to delete the schema
                duck_db = DuckDB(schema_name='temp', db_file=db_file)

                # Delete the schema
                duck_db.sql_drop_schema(schema_name_pruned)

                return True, f'Schema {schema_name_pruned} deleted successfully'

            except Exception as e:
                return False, f'Error deleting schema: {str(e)}'

        def delete_project_directory(ticket_number: str) -> None:
            """Delete the project directory for a specific ticket number.

            Args:
                ticket_number (str): Ticket number of the project to delete (is schema_name_pruned)

            """
            try:
                dir_manager = DirectoryManager(ticket_number, main_dir)
                dir_manager.delete_dir(main_dir / 'projects' / ticket_number)
            except Exception as e:
                logger.error(f'Error deleting project directory for {ticket_number}: {e}')

        delete_project_directory(schema_name_pruned)
        delete_schema(schema_name_pruned)
        return True, f'Project {schema_name_pruned} deleted successfully'

    @staticmethod
    async def save_curation_report(items: list) -> None:
        """Save curation report to Word."""
        ui.notify('Curation report saved successfully!', type='positive')

    @staticmethod
    def export_yaml_ui(duckdb: DuckDB, dir_manager: DirectoryManager) -> None:
        """Export YAML file from the project directory."""
        exporter = Exporter(duckdb, dir_manager)
        exporter.export_yaml()
        ui.notify('YAML exported successfully!', type='positive')
