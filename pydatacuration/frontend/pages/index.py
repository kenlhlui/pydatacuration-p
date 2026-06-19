"""The home page of the application, providing options to start a new project, resume work, or delete a project."""

from nicegui import ui

from pydatacuration.backend.models.app_settings import AppSettings
from pydatacuration.frontend.styles import MAIN_PAGE_HEAD_CSS
from pydatacuration.frontend.styles import apply_pdc_styles


# ============================================================================
# Main Entrance Page
# ============================================================================


app_settings = AppSettings()


@ui.page('/')
async def main_page() -> None:
    """Main entrance page to start new project, resume work, or delete project."""
    apply_pdc_styles()

    # Add custom CSS for main page
    ui.add_head_html(MAIN_PAGE_HEAD_CSS)

    with ui.column().classes('main-container'):
        # Logo and Header
        ui.html(
            '<img src="/static/UTL.png" alt="University of Toronto Libraries Logo" class="utl-logo">',
            sanitize=False,
        )
        ui.label(
            app_settings.app_title,
        ).classes('pdc-header')

        # Top row options
        with ui.element('div').classes('options-grid'):
            # New Project Option
            with ui.element('div').classes('option-card').on('click', lambda: ui.navigate.to('/new')):
                ui.markdown('📁').classes('icon')
                ui.markdown('New Project').classes('option-title')
                ui.markdown(
                    'Start a new curation process for a new project',
                ).classes('option-description')

            # Delete Project Option
            with ui.element('div').classes('option-card').on('click', lambda: ui.navigate.to('/delete')):
                ui.markdown('🗑️').classes('icon')
                ui.markdown('Delete Project').classes('option-title')
                ui.markdown('Delete a project from the database').classes('option-description')

        # Resume Work Option (centered)
        with (
            ui.element('div').classes('resume-container'),
            ui.element('div').classes('option-card resume-card').on('click', lambda: ui.navigate.to('/resume')),
        ):
            ui.markdown('✏️').classes('icon')
            ui.markdown('Resume Project').classes('option-title')
            ui.markdown('Continue working on an existing project').classes('option-description')
