"""NiceGUI Proof of Concept - With Production-Ready Styling
This version uses the nicegui_styles module for exact CSS matching
"""

import asyncio
import re
from pathlib import Path
from typing import Optional

from nicegui import app
from nicegui import app as nicegui_app
from nicegui import ui
from pydantic import BaseModel

from nicegui_styles import PDCStyles

# Import our custom styling
from nicegui_styles import apply_pdc_styles
from nicegui_styles import create_checklist_select
from nicegui_styles import create_info_grid
from nicegui_styles import create_priority_badge
from nicegui_styles import create_status_select


# ============================================================================
# Data Models
# ============================================================================

class SetupRequest(BaseModel):
    """Setup form data model"""
    pid: str
    base_url: Optional[str] = None
    api_token: Optional[str] = None
    ticket_number: str
    curator_name: str
    curator_email: str
    main_dir: str = 'workdir'
    force_del: bool = False
    check_zip: bool = True
    checklist: str = 'high'
    collection_alias: Optional[str] = None


class ChecklistItem(BaseModel):
    """Checklist item model"""
    id: str
    action: str
    instructions: str
    priority: str
    section: str = ''
    automated_check_ids: Optional[list[str]] = []
    information_location: str = ''
    check_type: str = ''
    status: Optional[str] = None
    comments: Optional[str] = None
    time_spent: Optional[str] = None


# ============================================================================
# Landing Page
# ============================================================================

@ui.page('/')
async def landing_page():
    """
    Landing page with exact CSS matching your current design
    """
    # Apply our custom CSS
    apply_pdc_styles()

    with ui.column().classes('pdc-container').style('width: 100%; max-width: 800px;'):
        # Logo
        ui.html(
            '<img src="/static/UTL.png" '
            'alt="University of Toronto Libraries Logo" '
            'class="pdc-logo" '
            'style="height: 60px; width: auto; margin: 8px;">'
        )

        # Header
        ui.label('Data Curation Tool').classes('pdc-header')

        # Messages
        error_msg = ui.label().classes('hidden')
        success_msg = ui.label().classes('hidden')

        # Form state - automatically persisted
        form_data = app.storage.user.setdefault('setup_form', {
            'base_url': 'https://demo.borealisdata.ca/',
            'main_dir': 'workdir',
            'force_del': False,
            'check_zip': True,
            'checklist': 'high'
        })

        # Dataset Information Section
        with ui.element('div').classes('pdc-form-section').style('width: 100%;'):
            ui.label('Dataset Information').classes('text-lg font-semibold text-gray-700').style('margin-bottom: 12px;')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Dataset Persistent Identifier (PID) *').classes('pdc-form-label')
                ui.input(
                    placeholder='doi:10.5683/SP2/... or hdl:1902.1/...'
                ).classes('pdc-form-input w-full').bind_value(form_data, 'pid').style('width: 100%')
                ui.label('Enter the DOI or Handle of the dataset').classes('pdc-form-helper')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Dataverse Base URL *').classes('pdc-form-label')
                ui.input(
                    placeholder='https://demo.borealisdata.ca/'
                ).classes('pdc-form-input w-full').bind_value(form_data, 'base_url').style('width: 100%')
                ui.label('Base URL of the Dataverse installation').classes('pdc-form-helper')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('API Token *').classes('pdc-form-label')
                ui.input(
                    placeholder='Enter your Dataverse API token',
                    password=True,
                    password_toggle_button=True
                ).classes('pdc-form-input w-full').bind_value(form_data, 'api_token').style('width: 100%')
                ui.label('Your Dataverse API token (will be hidden)').classes('pdc-form-helper')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Ticket Number *').classes('pdc-form-label')
                ui.input(
                    placeholder='TICKET-123'
                ).classes('pdc-form-input w-full').bind_value(form_data, 'ticket_number').style('width: 100%')
                ui.label('Ticket number for the curation report').classes('pdc-form-helper')

        # Curator Information Section
        with ui.element('div').classes('pdc-form-section').style('width: 100%;'):
            ui.label('Curator Information').classes('text-lg font-semibold text-gray-700').style('margin-bottom: 12px;')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Curator Name *').classes('pdc-form-label')
                ui.input(
                    placeholder='Enter your name'
                ).classes('pdc-form-input w-full').bind_value(form_data, 'curator_name').style('width: 100%')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Curator Email *').classes('pdc-form-label')
                ui.input(
                    placeholder='Enter your email'
                ).classes('pdc-form-input w-full').bind_value(form_data, 'curator_email').style('width: 100%')

        # Directory Settings Section
        with ui.element('div').classes('pdc-form-section').style('width: 100%;'):
            ui.label('Directory Settings').classes('text-lg font-semibold text-gray-700').style('margin-bottom: 12px;')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Main Directory Path').classes('pdc-form-label')
                ui.input(
                    placeholder='workdir'
                ).classes('pdc-form-input w-full').bind_value(form_data, 'main_dir').style('width: 100%')
                ui.label('The main (base) directory for project files').classes('pdc-form-helper')

        # Checklist Selection Section
        with ui.element('div').classes('pdc-form-section').style('width: 100%;'):
            ui.label('Checklist Selection').classes('text-lg font-semibold text-gray-700').style('margin-bottom: 12px;')

            with ui.element('div').classes('pdc-form-group'):
                # Use our custom checklist select with styling
                create_checklist_select(
                    current_value=form_data.get('checklist', 'high'),
                    on_change=lambda e: form_data.update({'checklist': e.value})
                ).style('width: 100%')
                ui.label('Select the checklist level for this curation task').classes('pdc-form-helper')

        # Processing Options Section
        with ui.element('div').classes('pdc-form-section').style('width: 100%;'):
            ui.label('Processing Options').classes('text-lg font-semibold text-gray-700').style('margin-bottom: 12px;')

            with ui.row().classes('gap-4'):
                ui.checkbox(
                    'Force delete existing project',
                    value=form_data.get('force_del', False)
                ).bind_value(form_data, 'force_del')

                ui.checkbox(
                    'Unzip and check contents of zip files',
                    value=form_data.get('check_zip', True)
                ).bind_value(form_data, 'check_zip')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Dataverse Collection Alias').classes('pdc-form-label')
                ui.input(
                    placeholder='Enter dataverse collection alias'
                ).classes('pdc-form-input w-full').bind_value(form_data, 'collection_alias').style('width: 100%')

        # Action buttons
        with ui.element('div').classes('pdc-actions'):
            ui.button(
                'Start Curation Process',
                on_click=lambda: handle_setup_submit(form_data, error_msg, success_msg, loading_spinner)
            ).classes('pdc-btn pdc-btn-primary')

            ui.button(
                'Reset Form',
                on_click=lambda: reset_form(form_data)
            ).classes('pdc-btn pdc-btn-secondary')

        # Loading indicator
        with ui.element('div').classes('pdc-loading hidden') as loading_spinner:
            ui.element('div').classes('pdc-loading-spinner')
            ui.label('Running curation process...')


async def handle_setup_submit(form_data: dict, error_msg, success_msg, loading_spinner):
    """Handle form submission"""
    # Validation
    required_fields = ['pid', 'base_url', 'api_token', 'ticket_number', 'curator_name', 'curator_email']
    missing = [f for f in required_fields if not form_data.get(f)]

    if missing:
        error_msg.set_text(f'Missing required fields: {", ".join(missing)}')
        error_msg.classes(remove='hidden', add='pdc-error')
        return

    # Show loading
    loading_spinner.classes(remove='hidden')
    error_msg.classes(add='hidden')
    success_msg.classes(add='hidden')

    try:
        # In production, call your FastAPI /setup endpoint
        setup_request = SetupRequest(**form_data)

        # Simulate API call
        await asyncio.sleep(1)

        # Store metadata (replaces sessionStorage)
        app.storage.user['ds_metadata'] = {
            'dataset_pid': form_data['pid'],
            'curator_name': form_data['curator_name'],
            'curator_email': form_data['curator_email'],
            'ticket_number': form_data['ticket_number']
        }

        # Show success
        success_msg.set_text('Curation process completed successfully!')
        success_msg.classes(remove='hidden', add='pdc-success')

        # Redirect
        await asyncio.sleep(2)
        ui.navigate.to(f'/checklist?ticket_number={form_data["ticket_number"]}')

    except Exception as e:
        error_msg.set_text(f'Error: {str(e)}')
        error_msg.classes(remove='hidden', add='pdc-error')
    finally:
        loading_spinner.classes(add='hidden')


def reset_form(form_data: dict):
    """Reset form to defaults"""
    form_data.clear()
    form_data.update({
        'base_url': 'https://demo.borealisdata.ca/',
        'main_dir': 'workdir',
        'force_del': False,
        'check_zip': True,
        'checklist': 'high'
    })
    ui.notify('Form reset to defaults', type='info')


# ============================================================================
# Checklist Page
# ============================================================================

@ui.page('/checklist')
async def checklist_page(ticket_number: Optional[str] = None):
    """
    Checklist page with exact styling match
    """
    apply_pdc_styles()

    # Get metadata from storage
    metadata = app.storage.user.get('ds_metadata', {})
    checklist_type = app.storage.user.get('setup_form', {}).get('checklist', 'high')

    # Load checklist data
    checklist_items = await load_checklist_from_duckdb(ticket_number)

    with ui.column().classes('pdc-container'):
        # Logo
        ui.html(
            '<img src="/static/UTL.png" '
            'alt="University of Toronto Libraries Logo" '
            'class="pdc-logo" '
            'style="height: 60px; width: auto; margin: 8px;">'
        )

        # Header
        ui.label(f'{checklist_type.title()}-Level Curation Checklist').classes('pdc-header')

        # Metadata Display using our helper function
        create_info_grid(metadata, [
            ('ticket_number', 'Ticket number'),
            ('curator_name', 'Curator name'),
            ('curator_email', 'Curator email'),
            ('dataset_title', 'Dataset title'),
            ('dataset_pid', 'Dataset persistent identifier'),
            ('dataset_id', 'Dataset ID (versioned)'),
            ('dataset_url', 'Dataset access URL'),
            ('dataset_path', 'Dataset Path'),
        ])

        # Status Legend
        with ui.element('div').classes('pdc-status-legend'):
            ui.label('Status Explanation').classes('text-xl font-semibold')
            with ui.element('div').classes('pdc-status-list'):
                for code, meaning in [
                    ('P', 'Passed'),
                    ('F', 'Follow-up'),
                    ('TBD', 'To Be Determined'),
                    ('NA', 'Not Applicable')
                ]:
                    with ui.element('div').classes('pdc-status-item'):
                        ui.label(f'{code}:').classes('pdc-status-code')
                        ui.label(f' {meaning}')

        # Checklist Table
        await render_checklist_table(checklist_items, ticket_number)

        # Action Buttons
        with ui.element('div').classes('pdc-actions'):
            ui.button(
                'Save Curation Log (Word)',
                on_click=lambda: save_curation_report(checklist_items)
            ).classes('pdc-btn pdc-btn-primary')

            ui.button(
                'Calculate Time Spent',
                on_click=lambda: calculate_total_time(checklist_items)
            ).classes('pdc-btn pdc-btn-calculate')

            ui.button(
                'Export YAML',
                on_click=lambda: export_yaml(checklist_items)
            ).classes('pdc-btn pdc-btn-secondary')

            ui.button(
                'New Dataset',
                on_click=confirm_new_dataset
            ).classes('pdc-btn pdc-btn-danger')


async def render_checklist_table(items: list[ChecklistItem], ticket_number: str):
    """Render checklist table with exact styling"""

    with ui.element('table').classes('pdc-checklist-table'):
        # Table Header
        with ui.element('thead'):
            with ui.element('tr'):
                for header in ['ID', 'Action Item', 'Information Location', 'Status', 'Curator\'s Comments', 'Priority', 'Time Spent']:
                    with ui.element('th'):
                        ui.html(header)

        # Table Body
        with ui.element('tbody'):
            current_section = None

            for item in items:
                # Section header row
                if item.section != current_section:
                    current_section = item.section
                    with ui.element('tr'):
                        with ui.element('td').props('colspan=7').classes('pdc-section-header'):
                            ui.html(item.section)

                # Item row
                with ui.element('tr').props(f'data-item-id="{item.id}"'):
                    # ID
                    with ui.element('td').classes('pdc-item-id'):
                        ui.html(item.id)

                    # Action & Instructions
                    with ui.element('td').classes('details-cell'):
                        with ui.element('div').classes('pdc-action-item'):
                            ui.html(item.action)
                        if item.instructions:
                            with ui.element('div').classes('pdc-instructions-header'):
                                ui.html('Guidance:')
                            ui.html(item.instructions).classes('pdc-instructions')

                    # Information Location
                    with ui.element('td').classes('information-location-column'):
                        with ui.element('div').classes('pdc-automated-check-cell'):
                            if item.information_location:
                                ui.html(item.information_location).classes('pdc-static-info-location')

                    # Status
                    with ui.element('td'):
                        create_status_select(
                            item.id,
                            item.status or '',
                            on_change=lambda e, iid=item.id: handle_status_change(iid, e.value, ticket_number)
                        )

                    # Comments
                    with ui.element('td'):
                        ui.textarea(
                            value=item.comments or '',
                            placeholder="Curator's comments..."
                        ).classes('pdc-comments-input').on(
                            'change',
                            lambda e, iid=item.id: handle_comments_change(iid, e.sender.value, ticket_number)
                        )

                    # Priority
                    with ui.element('td'):
                        with ui.element('div').classes('pdc-priority-badge-container'):
                            create_priority_badge(item.priority)

                    # Time Spent
                    with ui.element('td'):
                        ui.input(
                            value=item.time_spent or '',
                            placeholder='MM:SS'
                        ).classes('pdc-time-input').on(
                            'change',
                            lambda e, iid=item.id: handle_time_change(iid, e.sender.value, ticket_number)
                        ).props('maxlength=5')


# ============================================================================
# Helper Functions
# ============================================================================

async def load_checklist_from_duckdb(ticket_number: str) -> list[ChecklistItem]:
    """Load checklist data from DuckDB"""
    # Sample data for POC
    return [
        ChecklistItem(
            id='ABC-001',
            action='Check metadata completeness',
            instructions='Review all required fields for completeness and accuracy.',
            priority='required',
            section='Metadata Review',
            status='P',
            comments='All fields are complete',
            time_spent='05:30',
            information_location='<p>Check the <strong>Metadata</strong> tab in Dataverse</p>'
        ),
        ChecklistItem(
            id='ABC-002',
            action='Verify file formats',
            instructions='Ensure all files are in supported and appropriate formats.',
            priority='recommended',
            section='File Review',
            status='TBD',
            comments='',
            time_spent='02:15',
            information_location='<p>See <em>Files</em> section for list of formats</p>'
        ),
        ChecklistItem(
            id='ABC-003',
            action='Check documentation completeness',
            instructions='Verify README and codebook are present and complete.',
            priority='required',
            section='Documentation',
            status='F',
            comments='Missing codebook for variable X',
            time_spent='10:45',
            information_location=''
        ),
    ]


async def handle_status_change(item_id: str, new_status: str, ticket_number: str):
    """Handle status change with auto-save"""
    await save_to_duckdb(ticket_number, item_id, {'status': new_status})
    ui.notify(f'Status updated for {item_id}', type='positive', position='top-right', close_button=True)


async def handle_comments_change(item_id: str, new_comments: str, ticket_number: str):
    """Handle comments change"""
    await save_to_duckdb(ticket_number, item_id, {'comments': new_comments})


async def handle_time_change(item_id: str, new_time: str, ticket_number: str):
    """Handle time change with validation"""
    if validate_time_format(new_time):
        await save_to_duckdb(ticket_number, item_id, {'time_spent': new_time})
    else:
        ui.notify('Please enter time in MM:SS format', type='negative')


def validate_time_format(time_str: str) -> bool:
    """Validate MM:SS format"""
    return bool(re.match(r'^[0-9]{1,2}:[0-5][0-9]$', time_str)) if time_str else True


async def save_to_duckdb(ticket_number: str, item_id: str, data: dict):
    """Save item to DuckDB"""
    # In production, call your /update-checklist-item endpoint
    print(f"Saving to DuckDB: ticket={ticket_number}, item={item_id}, data={data}")


def calculate_total_time(items: list[ChecklistItem]):
    """Calculate total time spent"""
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


async def save_curation_report(items: list[ChecklistItem]):
    """Save curation report to Word"""
    ui.notify('Curation report saved successfully!', type='positive')


async def export_yaml(items: list[ChecklistItem]):
    """Export to YAML"""
    import yaml
    data = {
        'metadata': app.storage.user.get('ds_metadata', {}),
        'checklist_items': [item.model_dump() for item in items]
    }
    yaml_str = yaml.dump(data)
    print("YAML Export:")
    print(yaml_str)
    ui.notify('YAML exported successfully!', type='positive')


def confirm_new_dataset():
    """Confirm and navigate to new dataset"""
    async def handle_confirm():
        app.storage.user.clear()
        ui.navigate.to('/')

    with ui.dialog() as dialog:
        with ui.card():
            ui.label('This will erase all current input. Continue?')
            with ui.row():
                ui.button('Yes', on_click=lambda: [dialog.close(), handle_confirm()])
                ui.button('No', on_click=dialog.close)
    dialog.open()


# ============================================================================
# Static Files Setup - Must be BEFORE ui.run()
# ============================================================================

# Mount static files from your existing frontend directory
# Determine the correct path to static files
static_path = Path('pydatacuration/frontend')
if not static_path.exists():
    static_path = Path(__file__).parent / 'pydatacuration' / 'frontend'

if static_path.exists():
    # Add static files route
    nicegui_app.add_static_files('/static', str(static_path))
    print('✓ Static files mounted:', static_path.absolute())
else:
    print('⚠ WARNING: Static directory not found!')
    print('  Looked for:', static_path.absolute())


# ============================================================================
# Run the application
# ============================================================================

if __name__ in {'__main__', '__mp_main__'}:
    ui.run(
        title='PyDataCuration - Styled POC',
        favicon='🔬',
        port=8080,
        storage_secret='your-secret-key-here'
    )
