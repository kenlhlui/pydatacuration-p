"""The new dataset setup page."""

import asyncio
from pathlib import Path
from urllib.parse import quote

from nicegui import app
from nicegui import ui

from pydatacuration.backend.models.app_settings import AppSettings
from pydatacuration.backend.models.setup_form import SetupDefaults
from pydatacuration.backend.models.setup_form import SetupForm
from pydatacuration.backend.services.curation import run_curation
from pydatacuration.exceptions import DatasetAccessError
from pydatacuration.exceptions import DatasetNotFoundError
from pydatacuration.exceptions import DatasetUnauthorizedError
from pydatacuration.exceptions import DirectoryExistsError
from pydatacuration.frontend.styles import apply_pdc_styles
from pydatacuration.frontend.styles import create_checklist_select


app_settings = AppSettings()
setup_defaults = SetupDefaults()
default_form = SetupForm(**setup_defaults.model_dump(), main_dir=app_settings.main_dir)
RES_DIR = Path(app_settings.res_dir)


def handle_back_navigation(back_button: ui.button) -> None:
    """Handle back button navigation."""
    # Disable button during navigation
    back_button.set_enabled(False)
    ui.navigate.to('/')


async def handle_setup_submit(  # noqa: PLR0913, PLR0917
    form_data: dict,
    error_msg: ui.label,
    success_msg: ui.label,
    loading_spinner: ui.element,
    loading_label: ui.label,
    start_button: ui.button,
    reset_button: ui.button,
    back_button: ui.button,
) -> None:
    """Handle form submission."""
    # Validate the form data
    if not form_data.get('checklist'):
        ui.notify('Please select a valid checklist', type='negative', position='top-right', close_button=True)
        return

    # Disable all buttons and show loading
    start_button.set_enabled(False)
    reset_button.set_enabled(False)
    back_button.set_enabled(False)
    loading_spinner.classes(remove='hidden')
    error_msg.classes(add='hidden')
    success_msg.classes(add='hidden')

    # Run curation as a background task so the WebSocket connection stays alive
    # during long downloads. Polling via ui.timer keeps the connection active.
    task = asyncio.create_task(run_curation(SetupForm(**form_data)))

    def restore_buttons() -> None:
        start_button.set_enabled(True)
        reset_button.set_enabled(True)
        back_button.set_enabled(True)
        loading_spinner.classes(add='hidden')

    # Use a list so check_task can reference the timer before it's assigned
    poll_timer: list[ui.timer] = []
    start_time = [asyncio.get_running_loop().time()]

    def check_task() -> None:
        if not task.done():
            # Update label each tick — this sends a WebSocket message to keep the connection alive
            elapsed = int(asyncio.get_running_loop().time() - start_time[0])
            loading_label.set_text(f'Running curation process... ({elapsed}s)')
            return
        poll_timer[0].cancel()
        exc = task.exception()
        if exc is None:
            ui.navigate.to(f'/checklist?project_number={quote(form_data["project_number"])}')
        elif isinstance(exc, DirectoryExistsError):
            ui.notify(str(exc), type='warning')
            restore_buttons()
        elif isinstance(exc, DatasetUnauthorizedError):
            ui.notify('Unauthorized dataset access. Check API token/permissions.', type='negative')
            restore_buttons()
        elif isinstance(exc, DatasetNotFoundError):
            ui.notify('Dataset not found. Verify PID and base URL.', type='negative')
            restore_buttons()
        elif isinstance(exc, DatasetAccessError):
            ui.notify(str(exc), type='negative')
            restore_buttons()
        else:
            error_msg.set_text(f'Error: {exc}')
            error_msg.classes(remove='hidden', add='pdc-error')
            restore_buttons()

    poll_timer.append(ui.timer(1.0, check_task))


def reset_form(form_data: dict, default_form_data: dict, reset_button: ui.button) -> None:
    """Reset form to defaults."""
    # Disable button during reset
    reset_button.set_enabled(False)
    form_data.update(default_form_data)
    ui.notify('Form reset to defaults', type='info')
    # Re-enable button
    reset_button.set_enabled(True)


# ============================================================================
# New Dataset Setup Page
# ============================================================================
@ui.page('/new')
async def new_dataset_page() -> None:
    """New dataset setup page with exact CSS matching your current design."""
    # Enable the session storage for form persistence
    await ui.context.client.connected()

    # Apply our custom CSS
    apply_pdc_styles()

    with ui.column().classes('pdc-container-narrow'):
        # Logo
        ui.html(
            '<img src="/static/UTL.png" alt="University of Toronto Libraries Logo" class="utl-logo">',
            sanitize=False,
        )
        # Header
        ui.label(app_settings.app_title).classes('pdc-header')

        # Messages
        error_msg = ui.label().classes('hidden')
        success_msg = ui.label().classes('hidden')

        # Form state - automatically persisted
        # Initialize with environment variable defaults
        default_form_data = default_form.model_dump()

        # Get existing form data or create new
        form_data = app.storage.tab.setdefault('setup_form', default_form_data)

        # Update empty fields with environment variable defaults
        for key, default_value in default_form_data.items():
            if key not in form_data or not form_data.get(key):
                form_data[key] = default_value

        # Dataset Information Section
        with ui.element('div').classes('pdc-form-section'):
            ui.label('Dataset Information').classes('pdc-form-section-header')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Dataset PID *').classes('pdc-form-label')
                ui.input(placeholder='doi:10.5683/SP2/... or hdl:1902.1/...').classes(
                    'pdc-form-input w-full'
                ).bind_value(form_data, 'pid').style('width: 100%')
                ui.label('Persistent identifier for the dataset (DOI or Handle)').classes('pdc-form-helper')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Dataverse Base URL *').classes('pdc-form-label')
                ui.input(placeholder='https://demo.borealisdata.ca/').classes('pdc-form-input w-full').bind_value(
                    form_data, 'base_url'
                ).style('width: 100%')
                ui.label('Base URL of the Dataverse installation (e.g., https://demo.borealisdata.ca/)').classes(
                    'pdc-form-helper'
                )

            with ui.element('div').classes('pdc-form-group'):
                ui.label('API Token *').classes('pdc-form-label')
                ui.input(
                    placeholder='Enter your Dataverse API token', password=True, password_toggle_button=True
                ).props('autocorrect=off autocapitalize=off spellcheck=false').classes(
                    'pdc-form-input w-full'
                ).bind_value(form_data, 'api_token').style('width: 100%')
                ui.label('The API token from the Dataverse instance. The value is hidden by default.').classes(
                    'pdc-form-helper'
                )

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Project Number *').classes('pdc-form-label')
                ui.input(placeholder='PROJECT-123').classes('pdc-form-input w-full').bind_value(
                    form_data, 'project_number'
                ).style('width: 100%')
                ui.label('Identifier for the curation report (e.g., CUR-999)').classes('pdc-form-helper')

        # Curator Information Section
        with ui.element('div').classes('pdc-form-section'):
            ui.label('Curator Information').classes('pdc-form-section-header')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Curator Name *').classes('pdc-form-label')
                ui.input(placeholder='Enter your name').props('autocomplete=name').classes(
                    'pdc-form-input w-full'
                ).bind_value(form_data, 'curator_name').style('width: 100%')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Curator Email *').classes('pdc-form-label')
                ui.input(placeholder='Enter your email').classes('pdc-form-input w-full').props(
                    'type=email autocomplete=email'
                ).bind_value(form_data, 'curator_email').style('width: 100%')

        # # Directory Settings Section  # -- removed for now since we're defaulting to main_dir from .env and it can be confusing to have multiple directory fields. Can re-add later if needed --  # noqa: E501
        # with ui.element('div').classes('pdc-form-section'):
        #     ui.label('Directory Settings').classes('pdc-form-section-header')

        #     with ui.element('div').classes('pdc-form-group'):
        #         ui.label('Main Directory Path').classes('pdc-form-label')
        #         ui.input(placeholder='workdir').classes('pdc-form-input w-full').props(
        #             'spellcheck=false autocorrect=off autocapitalize=off'
        #         ).bind_value(form_data, 'main_dir').style('width: 100%')
        #         ui.label('Base directory where project folders and files will be created').classes('pdc-form-helper')

        # Checklist Selection Section
        with ui.element('div').classes('pdc-form-section'):
            ui.label('Checklist Selection').classes('pdc-form-section-header')

            with ui.element('div').classes('pdc-form-group'):
                # Use our custom checklist select with styling
                create_checklist_select(
                    res_dir=RES_DIR,
                    current_value=form_data.get('checklist', 'default'),
                    on_change=lambda e: form_data.update({'checklist': e.value}),
                ).style('width: 100%')
                ui.label('Checklist used for this curation project').classes('pdc-form-helper')

        # Processing Options Section
        with ui.element('div').classes('pdc-form-section'):
            ui.label('Processing Options').classes('pdc-form-section-header')

            with ui.row().classes('gap-4'):
                ui.checkbox(
                    'Delete existing project folder before starting', value=form_data.get('force_delete', False)
                ).bind_value(form_data, 'force_delete')
                ui.checkbox(
                    'Unzip archive files and check contents', value=form_data.get('check_zip', True)
                ).bind_value(form_data, 'check_zip')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Dataverse Collection Alias').classes('pdc-form-label')
                ui.input(placeholder='Enter dataverse collection alias').classes('pdc-form-input w-full').bind_value(
                    form_data, 'collection_alias'
                ).style('width: 100%')
                ui.label('Dataverse collection alias for checking dataset author and depositor history').classes(
                    'pdc-form-helper'
                )

        # Action buttons
        with ui.element('div').classes('pdc-actions'):
            start_button = ui.button(
                'Start Curation Process',
                on_click=lambda: handle_setup_submit(
                    form_data,
                    error_msg,
                    success_msg,
                    loading_spinner,
                    loading_label,
                    start_button,
                    reset_button,
                    back_button,
                ),
            ).classes('pdc-btn pdc-btn-primary')

            reset_button = ui.button(
                'Reset Form', on_click=lambda: reset_form(form_data, default_form_data, reset_button)
            ).classes('pdc-btn pdc-btn-secondary')

            back_button = ui.button('Back', on_click=lambda: handle_back_navigation(back_button), color='red').classes(
                'pdc-btn pdc-btn-secondary'
            )

        # Loading indicator
        with ui.element('div').classes('pdc-loading hidden') as loading_spinner:
            ui.element('div').classes('pdc-loading-spinner')
            loading_label = ui.label('Running curation process...')
