"""Utility functions for project management pages."""

from pathlib import Path

from nicegui import ui

from pydatacuration.backend.models.app_settings import AppSettings
from pydatacuration.frontend.helpers import NiceGUIHelper
from pydatacuration.frontend.reusable_elements import action_button
from pydatacuration.i18n import t


# Create global settings instance
app_settings = AppSettings()

# Load environment variables
MAIN_DIR: Path = Path(app_settings.main_dir)


def confirm_delete_project(schema: dict, refresh_callback) -> None:
    """Show confirmation dialog before deleting a project."""

    async def handle_delete() -> None:
        success, message = NiceGUIHelper.delete_project(schema.get('project_number'), MAIN_DIR)
        dialog.close()
        if success:
            ui.notify(message, type='positive')
            await refresh_callback()
        else:
            ui.notify(message, type='negative')

    with ui.dialog() as dialog, ui.card().style('min-width: min(400px, 90vw);'):
        ui.label(t('projects.confirm_delete_title', project_number=schema['project_number'])).classes(
            'text-xl font-semibold'
        )
        ui.label(t('projects.confirm_delete_warning')).classes('text-red-600')

        with ui.row().classes('w-full justify-end gap-2').style('margin-top: 20px;'):
            action_button(t('projects.confirm_delete_button'), on_click=handle_delete, color='red')
            action_button(t('common.cancel'), on_click=dialog.close)

    dialog.open()
