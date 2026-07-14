"""Helper functions for NiceGUI components."""

import re
import time
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any

from loguru import logger
from nicegui import app
from nicegui import ui
from sqlmodel import SQLModel

from pydatacuration.checklist.utils import discover_checklist_files
from pydatacuration.db import DatabaseBackend
from pydatacuration.db import DBModels
from pydatacuration.db import get_database
from pydatacuration.db import get_db_type
from pydatacuration.services.exporter import Exporter
from pydatacuration.utils.directory_manager import DirectoryManager
from pydatacuration.utils.utils import validate_project_number


# Type alias for checklist items - uses dummy schema for type hints only
# The actual schema name will be provided at runtime
Checklist: type[SQLModel] = DBModels('_type_hints_').checklist()


class NiceGUIHelper:  # noqa: PLR0904
    """Helper class for NiceGUI components."""

    def __init__(self, db: DatabaseBackend, project_number: str) -> None:
        """Initialize NiceGUIHelper.

        Args:
            db (DatabaseBackend): Database backend instance.
            project_number (str): Project number to work with.
        """
        self.db: DatabaseBackend = db
        self.project_number: str = project_number
        # Timer tracking: {item_id: {'start_time': timestamp, 'elapsed': seconds}}
        self.timers: dict[str, dict] = {}
        self.refresh_callback: Callable | None = None

    def get_checklist_items(self) -> list[SQLModel]:
        """Get all checklist items from the database database for the specified project.

        The checklist type is determined by what was stored in the database during setup.

        Args:
            project_number (str): Project number to get checklist items for.

        Returns:
            Sequence[SQLModel]: List of checklist items with their details.

        """
        checklist_items = self.db.read_checklist()

        # Change the timedelta to MM:SS format for each item to prevent JSON serialization issues
        for item in checklist_items:
            time_spent = item.time_spent
            if isinstance(time_spent, timedelta):
                total_seconds = int(time_spent.total_seconds())
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                item.time_spent = f'{minutes}:{seconds:02d}'
            elif time_spent is None:
                item.time_spent = ''

        return checklist_items

    def handle_status_change(self, item_id: str, new_status: str) -> None:
        """Handle status change with auto-save."""
        self.db.update_checklist_item(item_id=item_id, status=new_status)
        ui.notify(f'Status updated for {item_id}', type='positive', position='top-right', close_button=True)
        if self.refresh_callback:
            self.refresh_callback()

    def handle_comments_change(self, item_id: str, new_comments: str) -> None:
        """Handle comments change."""
        self.db.update_checklist_item(item_id=item_id, comments=new_comments)
        ui.notify(f'Comments updated for {item_id}', type='positive', position='top-right', close_button=True)
        if self.refresh_callback:
            self.refresh_callback()

    def handle_time_change(self, item_id: str, time_spent_input: str) -> None:
        """Handle time change with validation."""
        if not time_spent_input:
            self.db.update_checklist_item(item_id=item_id, clear_time_spent=True)
            ui.notify(f'Time cleared for {item_id}', type='positive', position='top-right', close_button=True)
            if self.refresh_callback:
                self.refresh_callback()
        elif self.validate_time_format(time_spent_input):
            parts = time_spent_input.split(':')
            time_spent_delta: timedelta = timedelta(minutes=int(parts[0]), seconds=int(parts[1]))
            self.db.update_checklist_item(item_id=item_id, time_spent=time_spent_delta)
            ui.notify(f'Time updated for {item_id}', type='positive', position='top-right', close_button=True)
            if self.refresh_callback:
                self.refresh_callback()
        else:
            ui.notify('Please enter time in MM:SS format', type='negative')

    def render_status_progress(self, color_map: dict[str, tuple[str, str]] | None = None) -> None:
        """Render circular progress indicators for each status count."""
        status_counts = self.db.get_status_count()
        total = sum(status_counts.values())

        for status, count in status_counts.items():
            label = status or 'No Status'
            value = round((count / total * 100), 1) if total > 0 else 0
            # color_map maps status label → (bg_color, text_color); fall back to 'primary'
            color = color_map[label][0] if (color_map and label in color_map) else 'primary'
            with ui.column().classes('flex-1 items-center gap-1'):
                ui.circular_progress(value=value, min=0, max=100, size='120px', color=color)
                ui.label(f'{label} ({count})').classes('text-sm text-center')

    def render_comment_input_counter(self) -> None:
        """Render comment input counter."""
        comment_input_count = self.db.get_comment_input_count()
        total_items = len(self.get_checklist_items())
        comment_input_counter = f'{comment_input_count}/{total_items}' if total_items > 0 else '0/0'
        with ui.column().classes('flex-1 items-center gap-1'):
            with ui.element('div').classes('flex items-center justify-center').style('height: 120px'):
                ui.label(f'{comment_input_counter}').classes('text-5xl font-bold text-center w-full')
            ui.label('Comments input').classes('text-sm text-center')

    def _get_time_spent_input_count(self) -> str:
        """Get count of checklist items that have time spent input.

        Return:
            str: A string in the format "X/Y" where X is the count of items with time spent input and Y is the total number of items.

        """  # noqa: E501
        time_spent_count = self.db.get_time_spent_input_count()
        items = self.get_checklist_items()

        counter = f'{time_spent_count}/{len(items)}' if items else '0/0'
        return counter

    def get_total_time_str(self) -> str:
        """Return total time spent across all checklist items as H:MM string."""
        items = self.get_checklist_items()
        total_seconds = 0
        for item in items:
            if item.time_spent:
                try:
                    parts = item.time_spent.split(':')
                    total_seconds += int(parts[0]) * 60 + int(parts[1])
                except (ValueError, IndexError):
                    continue
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f'{hours:02d}:{minutes:02d}:{seconds:02d}'

    @staticmethod
    def validate_time_format(time_str: str) -> bool:
        """Validate MM:SS format."""
        return bool(re.match(r'^[0-9]{1,2}:[0-5][0-9]$', time_str)) if time_str else True

    def is_timer_running(self, item_id: str) -> bool:
        """Check if a timer is currently running for an item.

        Args:
            item_id (str): The checklist item ID to check.

        Returns:
            bool: True if timer is running, False otherwise.
        """
        return item_id in self.timers

    def start_timer(self, item_id: str, time_input: ui.input | None = None) -> None:
        """Start a timer for a specific checklist item.

        Args:
            item_id (str): The checklist item ID to start timer for.
            time_input (ui.input | None): Optional input field to update in real-time.
        """
        if item_id in self.timers:
            ui.notify(f'Timer already running for {item_id}', type='warning')
            return

        self.timers[item_id] = {'start_time': time.time(), 'elapsed': 0, 'input': time_input}
        ui.notify(f'Timer started for {item_id}', type='positive', position='top-right', close_button=True)

        # Start a background timer to update the display every second
        if time_input:
            self._update_timer_display(item_id)

    def _update_timer_display(self, item_id: str) -> None:
        """Update the timer display every second.

        Args:
            item_id (str): The checklist item ID to update display for.
        """
        if item_id not in self.timers:
            return

        timer_data = self.timers[item_id]
        elapsed_seconds = int(time.time() - timer_data['start_time']) + timer_data['elapsed']
        time_str = self.format_elapsed_time(elapsed_seconds)

        # Update the input field if available
        if timer_data.get('input'):
            timer_data['input'].value = time_str

        # Schedule next update if timer is still running
        if item_id in self.timers:
            ui.timer(1.0, lambda: self._update_timer_display(item_id), once=True)

    def stop_timer(self, item_id: str, time_input: ui.input | None = None) -> None:
        """Stop a timer and save the elapsed time.

        Args:
            item_id (str): The checklist item ID to stop timer for.
            time_input (ui.input | None): The input field to update with the elapsed time.
        """
        if item_id not in self.timers:
            ui.notify(f'No timer running for {item_id}', type='warning')
            return

        timer_data = self.timers[item_id]
        elapsed_seconds = int(time.time() - timer_data['start_time']) + timer_data['elapsed']

        # Convert to MM:SS format for display
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        time_str = f'{minutes}:{seconds:02d}'

        # Update the input field
        if time_input:
            time_input.value = time_str

        # Save to database as timedelta
        time_delta = timedelta(seconds=elapsed_seconds)
        self.db.update_checklist_item(item_id=item_id, time_spent=time_delta)

        # Remove from active timers
        del self.timers[item_id]

        ui.notify(f'Timer stopped for {item_id}: {time_str}', type='positive', position='top-right', close_button=True)
        if self.refresh_callback:
            self.refresh_callback()

    def toggle_timer(self, item_id: str, time_input: ui.input, button: ui.button) -> None:
        """Toggle timer start/stop for a checklist item.

        Args:
            item_id (str): The checklist item ID.
            time_input (ui.input): The input field to update with elapsed time.
            button (ui.button): The button to update icon/color.
        """
        if self.is_timer_running(item_id):
            # Stop the timer
            self.stop_timer(item_id, time_input)
            # Update button to "Start" state
            button.props('icon=play_arrow color=positive')
            button._props['icon'] = 'play_arrow'
            button.update()
        else:
            # Start the timer
            self.start_timer(item_id, time_input)
            # Update button to "Stop" state
            button.props('icon=stop color=negative')
            button._props['icon'] = 'stop'
            button.update()

    @staticmethod
    def format_elapsed_time(elapsed_seconds: int) -> str:
        """Format elapsed seconds into MM:SS format.

        Args:
            elapsed_seconds (int): Number of elapsed seconds.

        Returns:
            str: Time formatted as MM:SS.
        """
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        return f'{minutes}:{seconds:02d}'

    @staticmethod
    def confirm_new_dataset() -> None:
        """Confirm and navigate to new dataset."""

        def handle_confirm() -> None:
            app.storage.user.clear()
            ui.navigate.to('/')

        with ui.dialog() as dialog, ui.card().style('min-width: 400px;'):
            ui.label('This will redirect to the new dataset page. Continue?').classes('text-xl font-semibold')
            with ui.row().classes('w-full justify-end gap-2').style('margin-top: 20px;'):
                ui.button('Continue', color='red', on_click=lambda: [dialog.close(), handle_confirm()]).classes(
                    'pdc-btn'
                )
                ui.button('Cancel', on_click=dialog.close).classes('pdc-btn')
        dialog.open()

    @staticmethod
    def get_all_schemas(main_dir: Path) -> list[dict]:
        """Get all available schemas (projects) from the database.

        Returns:
            list[dict]: List of schemas with metadata
        """
        try:
            backend = get_db_type()

            # For DuckDB, we need the file to exist
            db_file: Path | None = None
            if backend == 'duckdb':
                db_dir = Path(main_dir) / 'db'
                db_file = db_dir / DirectoryManager.DB_FILE_NAME
                if not db_file.exists():
                    return []

            # Create a database backend instance to get schema names for further querying
            db = get_database(schema_name='_system_query_', db_file=db_file)
            schema_names = db.get_all_schema_names()

            # Get additional project metadata for each schema
            project_metadata_schema = []
            for schema_name in schema_names:
                try:
                    # Try to get project metadata for last modified date
                    schema_db = get_database(schema_name=schema_name, db_file=db_file)
                    project_metadata_record: dict[str, Any] = schema_db.read_project_metadata_record(mode='python')

                    # Turn the last_modified_datetime into a YYYY-MM-DD HH:MM:SS format
                    last_modified_dt = project_metadata_record.get('last_modified_datetime')
                    last_modified_display = (
                        last_modified_dt.strftime('%Y-%m-%d %H:%M:%S') if last_modified_dt else 'Unknown'
                    )  # noqa: E501

                    project_metadata_record['last_modified'] = last_modified_display

                    # Append to the list
                    project_metadata_schema.append(project_metadata_record)

                except Exception as e:
                    logger.error(f'Could not get metadata for schema {schema_name}: {e}')
                    project_metadata_schema.append({
                        'project_number': schema_name.replace('duckdb.', '').replace('"', ''),
                        'name': schema_name,
                        'last_modified': 'Unknown',
                        'has_metadata': False,
                    })

            # Sort by last modified (most recent first)
            project_metadata_schema.sort(key=lambda x: x['last_modified'], reverse=True)

            return project_metadata_schema

        except Exception as e:
            logger.error(f'Error fetching schemas: {e}')
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
            """Delete a specific schema from the database.

            Args:
                schema_name_pruned (str): Name of the schema to delete (without duckdb. prefix)

            Returns:
                tuple[bool, str]: Success status and message
            """
            try:
                from pydatacuration.db import get_db_type

                backend = get_db_type()

                db_file: Path | None = None
                if backend == 'duckdb':
                    db_dir = Path(main_dir) / DirectoryManager.DB_SUBDIR
                    db_file = db_dir / DirectoryManager.DB_FILE_NAME
                    if not db_file.exists():
                        return False, 'Database file not found'

                # Create a database backend instance to delete the schema
                db = get_database(schema_name='_system_query_', db_file=db_file)

                # Delete the schema
                db.drop_schema(schema_name_pruned)

                return True, f'Schema {schema_name_pruned} deleted successfully'

            except Exception as e:
                return False, f'Error deleting schema: {str(e)}'

        def delete_project_directory(project_number: str) -> None:
            """Delete the project directory for a specific project number.

            Args:
                project_number (str): Project number of the project to delete (is schema_name_pruned)

            """
            try:
                dir_manager = DirectoryManager(main_dir=main_dir, project_number=project_number)
                dir_manager.delete_dir(main_dir / 'projects' / project_number)
            except Exception as e:
                logger.error(f'Error deleting project directory for {project_number}: {e}')

        delete_project_directory(schema_name_pruned)
        delete_schema(schema_name_pruned)
        return True, f'Project {schema_name_pruned} deleted successfully'

    @staticmethod
    def export_word(db: DatabaseBackend, dir_manager: DirectoryManager, word_template_name: str | None = None) -> None:
        """Save curation report to Word."""
        exporter = Exporter(db, dir_manager)
        exporter.export_word(word_template_name=word_template_name)
        docx_file_name = exporter.get_docx_file_name()

        ui.download.file(
            Path(dir_manager.outputs_dir, 'curation_report.docx'),
            docx_file_name,
        )

        ui.notify('Curation report saved successfully!', type='positive')

    @staticmethod
    def export_yaml_button(db: DatabaseBackend, dir_manager: DirectoryManager) -> None:
        """Export YAML file from the project directory."""
        exporter = Exporter(db, dir_manager)
        exporter.export_yaml()

        ui.notify('YAML exported successfully!', type='positive')


# ============================================================================
# Functions for returning dictionary for returning options
# ============================================================================


def checklist_options(res_dir: Path) -> dict[str, str]:
    """Get checklist options for select input by discovering available checklist files.

    Returns:
        dict[str, str]: Dictionary mapping checklist identifiers to display names.
    """
    # Discover available checklist files
    options = discover_checklist_files(res_dir)

    # Add blank option as the first option
    return {'': 'Select checklist', **options}


def back_to_main_menu_button() -> None:
    """Create a centered 'Back to Main Menu' button."""
    with ui.row().classes('justify-left my-4'):
        ui.button('← Back', on_click=lambda: ui.navigate.to('/')).classes('pdc-btn')


# ============================================================================
# Validation functions for NiceGUI inputs
# ============================================================================
def project_number_rule(v: str) -> str | None:
    """Validate project number input for NiceGUI forms.

     - Must not be empty
     - Must match the expected format (validated by validate_project_number)

    Args:
        v (str): The project number input value.

    Returns:
        str | None: An error message if validation fails, or None if validation passes.
    """
    if not v:
        return 'This field is required'
    try:
        validate_project_number(v)
        return None
    except ValueError as e:
        return str(e)
