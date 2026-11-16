"""The new dataset setup page."""

import asyncio
from html import escape
from pathlib import Path
from urllib.parse import quote

from nicegui import ui

from pydatacuration.backend.models.app_settings import AppSettings
from pydatacuration.backend.models.setup_form import SetupDefaults
from pydatacuration.backend.models.setup_form import SetupForm
from pydatacuration.backend.models.setup_form import validate_setup_form_input
from pydatacuration.backend.services.curation import run_curation
from pydatacuration.exceptions import DirectoryExistsError
from pydatacuration.exceptions import describe_error
from pydatacuration.frontend.helpers import create_checklist_select
from pydatacuration.frontend.helpers import project_number_rule
from pydatacuration.frontend.reusable_elements import action_button

# Import reusable UI elements
from pydatacuration.frontend.reusable_elements import form_section
from pydatacuration.frontend.reusable_elements import scroll_to_top_button
from pydatacuration.frontend.reusable_elements import text_input_box

# Import styles and custom components
from pydatacuration.frontend.styles import apply_pdc_styles

# Import the message catalogue
from pydatacuration.i18n import t


app_settings = AppSettings()
setup_defaults = SetupDefaults()
default_form = SetupForm(**setup_defaults.model_dump(), main_dir=app_settings.main_dir)
RES_DIR = Path(app_settings.res_dir)


def resolve_form_data(form_data: dict) -> dict:
    """Return form data with api_token resolved from environment if left blank."""
    resolved = dict(form_data)
    if not resolved.get('api_token') and setup_defaults.api_token:
        resolved['api_token'] = str(setup_defaults.api_token)
    return resolved


def handle_back_navigation(back_button: ui.button) -> None:
    """Handle back button navigation."""
    # Disable button during navigation
    back_button.set_enabled(False)
    ui.navigate.to('/')


async def handle_setup_submit(  # noqa: PLR0913, PLR0917
    form_data: dict,
    validated_inputs: list[ui.input],
    success_msg: ui.label,
    loading_section: ui.element,
    loading_label: ui.label,
    start_button: ui.button,
    reset_button: ui.button,
    back_button: ui.button,
) -> None:
    """Handle form submission."""
    # Validate all inputs and block if any fail
    # FIXME: This should combine with the checklist check below.
    if not all(i.validate() for i in validated_inputs):
        ui.notify(t('setup.fix_form_errors'), type='negative', position='top-right', close_button=True)
        return

    # FIXME: This should algin with the validation logic above.
    if not form_data.get('checklist'):
        ui.notify(t('setup.select_checklist'), type='negative', position='top-right', close_button=True)
        return

    # Disable all buttons and show loading
    start_button.set_enabled(False)
    reset_button.set_enabled(False)
    back_button.set_enabled(False)
    loading_section.set_visibility(True)
    success_msg.classes(add='hidden')

    # Run curation as a background task so the WebSocket connection stays alive
    # during long downloads. Polling via ui.timer keeps the connection active.
    task = asyncio.create_task(run_curation(SetupForm(**resolve_form_data(form_data))))

    def restore_buttons() -> None:
        start_button.set_enabled(True)
        reset_button.set_enabled(True)
        back_button.set_enabled(True)
        loading_section.set_visibility(False)

    # Use a list so check_task can reference the timer before it's assigned
    poll_timer: list[ui.timer] = []
    start_time = [asyncio.get_running_loop().time()]

    def check_task() -> None:
        if not task.done():
            # Update label each tick — this sends a WebSocket message to keep the connection alive
            elapsed = int(asyncio.get_running_loop().time() - start_time[0])
            loading_label.set_text(t('setup.running', elapsed=elapsed))
            return
        poll_timer[0].cancel()
        exc = task.exception()
        if exc is None:
            ui.navigate.to(f'/checklist?project_number={quote(form_data["project_number"])}')
            return
        # Stays until closed, so the reference ID can be read and reported
        ui.notify(
            describe_error(exc),
            type='warning' if isinstance(exc, DirectoryExistsError) else 'negative',
            timeout=0,
            close_button=True,
        )
        restore_buttons()

    poll_timer.append(ui.timer(1.0, check_task))


def reset_form(form_data: dict, default_form_data: dict, reset_button: ui.button) -> None:
    """Reset form to defaults."""
    # Disable button during reset
    reset_button.set_enabled(False)
    form_data.update(default_form_data)
    ui.notify(t('setup.form_reset'), type='info')
    # Re-enable button
    reset_button.set_enabled(True)


# ============================================================================
# New Dataset Setup Page
# ============================================================================
@ui.page('/new')
async def new_dataset_page() -> None:  # noqa: PLR0914
    """New dataset setup page with exact CSS matching your current design."""
    # Enable the session storage for form persistence
    await ui.context.client.connected()

    # Apply our custom CSS
    apply_pdc_styles()

    # Apply the scroll to top button
    scroll_to_top_button()

    with ui.column().classes('pdc-container-narrow'):
        # Logo
        ui.html(
            f'<img src="/static/UTL.png" alt="{escape(t("common.logo_alt"))}" class="utl-logo">',
            sanitize=False,
        )
        # Header
        ui.label(app_settings.app_title).classes('pdc-header')

        # Messages
        success_msg = ui.label().classes('hidden')

        # Form state - fresh defaults on every visit to this page.
        # Initialize with environment variable defaults, but strip api_token so
        # the secret is never sent to the browser — resolved server-side at submit.
        default_form_data = default_form.model_dump()
        default_form_data['api_token'] = ''
        form_data = dict(default_form_data)

        # Dataset Information Section
        with form_section(t('setup.section_dataset')):
            _input_pid = text_input_box(
                label=t('setup.pid_label'),
                form_data=form_data,
                key='pid',
                placeholder=t('setup.pid_placeholder'),
                validation=validate_setup_form_input(SetupForm, 'pid', required=True),
                helper_text=t('setup.pid_helper'),
            )

            _input_base_url = text_input_box(
                label=t('setup.base_url_label'),
                form_data=form_data,
                key='base_url',
                placeholder=t('setup.base_url_placeholder'),
                validation=validate_setup_form_input(
                    SetupForm, 'base_url', required=True, invalid_message=t('setup.base_url_invalid')
                ),
                helper_text=t('setup.base_url_helper'),
            )

            _has_env_token = setup_defaults.api_token is not None
            _token_placeholder = (
                t('setup.api_token_placeholder_prefilled') if _has_env_token else t('setup.api_token_placeholder')
            )
            _helper = t('setup.api_token_helper_prefilled') if _has_env_token else t('setup.api_token_helper')
            _api_token_rule = validate_setup_form_input(
                SetupForm, 'api_token', invalid_message=t('setup.api_token_invalid')
            )
            _input_api_token = text_input_box(
                label=t('setup.api_token_label'),
                form_data=form_data,
                key='api_token',
                placeholder=_token_placeholder,
                validation=lambda v: _api_token_rule(v) if v else None,
                helper_text=_helper,
                props='autocorrect=off autocapitalize=off spellcheck=false',
                password=True,
                password_toggle_button=True,
            )

            _input_project_number = text_input_box(
                label=t('setup.project_number_label'),
                form_data=form_data,
                key='project_number',
                placeholder=t('setup.project_number_placeholder'),
                validation=project_number_rule,
                helper_text=t('setup.project_number_helper'),
            )

        # Curator Information Section
        with form_section(t('setup.section_curator')):
            _input_curator_name = text_input_box(
                label=t('setup.curator_name_label'),
                form_data=form_data,
                key='curator_name',
                placeholder=t('setup.curator_name_placeholder'),
                validation=validate_setup_form_input(SetupForm, 'curator_name', required=True),
                helper_text=t('setup.curator_name_helper'),
            )

            _input_curator_email = text_input_box(
                label=t('setup.curator_email_label'),
                form_data=form_data,
                key='curator_email',
                placeholder=t('setup.curator_email_placeholder'),
                validation=validate_setup_form_input(
                    SetupForm, 'curator_email', required=True, invalid_message=t('setup.curator_email_invalid')
                ),
                helper_text=t('setup.curator_email_helper'),
                props='type=email autocomplete=email',
            )

        validated_inputs = [
            _input_pid,
            _input_base_url,
            _input_api_token,
            _input_project_number,
            _input_curator_email,
            _input_curator_name,
        ]

        # Checklist Selection Section
        with form_section(t('setup.section_checklist')), ui.element('div').classes('pdc-form-group'):
            # Use our custom checklist select with styling
            create_checklist_select(
                res_dir=RES_DIR,
                current_value=form_data.get('checklist', 'default'),
                on_change=lambda e: form_data.update({'checklist': e.value}),
            ).bind_value(form_data, 'checklist').style('width: 100%')
            ui.label(t('setup.checklist_helper')).classes('pdc-form-helper')

        # Processing Options Section
        with form_section(t('setup.section_processing')):
            with ui.row().classes('gap-4'):
                ui.checkbox(t('setup.replace_existing'), value=form_data.get('force_delete', False)).bind_value(
                    form_data, 'force_delete'
                )
                ui.checkbox(t('setup.check_zip'), value=form_data.get('check_zip', True)).bind_value(
                    form_data, 'check_zip'
                )

            text_input_box(
                label=t('setup.collection_alias_label'),
                form_data=form_data,
                key='collection_alias',
                placeholder=t('setup.collection_alias_placeholder'),
                helper_text=t('setup.collection_alias_helper'),
            )

        # Loading indicator (hidden by default)
        with ui.column().classes('w-full items-center') as loading_section:
            with ui.row().classes('items-center justify-center gap-2'):
                ui.spinner(size='lg').classes('')
            loading_label = ui.label(t('setup.generating_report')).classes('text-lg')
        loading_section.set_visibility(False)

        # Action buttons
        with ui.element('div').classes('pdc-actions'):
            back_button = action_button(
                t('setup.back'), on_click=lambda: handle_back_navigation(back_button), color='red'
            )

            reset_button = action_button(
                t('setup.reset_form'), on_click=lambda: reset_form(form_data, default_form_data, reset_button)
            )

            start_button = action_button(
                t('setup.start'),
                on_click=lambda: handle_setup_submit(
                    form_data,
                    validated_inputs,
                    success_msg,
                    loading_section,
                    loading_label,
                    start_button,
                    reset_button,
                    back_button,
                ),
            )
