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

# Import the reusable elements
from pydatacuration.frontend.reusable_elements import action_button
from pydatacuration.frontend.reusable_elements import dropdown_menu
from pydatacuration.frontend.reusable_elements import form_section

# Import reusable components
from pydatacuration.frontend.reusable_elements import scroll_to_top_button

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
async def checklist_page(project_number: str, view_only: bool = False) -> None:
    """Checklist page with exact styling match.

    Args:
        project_number (str): The project number to load data for.
        view_only (bool): If True, disables all interactive elements for read-only viewing.
    """
    apply_pdc_styles()

    # Initialize the db connection for this project number
    dir_manager = DirectoryManager(project_number, MAIN_DIR, RES_DIR)
    db = get_database(schema_name=project_number, db_file=dir_manager.db_path)
    helpers = NiceGUIHelper(db, project_number)

    # Load metadata from database
    project_metadata = db.read_project_metadata_record()

    # Load checklist results and checklist metadata from database
    check_results = db.read_check_results()
    checklist_metadata = db.read_checklist_metadata() or {}

    # Load the options for status and priority from the resource directory (with fallback to defaults)
    _status_opts = load_status_options(RES_DIR)
    status_options = list(_status_opts.model_dump(mode='python').values())
    status_color_map = _status_opts.color_map()
    priority_options = load_priority_options(RES_DIR).model_dump(mode='python')

    # Load the scroll to top button (using reusable component)
    scroll_to_top_button()

    with ui.column().classes('pdc-container'):
        # Logo
        ui.html(
            '<img src="/static/UTL.png" alt="University of Toronto Libraries Logo" class="utl-logo">',
            sanitize=False,
        )
        # Header using the checklist metadata name field (with fallback to "Unknown Checklist" if not available)
        ui.label(f'{checklist_metadata.get("name", "Unknown Checklist")}').classes('pdc-header')

        # Metadata Display using our helper function
        with ui.tabs() as tabs:
            project_metadata_tab = ui.tab('Project Metadata')
            checklist_metadata_tab = ui.tab('Checklist Metadata')
        with ui.tab_panels(tabs, value=project_metadata_tab).classes('w-full'):
            with ui.tab_panel(project_metadata_tab).classes('w-full'):
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
            with ui.tab_panel(checklist_metadata_tab).classes('w-full'):
                if checklist_metadata:
                    created_by = checklist_metadata.get('created_by') or []
                    display_metadata = {
                        **checklist_metadata,
                        'created_by': ', '.join(created_by) if created_by else 'N/A',
                        'last_updated': str(checklist_metadata.get('last_updated', 'N/A')),
                    }
                    create_info_grid(
                        display_metadata,
                        [
                            ('name', 'Checklist name'),
                            ('version', 'Version'),
                            ('created_by', 'Created by'),
                            ('last_updated', 'Last updated'),
                            ('status', 'Status'),
                        ],
                    )
                else:
                    ui.label('No checklist metadata available.').classes('pdc-additional-info')

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

        # View-only toggle state and element refs (populated by render_checklist_table)
        is_view_only = {'value': view_only}
        interactive_elements: list = []
        timer_buttons: list = []

        def toggle_view_only() -> None:
            is_view_only['value'] = not is_view_only['value']
            active = is_view_only['value']
            toggle_btn.set_text('Edit Mode' if active else 'View Only')
            for el in interactive_elements:
                if active:
                    el.props('readonly')
                else:
                    el.props(remove='readonly')
            for btn in timer_buttons:
                btn.set_visibility(not active)
            action_button_div.set_visibility(not active)

        # Status and time dashboard with view-only toggle
        @ui.refreshable
        def status_progress_ui() -> None:
            with ui.row().classes('gap-4 items-end'):
                helpers.render_status_progress(color_map=status_color_map)
                with ui.column().classes('items-center gap-1'):
                    ui.label(helpers.get_total_time_str()).classes('text-lg font-bold')
                    ui.label('Total Time (HH:MM)').classes('text-sm text-center')

        _btn_ref: list = []

        def _render_toggle_btn() -> None:
            _btn_ref.append(
                ui.button(
                    'Edit Mode' if view_only else 'View Only',
                    on_click=toggle_view_only,
                ).classes('pdc-btn')
            )

        with form_section('Status and Time', header_slot=_render_toggle_btn):
            status_progress_ui()

        toggle_btn = _btn_ref[0]

        # Filters Section
        with form_section('Filters'), ui.row().classes('gap-4').style('align-items: flex-end;'):
            status_filter = dropdown_menu('Filter by Status', status_options)
            priority_filter = dropdown_menu('Filter by Priority', priority_options)
            # Clear filters button
            action_button('Clear Filters', lambda: clear_filters())  # noqa: PLW0108

        # Dicts populated by render_checklist_table for visibility-based filtering
        # item_rows: {item_id: (row_element, item)}
        # section_header_rows: {section_name: row_element}
        item_rows: dict = {}
        section_header_rows: dict = {}

        # Render all rows once — never cleared, so timers are never interrupted
        checklist_items = helpers.get_checklist_items()

        def _numeric_id_key(item) -> tuple[int, ...]:  # type: ignore[no-untyped-def]
            try:
                return tuple(int(part) for part in str(item.id).split('.'))  # type: ignore[union-attr]
            except ValueError:
                return (0,)

        checklist_items = sorted(checklist_items, key=_numeric_id_key)
        await render_checklist_table(
            db,
            checklist_items,
            check_results,
            project_number,
            status_options=status_options,
            status_color_map=status_color_map,
            helpers=helpers,
            item_rows=item_rows,
            section_header_rows=section_header_rows,
            view_only=view_only,
            interactive_elements=interactive_elements,
            timer_buttons=timer_buttons,
        )

        # Filtering is a pure visibility toggle — no re-render needed
        def apply_filters() -> None:
            status_val = status_filter.value
            priority_val = priority_filter.value
            visible_sections: set[str] = set()
            for _, (row, item) in item_rows.items():
                visible = (not status_val or (item.status or '') == status_val) and (
                    not priority_val or item.priority == priority_val
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
        def on_status_change() -> None:
            apply_filters()
            status_progress_ui.refresh()

        helpers.refresh_callback = on_status_change
        status_filter.on('update:model-value', apply_filters)
        priority_filter.on('update:model-value', apply_filters)

        # Action Buttons — always rendered so toggle_view_only can show/hide
        with ui.element('div').classes('pdc-actions') as action_button_div:
            action_button('Save Curation Log (Word)', lambda: NiceGUIHelper.export_word_button(db, dir_manager))
            action_button('Calculate Time Spent', lambda: helpers.calculate_total_time)
            action_button('Export YAML', lambda: NiceGUIHelper.export_yaml_button(db, dir_manager))
            action_button('New Dataset', helpers.confirm_new_dataset)
        action_button_div.set_visibility(not view_only)


async def render_checklist_table(  # noqa: PLR0913, PLR0912, PLR0915, C901, PLR0917
    db_instance: DatabaseBackend,
    checklist_items: list,
    check_results: dict[str, str],
    project_number: str,
    status_options: list,
    status_color_map: dict[str, tuple[str, str]] | None = None,
    helpers: NiceGUIHelper | None = None,
    item_rows: dict | None = None,
    section_header_rows: dict | None = None,
    view_only: bool = False,
    interactive_elements: list | None = None,
    timer_buttons: list | None = None,
) -> None:
    """Render checklist table with exact styling.

    Args:
        db_instance: DatabaseBackend instance
        checklist_items: List of checklist items
        check_results: Dictionary of check results
        project_number: Project number
        status_options: List of available status option labels
        status_color_map: Optional mapping of status label → (bg_color, text_color)
        helpers: NiceGUIHelper instance (shared from page to preserve timer state)
        item_rows: Dict populated with {item_id: (row_element, item)} for visibility filtering
        section_header_rows: Dict populated with {section: row_element} for visibility filtering
        interactive_elements: List populated with references to interactive elements for view-only toggling
        timer_buttons: List populated with references to timer buttons for view-only toggling
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
                'Priority',
                "Curator's Comments",
                'Status',
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
                                ui.markdown('--')
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

                    # Priority
                    with ui.element('td'), ui.element('div').classes('pdc-badge-container'):
                        create_priority_badge(item.priority)

                    # Comments
                    with ui.element('td'):
                        comments_input = ui.textarea(
                            value=item.comments or '', placeholder="Curator's comments..."
                        ).classes('pdc-comments-input')
                        if view_only:
                            comments_input.props('readonly')
                        comments_input.on(
                            'change',
                            lambda e, iid=item.id: helpers.handle_comments_change(iid, e.sender.value),
                        )

                    # Status
                    with ui.element('td'):
                        status_el = create_status_select(
                            item.id,
                            status_options=status_options,
                            current_value=item.status or None,
                            on_change=lambda e, iid=item.id, it=item: [
                                setattr(it, 'status', e.value),
                                helpers.handle_status_change(iid, e.value),
                            ],
                            color_map=status_color_map,
                        )
                        if view_only:
                            status_el.props('readonly')

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
                        if view_only:
                            time_input.props('readonly')

                        # Single toggle timer button — always rendered, visibility toggled
                        def create_timer_callback(item_id: str, time_inp: ui.input) -> ui.button:
                            timer_btn = (
                                ui.button(icon='play_arrow')
                                .props('flat dense round size=sm color=positive')
                                .tooltip('Start/Stop Timer')
                            )
                            timer_btn.on('click', lambda: helpers.toggle_timer(item_id, time_inp, timer_btn))
                            return timer_btn

                        t_btn = create_timer_callback(item.id, time_input)
                        t_btn.set_visibility(not view_only)
                        if timer_buttons is not None:
                            timer_buttons.append(t_btn)

                    if interactive_elements is not None:
                        interactive_elements.extend([status_el, comments_input, time_input])

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
