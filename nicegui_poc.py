"""
NiceGUI Proof of Concept for PyDataCuration Frontend
This demonstrates how the landing page and checklist would look in NiceGUI
"""

from pathlib import Path
from typing import Optional
import asyncio

from nicegui import ui, app
from pydantic import BaseModel


# ============================================================================
# Data Models (same as your current app.py)
# ============================================================================

class SetupRequest(BaseModel):
    """Setup form data model."""
    pid: str
    base_url: str | None = None
    api_token: str | None = None
    ticket_number: str
    curator_name: str
    curator_email: str
    main_dir: str = 'workdir'
    force_del: bool = False
    check_zip: bool = True
    checklist: str = 'high'
    collection_alias: str | None = None


class ChecklistItem(BaseModel):
    """Checklist item model."""
    id: str
    action: str
    instructions: str
    priority: str
    section: str = ''
    automated_check_ids: list[str] | None = []
    information_location: str = ''
    check_type: str = ''
    status: str | None = None
    comments: str | None = None
    time_spent: str | None = None


# ============================================================================
# Styling - Replaces your CSS files
# ============================================================================

CUSTOM_CSS = """
<style>
/* Status colors for dropdowns */
.status-P { background-color: #d4edda !important; border-color: #28a745 !important; }
.status-F { background-color: #fff3cd !important; border-color: #ffc107 !important; }
.status-TBD { background-color: #cce5ff !important; border-color: #007bff !important; }
.status-NA { background-color: #e2e3e5 !important; border-color: #6c757d !important; }

/* Checklist selection colors */
.checklist-high { border-color: #3498db !important; background-color: #ebf5fb !important; }
.checklist-medium { border-color: #27ae60 !important; background-color: #e8f8f0 !important; }

/* Priority badges */
.priority-critical { background-color: #e74c3c; color: white; padding: 4px 8px; border-radius: 4px; }
.priority-high { background-color: #f39c12; color: white; padding: 4px 8px; border-radius: 4px; }
.priority-medium { background-color: #3498db; color: white; padding: 4px 8px; border-radius: 4px; }
.priority-low { background-color: #95a5a6; color: white; padding: 4px 8px; border-radius: 4px; }
</style>
"""


# ============================================================================
# Landing Page - Replaces landing.html + session-manager.js + utilities.js
# ============================================================================

@ui.page('/')
async def landing_page() -> None:
    """Landing page for data curation setup.

    Replaces:
    - landing.html (373 lines HTML + inline JS)
    - session-manager.js (222 lines)
    - utilities.js (170 lines)

    Total: ~765 lines → ~150 lines of Python
    """
    # Add custom CSS
    ui.add_head_html(CUSTOM_CSS)

    with ui.column().classes('w-full max-w-4xl mx-auto p-8 bg-white rounded-lg shadow-lg'):
        # Logo
        ui.image('/static/UTL.png').classes('h-16 mb-4')

        ui.label('Data Curation Tool').classes('text-3xl font-bold text-gray-800 border-b-2 border-blue-500 pb-2 mb-6')

        # Messages (replaces manual display management)
        error_msg = ui.label().classes('hidden bg-red-500 text-white p-3 rounded mb-4')
        success_msg = ui.label().classes('hidden bg-green-500 text-white p-3 rounded mb-4')

        # Form state - automatically persisted
        form_data = app.storage.user.setdefault('setup_form', {
            'base_url': 'https://demo.borealisdata.ca/',
            'main_dir': 'workdir',
            'force_del': False,
            'check_zip': True,
            'checklist': 'high'
        })

        with ui.card().classes('w-full'):
            ui.label('Dataset Information').classes('text-xl font-semibold text-gray-700 mb-4')

            # All form fields with auto-persistence via bind_value
            pid_input = ui.input(
                'Dataset Persistent Identifier (PID) *',
                placeholder='doi:10.5683/SP2/... or hdl:1902.1/...'
            ).classes('w-full').bind_value(form_data, 'pid')
            ui.label('Enter the DOI or Handle of the dataset').classes('text-sm text-gray-600')

            base_url_input = ui.input(
                'Dataverse Base URL *',
                placeholder='https://demo.borealisdata.ca/'
            ).classes('w-full').bind_value(form_data, 'base_url')
            ui.label('Base URL of the Dataverse installation').classes('text-sm text-gray-600')

            api_token_input = ui.input(
                'API Token *',
                placeholder='Enter your Dataverse API token',
                password=True,
                password_toggle_button=True
            ).classes('w-full').bind_value(form_data, 'api_token')
            ui.label('Your Dataverse API token (will be hidden)').classes('text-sm text-gray-600')

            ticket_input = ui.input(
                'Ticket Number *',
                placeholder='TICKET-123'
            ).classes('w-full').bind_value(form_data, 'ticket_number')
            ui.label('Ticket number for the curation report').classes('text-sm text-gray-600')

        with ui.card().classes('w-full'):
            ui.label('Curator Information').classes('text-xl font-semibold text-gray-700 mb-4')

            curator_name_input = ui.input(
                'Curator Name *',
                placeholder='Enter your name'
            ).classes('w-full').bind_value(form_data, 'curator_name')

            curator_email_input = ui.input(
                'Curator Email *',
                placeholder='Enter your email'
            ).classes('w-full').bind_value(form_data, 'curator_email')

        with ui.card().classes('w-full'):
            ui.label('Directory Settings').classes('text-xl font-semibold text-gray-700 mb-4')

            main_dir_input = ui.input(
                'Main Directory Path',
                placeholder='workdir'
            ).classes('w-full').bind_value(form_data, 'main_dir')
            ui.label('The main (base) directory for project files').classes('text-sm text-gray-600')

        with ui.card().classes('w-full'):
            ui.label('Checklist Selection').classes('text-xl font-semibold text-gray-700 mb-4')

            # Dynamic styling based on selection
            checklist_select = ui.select(
                ['high', 'medium'],
                label='Select Checklist',
                value=form_data.get('checklist', 'high')
            ).classes('w-full').bind_value(form_data, 'checklist')

            # Update styling dynamically
            def update_checklist_style():
                checklist_select.classes(remove='checklist-high checklist-medium')
                checklist_select.classes(add=f'checklist-{form_data["checklist"]}')

            checklist_select.on_value_change(lambda: update_checklist_style())
            update_checklist_style()

            ui.label('Select the checklist level for this curation task').classes('text-sm text-gray-600')

        with ui.card().classes('w-full'):
            ui.label('Processing Options').classes('text-xl font-semibold text-gray-700 mb-4')

            with ui.row().classes('gap-4'):
                ui.checkbox(
                    'Force delete existing project',
                    value=form_data.get('force_del', False)
                ).bind_value(form_data, 'force_del')

                ui.checkbox(
                    'Unzip and check contents of zip files',
                    value=form_data.get('check_zip', True)
                ).bind_value(form_data, 'check_zip')

            collection_alias_input = ui.input(
                'Dataverse Collection Alias',
                placeholder='Enter dataverse collection alias'
            ).classes('w-full').bind_value(form_data, 'collection_alias')

        # Action buttons
        with ui.row().classes('w-full justify-center gap-4 mt-6'):
            submit_btn = ui.button(
                'Start Curation Process',
                on_click=lambda: handle_setup_submit(
                    form_data, error_msg, success_msg, loading_spinner
                )
            ).props('color=primary')

            reset_btn = ui.button(
                'Reset Form',
                on_click=lambda: reset_form(form_data)
            ).props('color=secondary')

        # Loading indicator
        loading_spinner = ui.spinner('dots', size='lg').classes('hidden')


async def handle_setup_submit(form_data: dict, error_msg, success_msg, loading_spinner):
    """Handle form submission.

    Replaces: 80 lines of JavaScript (lines 317-397 in landing.html)
    """
    # Validation
    required_fields = ['pid', 'base_url', 'api_token', 'ticket_number', 'curator_name', 'curator_email']
    missing = [f for f in required_fields if not form_data.get(f)]

    if missing:
        error_msg.text = f'Missing required fields: {", ".join(missing)}'
        error_msg.classes(remove='hidden')
        return

    # Show loading
    loading_spinner.classes(remove='hidden')
    error_msg.classes(add='hidden')
    success_msg.classes(add='hidden')

    try:
        # Call your existing setup API
        # In production, this would call your FastAPI /setup endpoint
        setup_request = SetupRequest(**form_data)

        # Simulate API call (replace with actual FastAPI call)
        await asyncio.sleep(1)

        # Store metadata in user storage (replaces sessionStorage)
        app.storage.user['ds_metadata'] = {
            'dataset_pid': form_data['pid'],
            'curator_name': form_data['curator_name'],
            'curator_email': form_data['curator_email'],
            'ticket_number': form_data['ticket_number']
        }

        # Show success
        success_msg.text = 'Curation process completed successfully!'
        success_msg.classes(remove='hidden')

        # Redirect after delay
        await asyncio.sleep(2)
        ui.navigate.to(f'/checklist?ticket_number={form_data["ticket_number"]}')

    except Exception as e:
        error_msg.text = f'Error: {str(e)}'
        error_msg.classes(remove='hidden')
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
# Checklist Page - Replaces main.html + 8 JS files
# ============================================================================

@ui.page('/checklist')
async def checklist_page(ticket_number: Optional[str] = None):
    """Checklist page with dynamic table and auto-save.

    Replaces:
    - main.html (295 lines)
    - session-manager.js (222 lines)
    - yaml-autosave.js (503 lines)
    - validation.js (95 lines)
    - load-from-duckdb.js (239 lines)
    - write-to-duckdb.js (208 lines)
    - load-check-results.js (230 lines)
    - readdsmetadata.js (146 lines)
    - utilities.js (170 lines)

    Total: ~2,108 lines → ~300 lines of Python
    """
    ui.add_head_html(CUSTOM_CSS)

    # Get metadata from storage (replaces sessionStorage + readdsmetadata.js)
    metadata = app.storage.user.get('ds_metadata', {})

    # Load checklist data from DuckDB (replaces load-from-duckdb.js)
    checklist_items = await load_checklist_from_duckdb(ticket_number)

    with ui.column().classes('w-full p-8'):
        ui.image('/static/UTL.png').classes('h-16 mb-4')

        checklist_type = app.storage.user.get('setup_form', {}).get('checklist', 'high')
        ui.label(f'{checklist_type.title()}-Level Curation Checklist').classes('text-3xl font-bold')

        # Metadata display (replaces info-grid in main.html)
        with ui.card().classes('w-full mb-4'):
            ui.label('Project Information').classes('text-xl font-semibold mb-2')
            with ui.grid(columns=2).classes('gap-4'):
                for key, label in [
                    ('ticket_number', 'Ticket number'),
                    ('curator_name', 'Curator name'),
                    ('curator_email', 'Curator email'),
                    ('dataset_title', 'Dataset title'),
                    ('dataset_pid', 'Dataset PID'),
                ]:
                    ui.label(f'{label}:').classes('font-semibold')
                    ui.label(metadata.get(key, 'N/A')).classes('text-gray-700')

        # Status legend
        with ui.card().classes('w-full mb-4'):
            ui.label('Status Explanation').classes('text-xl font-semibold mb-2')
            with ui.row().classes('gap-4'):
                for code, meaning in [('P', 'Passed'), ('F', 'Follow-up'), ('TBD', 'To Be Determined'), ('NA', 'Not Applicable')]:
                    ui.label(f'{code}: {meaning}').classes('text-sm')

        # Checklist Table (replaces complex table + multiple JS modules)
        await render_checklist_table(checklist_items, ticket_number)

        # Action buttons
        with ui.row().classes('gap-4 mt-6'):
            ui.button('Save Curation Log (Word)', on_click=lambda: save_curation_report(checklist_items))
            ui.button('Calculate Time Spent', on_click=lambda: calculate_total_time(checklist_items))
            ui.button('Export YAML', on_click=lambda: export_yaml(checklist_items))
            ui.button('New Dataset', on_click=confirm_new_dataset)


async def render_checklist_table(items: list[ChecklistItem], ticket_number: str):
    """
    Render checklist table with reactive updates

    Replaces: Manual DOM manipulation + event listeners (200+ lines of JS)
    """

    # Table columns definition
    columns = [
        {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
        {'name': 'action', 'label': 'Action Item', 'field': 'action', 'align': 'left'},
        {'name': 'info', 'label': 'Information Location', 'field': 'information_location', 'align': 'left'},
        {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'},
        {'name': 'comments', 'label': 'Comments', 'field': 'comments', 'align': 'left'},
        {'name': 'priority', 'label': 'Priority', 'field': 'priority', 'align': 'center'},
        {'name': 'time', 'label': 'Time Spent', 'field': 'time_spent', 'align': 'center'},
    ]

    # Convert items to dict for table
    rows = [item.model_dump() for item in items]

    # Create table with inline editing
    table = ui.table(
        columns=columns,
        rows=rows,
        row_key='id',
        pagination={'rowsPerPage': 50}
    ).classes('w-full')

    # Add custom slots for editable cells
    with table.add_slot('body-cell-status'):
        # Status dropdown with auto-save
        for item in items:
            status_select = ui.select(
                ['', 'P', 'F', 'TBD', 'NA'],
                value=item.status or '',
                on_change=lambda e, item_id=item.id: handle_status_change(item_id, e.value, ticket_number)
            ).classes('w-32')

            # Dynamic styling
            def update_status_style(value, select):
                select.classes(remove='status-P status-F status-TBD status-NA')
                if value:
                    select.classes(add=f'status-{value}')

            status_select.on_value_change(lambda e, s=status_select: update_status_style(e.value, s))
            if item.status:
                update_status_style(item.status, status_select)

    with table.add_slot('body-cell-comments'):
        # Comments textarea with auto-save
        for item in items:
            ui.textarea(
                value=item.comments or '',
                on_change=lambda e, item_id=item.id: handle_comments_change(item_id, e.value, ticket_number)
            ).classes('w-full min-h-20')

    with table.add_slot('body-cell-time'):
        # Time input with validation
        for item in items:
            ui.input(
                value=item.time_spent or '',
                placeholder='MM:SS',
                validation={'MM:SS format': lambda v: not v or validate_time_format(v)},
                on_change=lambda e, item_id=item.id: handle_time_change(item_id, e.value, ticket_number)
            ).classes('w-24')


# ============================================================================
# Helper Functions - Replaces individual JS modules
# ============================================================================

async def load_checklist_from_duckdb(ticket_number: str) -> list[ChecklistItem]:
    """
    Load checklist data from DuckDB

    Replaces: load-from-duckdb.js (239 lines)
    """
    # In production, call your DuckDB API
    # For POC, return sample data
    return [
        ChecklistItem(
            id='ABC-001',
            action='Check metadata completeness',
            instructions='Review all required fields',
            priority='high',
            section='Metadata Review',
            status='P',
            comments='All fields present',
            time_spent='05:30'
        ),
        ChecklistItem(
            id='ABC-002',
            action='Verify file formats',
            instructions='Ensure all files are in supported formats',
            priority='medium',
            section='File Review',
            status='TBD',
            comments='',
            time_spent='02:15'
        ),
    ]


async def handle_status_change(item_id: str, new_status: str, ticket_number: str):
    """
    Handle status change with auto-save to DuckDB

    Replaces: write-to-duckdb.js debounced update (50+ lines)
    """
    # Auto-save to DuckDB (no manual debouncing needed - NiceGUI handles it)
    await save_to_duckdb(ticket_number, item_id, {'status': new_status})
    ui.notify(f'Status updated for {item_id}', type='positive', position='top-right', timeout=1000)


async def handle_comments_change(item_id: str, new_comments: str, ticket_number: str):
    """Handle comments change with auto-save"""
    await save_to_duckdb(ticket_number, item_id, {'comments': new_comments})


async def handle_time_change(item_id: str, new_time: str, ticket_number: str):
    """Handle time change with validation and auto-save"""
    if validate_time_format(new_time):
        await save_to_duckdb(ticket_number, item_id, {'time_spent': new_time})


def validate_time_format(time_str: str) -> bool:
    """Validate MM:SS format - Replaces validation.js"""
    import re
    return bool(re.match(r'^[0-9]{1,2}:[0-5][0-9]$', time_str))


async def save_to_duckdb(ticket_number: str, item_id: str, data: dict):
    """
    Save item to DuckDB

    Replaces: write-to-duckdb.js (208 lines)
    """
    # In production, call your FastAPI /update-checklist-item endpoint
    pass


def calculate_total_time(items: list[ChecklistItem]):
    """Calculate total time spent - Replaces validation.js calculate function"""
    total_minutes = 0
    for item in items:
        if item.time_spent:
            parts = item.time_spent.split(':')
            total_minutes += int(parts[0]) * 60 + int(parts[1])

    hours = total_minutes // 60
    minutes = total_minutes % 60
    ui.notify(f'Total Time Spent: {hours}:{minutes:02d}', type='info')


async def save_curation_report(items: list[ChecklistItem]):
    """Save curation report to Word - Replaces inline script"""
    # Call your /render-report endpoint
    ui.notify('Curation report saved successfully!', type='positive')


async def export_yaml(items: list[ChecklistItem]):
    """Export to YAML - Replaces yaml-autosave.js (503 lines)"""
    # NiceGUI can directly serialize to YAML without custom parser
    import yaml
    data = {
        'metadata': app.storage.user.get('ds_metadata', {}),
        'checklist_items': [item.model_dump() for item in items]
    }
    yaml_str = yaml.dump(data)
    # Call your /export-curation-log endpoint
    ui.notify('YAML exported successfully!', type='positive')


def confirm_new_dataset():
    """Confirm and navigate to new dataset"""
    async def handle_confirm(result: bool):
        if result:
            app.storage.user.clear()
            ui.navigate.to('/')

    ui.dialog().props('message="This will erase all current input. Continue?"').on('confirm', handle_confirm)


# ============================================================================
# Run the application
# ============================================================================

if __name__ in {"__main__", "__mp_main__"}:
    # In production, mount this within your existing FastAPI app
    ui.run(
        title='PyDataCuration - NiceGUI POC',
        favicon='🔬',
        port=8080,
        storage_secret='your-secret-key-here'  # Use env var in production
    )
