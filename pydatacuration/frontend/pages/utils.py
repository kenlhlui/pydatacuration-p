"""Utility functions for project management pages."""

from pathlib import Path

from nicegui import ui

from pydatacuration.backend.models.app_settings import AppSettings
from pydatacuration.frontend.helpers import NiceGUIHelper


# Create global settings instance
app_settings = AppSettings()

# Load environment variables
MAIN_DIR: Path = Path(app_settings.main_dir)


def confirm_delete_project(schema: dict, refresh_callback) -> None:
    """Show confirmation dialog before deleting a project."""

    async def handle_delete() -> None:
        success, message = NiceGUIHelper.delete_project(schema.get('project_number'), MAIN_DIR)
        if success:
            ui.notify(message, type='positive')
            await refresh_callback()
            dialog.close()
        else:
            ui.notify(message, type='negative')
            dialog.close()

    with ui.dialog() as dialog, ui.card().style('min-width: 400px;'):
        ui.label(f'Delete project "{schema["project_number"]}"?').classes('text-xl font-semibold')
        ui.label('This action cannot be undone. All data will be permanently deleted.').classes('text-red-600')

        with ui.row().classes('w-full justify-end gap-2').style('margin-top: 20px;'):
            ui.button('Cancel', on_click=dialog.close).classes('pdc-btn pdc-btn-secondary')
            ui.button('Delete', color='red', on_click=handle_delete).classes('pdc-btn pdc-btn-danger')

    dialog.open()
