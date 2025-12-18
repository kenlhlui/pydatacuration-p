"""Helper functions for NiceGUI components."""

import re
import time
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any

import markdown2
from nicegui import app
from nicegui import ui
from sqlmodel import SQLModel

from pydatacuration.custom_logging import logger
from pydatacuration.custom_logging import setup_logging
from pydatacuration.directory_manager import DirectoryManager
from pydatacuration.duck_db import DuckDB
from pydatacuration.exporter import Exporter
from pydatacuration.sqlmodels import DuckDBmodels


setup_logging()

# Type alias for checklist items - uses dummy schema for type hints only
# The actual schema name will be provided at runtime
Checklist: type[SQLModel] = DuckDBmodels('_type_hints_').checklist()


class NiceGUIHelper:
    """Helper class for NiceGUI components."""

    def __init__(self, duckdb: DuckDB, ticket_number: str, refresh_callback: Callable | None = None) -> None:
        """Initialize NiceGUIHelper.

        Args:
            duckdb (DuckDB): Instance of DuckDB.
            ticket_number (str): Ticket number to work with.
            refresh_callback: Optional callback function to refresh the UI after updates.
        """
        self.duckdb: DuckDB = duckdb
        self.ticket_number: str = ticket_number
        self.refresh_callback = refresh_callback
        # Timer tracking: {item_id: {'start_time': timestamp, 'elapsed': seconds}}
        self.timers: dict[str, dict] = {}

    def get_checklist_items(self) -> list:
        """Get all checklist items from the DuckDB database for the specified ticket.

        The checklist type is determined by what was stored in the database during setup.

        Args:
            ticket_number (str): Ticket number to get checklist items for.

        Returns:
            list: List of checklist items with their details.

        """
        duck_db_data = self.duckdb.read_checklist(mode='python')
        items = []
        for item in duck_db_data.get('checklist', []):
            # Convert timedelta to MM:SS format for display
            # ! Temp fix for time_spent being stored as string in older DBs
            time_spent_value = item.get('time_spent', '')
            if isinstance(time_spent_value, timedelta):
                total_seconds = int(time_spent_value.total_seconds())
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                time_spent_display = f'{minutes:02d}:{seconds:02d}'
            else:
                time_spent_display = time_spent_value if time_spent_value else ''

            checklist_item = Checklist(
                id=item['id'],
                action=markdown2.markdown(item['action']) if item['action'] else '',
                instructions=markdown2.markdown(item['instructions']) if item['instructions'] else '',
                priority=item['priority'],
                section=item.get('section', ''),
                automated_check_ids=item.get('automated_check_ids', []),
                status=item.get('status', ''),
                comments=item.get('comments', ''),
                time_spent=time_spent_display,
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
        if self.refresh_callback:
            # Schedule the async callback to run
            ui.timer(0.0, self.refresh_callback, once=True)

    def handle_comments_change(self, item_id: str, new_comments: str) -> None:
        """Handle comments change."""
        self.duckdb.sql_update_checklist_item(item_id=item_id, comments=new_comments)
        ui.notify(f'Comments updated for {item_id}', type='positive', position='top-right', close_button=True)
        if self.refresh_callback:
            # Schedule the async callback to run
            ui.timer(0.0, self.refresh_callback, once=True)

    def handle_time_change(self, item_id: str, time_spent_input: str) -> None:
        """Handle time change with validation."""
        if self.validate_time_format(time_spent_input):
            # Turn the MM:SS string into a timedelta
            # Parse MM:SS format directly (e.g., "06:30" = 6 minutes, 30 seconds)
            parts = time_spent_input.split(':')
            minutes = int(parts[0])
            seconds = int(parts[1])
            time_spent_delta: timedelta = timedelta(minutes=minutes, seconds=seconds)
            self.duckdb.sql_update_checklist_item(item_id=item_id, time_spent=time_spent_delta)
            ui.notify(f'Time updated for {item_id}', type='positive', position='top-right', close_button=True)
            if self.refresh_callback:
                # Schedule the async callback to run
                ui.timer(0.0, self.refresh_callback, once=True)
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
        self.duckdb.sql_update_checklist_item(item_id=item_id, time_spent=time_delta)

        # Remove from active timers
        del self.timers[item_id]

        ui.notify(f'Timer stopped for {item_id}: {time_str}', type='positive', position='top-right', close_button=True)

        if self.refresh_callback:
            # Schedule the async callback to run
            ui.timer(0.0, self.refresh_callback, once=True)

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

            # Create a DuckDB instance to get schemas names for further querying
            duck_db = DuckDB(schema_name='_system_query_', db_file=db_file)
            schema_names = duck_db.get_all_schema_names()

            # Get additional project metadata for each schema
            project_metadata_schema = []
            for schema_name in schema_names:
                try:
                    # Try to get project metadata for last modified date
                    schema_duck_db = DuckDB(schema_name=schema_name, db_file=db_file)
                    project_metadata_record: dict[str, Any] = schema_duck_db.read_project_metadata_record(mode='python')

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
                    project_metadata_schema.append(
                        {
                            'ticket_number': schema_name.replace('duckdb.', '').replace('"', ''),
                            'name': schema_name,
                            'last_modified': 'Unknown',
                            'has_metadata': False,
                        }
                    )

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
                duck_db = DuckDB(schema_name='_system_query_', db_file=db_file)

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
    def export_word_button(
        duckdb: DuckDB, dir_manager: DirectoryManager, word_template_name: str | None = None
    ) -> None:
        """Save curation report to Word."""
        exporter = Exporter(duckdb, dir_manager)
        exporter.export_word(word_template_name=word_template_name)

        ui.notify('Curation report saved successfully!', type='positive')

    @staticmethod
    def export_yaml_button(duckdb: DuckDB, dir_manager: DirectoryManager) -> None:
        """Export YAML file from the project directory."""
        exporter = Exporter(duckdb, dir_manager)
        exporter.export_yaml()

        ui.notify('YAML exported successfully!', type='positive')


# ============================================================================
# Functions for returning dictionary for returning options
# ============================================================================


def status_options() -> dict[str, str]:
    """Get status options for select input."""
    return {
        '': 'Select status',
        'P': 'Passed',
        'F': 'Follow-up',
        'TBD': 'To Be Determined',
        'NA': 'Not Applicable',
    }


def priority_options() -> dict[str, str]:
    """Get priority options for select input."""
    return {
        '': 'Select priority',
        'Info': 'Info',
        'Required': 'Required',
        'Recommended': 'Recommended',
    }


def checklist_options() -> dict[str, str]:
    """Get checklist options for select input."""
    return {
        'high': 'High',
        'medium': 'Medium',
    }


def back_to_main_menu_button() -> None:
    """Create a centered 'Back to Main Menu' button."""
    with ui.row().classes('justify-left my-4'):
        ui.button('← Back', on_click=lambda: ui.navigate.to('/')).classes('pdc-btn pdc-btn-secondary')
