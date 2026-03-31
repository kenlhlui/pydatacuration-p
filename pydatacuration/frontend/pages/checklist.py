"""Checklist page implementation for pydatacuration frontend."""

# ruff: noqa: PLR1702
from pathlib import Path

from nicegui import ui

from pydatacuration.backend.models.app_settings import AppSettings

# Import the options models and loaders
from pydatacuration.checklist.priority_options import load_priority_options
from pydatacuration.db import DatabaseBackend
from pydatacuration.db import get_database

# Import exceptions for error handling
from pydatacuration.frontend.helpers import NiceGUIHelper
from pydatacuration.frontend.models.status_options import load_status_options

# Import styles and styled components
from pydatacuration.frontend.styles import apply_pdc_styles
from pydatacuration.frontend.styles import create_check_type_badge
from pydatacuration.frontend.styles import create_info_grid
from pydatacuration.frontend.styles import create_priority_badge
from pydatacuration.frontend.styles import create_status_select

# Import pydatacuration modules
from pydatacuration.utils.directory_manager import DirectoryManager


# Create global settings instance
app_settings = AppSettings()

# Load environment variables
MAIN_DIR: Path = Path(app_settings.main_dir)
RES_DIR = Path(app_settings.res_dir)


# ============================================================================
# Checklist Page
# ============================================================================


@ui.page('/checklist')
async def checklist_page(project_number: str) -> None:
    """Checklist page with exact styling match."""
    apply_pdc_styles()

    # Initialize the db connection for this project number
    dir_manager = DirectoryManager(project_number, MAIN_DIR, RES_DIR)
    db = get_database(schema_name=project_number, db_file=dir_manager.db_path)
    helpers = NiceGUIHelper(db, project_number)

    # Load metadata from database
    project_metadata = db.read_project_metadata_record()
    checklist_type: str | None = project_metadata.get('checklist_type')

    # Load checklist results from database
    check_results = db.read_check_results()

    # Load the options for status and priority from the resource directory (with fallback to defaults)
    status_options = list(load_status_options(RES_DIR).model_dump(mode='python').values())
    priority_options = list(load_priority_options(RES_DIR).model_dump(mode='python').values())

    with ui.column().classes('pdc-container'):
        # Logo
        ui.html(
            '<img src="/static/UTL.png" alt="University of Toronto Libraries Logo" class="utl-logo">',
            sanitize=False,
        )
        # Header, with dynamic checklist type
        # FIXME: change to use the YAML model
        checklist_name = f'{checklist_type.title()}-Level ' if checklist_type else ''
        ui.label(f'{checklist_name}Curation Checklist').classes('pdc-header')

        # Metadata Display using our helper function
        create_info_grid(
            project_metadata,
            [
                ('project_number', 'Project number'),
                ('curator_name', 'Curator name'),
                ('curator_email', 'Curator email'),
                ('dataset_title', 'Dataset title'),
                ('dataset_pid', 'Dataset persistent identifier'),
                ('dataset_id', 'Dataset ID (versioned)'),
                ('dataset_url', 'Dataset access URL'),
                ('dataset_path', 'Dataset Path'),
            ],
        )

        # # Status Legend  # (commented out for cleaner UI); can be re-enabled for other content if needed
        # with ui.element('div').classes('pdc-status-legend'):
        #     ui.label('Status Explanation').classes('text-xl font-semibold')
        #     with ui.element('div').classes('pdc-status-list'):
        #         for code, meaning in [
        #             ('P', 'Passed'),
        #             ('F', 'Follow-up'),
        #             ('TBD', 'To Be Determined'),
        #             ('NA', 'Not Applicable'),
        #         ]:
        #             with ui.element('div').classes('pdc-status-item'):
        #                 ui.label(f'{code}:').classes('pdc-status-code')
        #                 ui.label(f' {meaning}')

        # Filters Section
        with ui.element('div').classes('pdc-form-section').style('width: 100%; margin-bottom: 20px;'):
            ui.label('Filters').classes('text-lg font-semibold text-gray-700').style('margin-bottom: 12px;')

            with ui.row().classes('gap-4').style('align-items: flex-end;'):
                # Status filter
                with ui.element('div').style('flex: 1; min-width: 200px;'):
                    ui.label('Filter by Status').classes('pdc-form-label')
                    status_filter = (
                        ui.select(
                            options=status_options,
                            value=None,
                            with_input=False,
                        )
                        .classes('pdc-status-select')
                        .style('width: 100%;')
                    )

                # Priority filter
                with ui.element('div').style('flex: 1; min-width: 200px;'):
                    ui.label('Filter by Priority').classes('pdc-form-label')
                    priority_filter = (
                        ui.select(
                            options=priority_options,
                            value=None,
                            with_input=False,
                        )
                        .classes('pdc-status-select')
                        .style('width: 100%;')
                    )

                # Clear filters button
                ui.button('Clear Filters', on_click=lambda: clear_filters()).classes(  # noqa: PLW0108
                    'pdc-btn pdc-btn-secondary'
                )

        # Dicts populated by render_checklist_table for visibility-based filtering
        # item_rows: {item_id: (row_element, item)}
        # section_header_rows: {section_name: row_element}
        item_rows: dict = {}
        section_header_rows: dict = {}

        # Render all rows once — never cleared, so timers are never interrupted
        checklist_items = helpers.get_checklist_items()
        await render_checklist_table(
            db,
            checklist_items,
            check_results,
            project_number,
            status_options=status_options,
            helpers=helpers,
            item_rows=item_rows,
            section_header_rows=section_header_rows,
        )

        # Filtering is a pure visibility toggle — no re-render needed
        def apply_filters() -> None:
            status_val = status_filter.value
            priority_val = priority_filter.value
            visible_sections: set[str] = set()
            for _, (row, item) in item_rows.items():
                visible = (not status_val or (item.status or '') == status_val) and (
                    not priority_val or (item.priority or '').lower() == priority_val.lower()
                )
                row.set_visibility(visible)
                if visible:
                    visible_sections.add(item.section)
            for section, row in section_header_rows.items():
                row.set_visibility(section in visible_sections)

        def clear_filters() -> None:
            status_filter.value = None
            priority_filter.value = None
            apply_filters()

        # Set after render — depends on item_rows/section_header_rows closures built during render
        helpers.refresh_callback = apply_filters
        status_filter.on('update:model-value', apply_filters)
        priority_filter.on('update:model-value', apply_filters)

        # Action Buttons
        with ui.element('div').classes('pdc-actions'):
            ui.button(
                'Save Curation Log (Word)', on_click=lambda: NiceGUIHelper.export_word_button(db, dir_manager)
            ).classes('pdc-btn pdc-btn-primary')

            ui.button('Calculate Time Spent', on_click=helpers.calculate_total_time).classes(
                'pdc-btn pdc-btn-calculate'
            )

            ui.button('Export YAML', on_click=lambda: NiceGUIHelper.export_yaml_button(db, dir_manager)).classes(
                'pdc-btn pdc-btn-secondary'
            )

            ui.button('New Dataset', on_click=helpers.confirm_new_dataset).classes('pdc-btn pdc-btn-danger')


async def render_checklist_table(  # noqa: PLR0913, PLR0912, PLR0915, C901, PLR0917
    db_instance: DatabaseBackend,
    checklist_items: list,
    check_results: dict[str, str],
    project_number: str,
    status_options: list,
    helpers: NiceGUIHelper | None = None,
    item_rows: dict | None = None,
    section_header_rows: dict | None = None,
    **kwargs: dict,
) -> None:
    """Render checklist table with exact styling.

    Args:
        db_instance: DatabaseBackend instance
        checklist_items: List of checklist items
        check_results: Dictionary of check results
        project_number: Project number
        helpers: NiceGUIHelper instance (shared from page to preserve timer state)
        item_rows: Dict populated with {item_id: (row_element, item)} for visibility filtering
        section_header_rows: Dict populated with {section: row_element} for visibility filtering
    """
    if helpers is None:
        helpers = NiceGUIHelper(db_instance, project_number)

    with ui.element('table').classes('pdc-checklist-table'):
        # Table Header
        with ui.element('thead'), ui.element('tr'):
            for header in [
                'ID',
                'Action Item',
                'Information Location',
                'Status',
                "Curator's Comments",
                'Priority',
                'Time Spent',
            ]:
                with ui.element('th'):
                    ui.markdown(header)

        # Table Body
        with ui.element('tbody'):
            current_section = None
            for item in checklist_items:
                # Section header row
                if item.section != current_section:
                    current_section = item.section
                    with (
                        ui.element('tr') as section_row,
                        ui.element('td').props('colspan=7').classes('pdc-section-header'),
                    ):  # noqa: E501
                        ui.label(item.section)
                    if section_header_rows is not None:
                        section_header_rows[item.section] = section_row

                # Item row
                with ui.element('tr').props(f'data-item-id="{item.id}"') as item_row:
                    # ID
                    with ui.element('td').classes('pdc-item-id'):
                        ui.label(item.id)

                    # Action & Instructions
                    with ui.element('td').classes('details-cell'):
                        with ui.element('div').classes('pdc-action-item'):
                            ui.markdown(item.action)
                        if item.instructions:
                            with ui.element('div').classes('pdc-instructions-header'):
                                ui.markdown('---')
                                ui.markdown('**Guidance**')
                            ui.markdown(item.instructions).classes('pdc-instructions')

                    # Information Location
                    with (
                        ui.element('td').classes('information-location-column'),
                        ui.element('div').classes('pdc-info-location-container'),
                    ):  # noqa: E501
                        # 1. Create check type badge if applicable
                        item_check_type = getattr(item, 'check_type', None)
                        if item_check_type:
                            create_check_type_badge(item_check_type)

                        # 2. Show tool execution and results - combined section
                        automated_check_ids = getattr(item, 'automated_check_ids', [])
                        tool_explanation = getattr(item, 'tool_explanation', None)

                        # Show for Automated checks or when check IDs exist
                        if item_check_type == 'Automated' or automated_check_ids:
                            with ui.element('div').classes('pdc-tool-execution'):
                                # Collect check info
                                checks_info = []

                                if automated_check_ids:
                                    checks_info = db_instance.read_with_in_filter(
                                        db_instance.models.check_results(),
                                        'check_id',
                                        automated_check_ids,
                                    )

                                # Display Tool Checks header with check names
                                with ui.element('div').classes('pdc-instructions-header'):
                                    ui.markdown('**Tool Checks:**')
                                if checks_info:
                                    check_names = [
                                        f'- {info["check_name"]}' for info in checks_info if info.get('check_name')
                                    ]
                                    checklist = '\n'.join(check_names)
                                    ui.markdown(checklist).classes('pdc-static-curator-check-item')
                                elif tool_explanation:
                                    ui.markdown(tool_explanation).classes('pdc-static-curator-check-item')
                                else:
                                    ui.markdown('*No automated checks configured*').classes(
                                        'pdc-static-curator-check-item'
                                    )

                            # 3. Render actual check results
                            if checks_info:
                                results_displayed = False
                                for result in checks_info:
                                    if result and result.get('results') and len(result['results']) > 0:
                                        with ui.element('div').classes('pdc-dynamic-check-results'):
                                            render_check_results(result)
                                        results_displayed = True

                                # Show "no applicable result" if checks exist but no results
                                if not results_displayed:
                                    with ui.element('div').classes('pdc-dynamic-check-results'):
                                        ui.markdown('*No applicable results*')

                        # 4. Finally, show any manually entered information location
                        curator_check_item = getattr(item, 'curator_check_item', None)
                        if curator_check_item:
                            with ui.element('div').classes('pdc-instructions-header'):
                                ui.markdown('**Curator Checks:**')
                            ui.markdown(curator_check_item).classes('pdc-static-curator-check-item')
                    # Status
                    with ui.element('td'):
                        create_status_select(
                            item.id,
                            status_options=status_options,
                            current_value=item.status or None,
                            on_change=lambda e, iid=item.id, it=item: [
                                setattr(it, 'status', e.value),
                                helpers.handle_status_change(iid, e.value),
                            ],
                        )

                    # Comments
                    with ui.element('td'):
                        ui.textarea(value=item.comments or '', placeholder="Curator's comments...").classes(
                            'pdc-comments-input'
                        ).on(
                            'change',
                            lambda e, iid=item.id: helpers.handle_comments_change(iid, e.sender.value),
                        )

                    # Priority
                    with ui.element('td'), ui.element('div').classes('pdc-priority-badge-container'):
                        create_priority_badge(item.priority)

                    # Time Spent with Timer
                    with (
                        ui.element('td'),
                        ui.row().classes('gap-1').style('align-items: center;'),
                    ):
                        time_input = (
                            ui.input(value=item.time_spent or '', placeholder='MM:SS')
                            .classes('pdc-time-input')
                            .on('change', lambda e, iid=item.id: helpers.handle_time_change(iid, e.sender.value))
                            .props('maxlength=5')
                            .style('flex: 1; min-width: 60px;')
                        )

                        # Single toggle timer button
                        # Create a closure-safe callback
                        def create_timer_callback(item_id: str, time_inp: ui.input) -> ui.button:
                            timer_btn = (
                                ui.button(icon='play_arrow')
                                .props('flat dense round size=sm color=positive')
                                .tooltip('Start/Stop Timer')
                            )
                            timer_btn.on('click', lambda: helpers.toggle_timer(item_id, time_inp, timer_btn))
                            return timer_btn

                        create_timer_callback(item.id, time_input)

                if item_rows is not None:
                    item_rows[item.id] = (item_row, item)


def render_check_results(results: dict) -> None:
    """Render check results based on their type (list, dict, or other).

    Args:
        results (dict): The results data to render (can be list, dict, or other types).

    """
    check_id = results.get('check_id', 'Unknown Check ID')
    result_name = results.get('unit', 'result')
    results = results.get('results', {})

    # Use the pdc-check-result class from nicegui_styles.py instead of inline styles
    with ui.element('div').classes('pdc-check-result'):
        # Header with check ID - using pdc-static-curator-check-item class
        ui.label(f'{check_id}').classes('pdc-check-result-header')

        if isinstance(results, list):
            # Show count description
            ui.label(f'{len(results)} {result_name} found').classes('pdc-check-description')

            # Use pdc-check-details-list class for the numbered list
            with ui.element('ol').classes('pdc-check-details-list'):
                for item in results:
                    with ui.element('li').classes('result-item'):
                        if isinstance(item, dict):
                            # If list contains dicts, render key-value pairs
                            for k, v in item.items():
                                with ui.element('div'):
                                    ui.markdown(f'**{k}:** ')
                                    ui.label(str(v)).style('display: inline;')
                        else:
                            ui.label(str(item))

        elif isinstance(results, dict):
            # Show count description
            ui.label(f'{len(results)} {result_name} found').classes('pdc-check-description')

            # Use pdc-check-details-list class for the numbered list
            with ui.element('ol').classes('pdc-check-details-list'):
                for key, value in results.items():
                    with ui.element('li').classes('result-item'):
                        ui.markdown(f'**{key}:** {value}')

        else:
            # Render as plain text for other types
            ui.label(str(results)).classes('pdc-check-description')
