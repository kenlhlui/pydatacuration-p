"""The project table page shared by the delete and resume project pages."""

# ruff: noqa: PLR1702
from urllib.parse import quote
from urllib.parse import urlparse

from nicegui import ui
from nicegui.elements.input import Input

from pydatacuration.frontend.pages.utils import confirm_delete_project
from pydatacuration.frontend.reusable_elements import action_button
from pydatacuration.frontend.reusable_elements import dropdown_menu
from pydatacuration.frontend.reusable_elements import form_section


async def render_project_table(
    schemas: list[dict],
    mode: str = 'resume',  # 'resume' or 'delete'
    refresh_callback=None,
) -> None:
    """Render a filterable project table.

    Args:
        schemas: List of project schemas
        mode: 'resume' for clickable rows, 'delete' for delete buttons
        refresh_callback: Optional callback to refresh the list after deletion
    """
    if not schemas:
        with ui.element('div').classes('no-projects'):
            ui.label('No projects found').classes('text-xl')
        return

    # Filters
    with form_section('Filters'), ui.row().classes('gap-4').style('align-items: flex-end;'):
        # Search filter
        with ui.element('div').classes('pdc-form-group').style('flex: 1; margin-bottom: 0;'):
            ui.label('Search').classes('pdc-form-label')
            search_input: Input = (
                ui.input(placeholder='Search Project Number, Title, PID, ID (Versioned), URL')
                .classes('pdc-input')
                .style('width: 100%;')
            )

        # Curator filter
        with ui.element('div').classes('pdc-form-group').style('flex: 1; margin-bottom: 0;'):
            curators = [''] + sorted({s['curator_name'] for s in schemas if s.get('curator_name')})
            curator_filter = dropdown_menu('Select Curator', curators)

        # Clear filters button
        action_button('Clear Filters', lambda: clear_filters(search_input, curator_filter))

    # Table container
    table_container = ui.column().style('width: 100%;')

    # Define render function that applies filters
    def render_filtered_table() -> None:
        # Apply filters
        filtered_schemas = schemas
        if search_input.value:
            search_term = search_input.value.lower()
            filtered_schemas = [
                s
                for s in filtered_schemas
                if search_term in str(s.get('project_number', '')).lower()
                or search_term in str(s.get('dataset_title', '')).lower()
                or search_term in str(s.get('dataset_pid', '')).lower()
                or search_term in str(s.get('dataset_id', '')).lower()
            ]
        if curator_filter.value:
            filtered_schemas = [s for s in filtered_schemas if s.get('curator_name') == curator_filter.value]

        table_container.clear()
        with table_container:
            ui.label(f'Found {len(filtered_schemas)} project(s)').classes('pdc-form-section-title').style(
                'margin: 20px 0;'
            )

            # Render table
            with ui.element('table').classes('pdc-checklist-table'):
                # Table Header
                with ui.element('thead'), ui.element('tr'):
                    headers = ['Project Number', 'Dataset Information', 'Curator', 'Project Last Modified']
                    if mode == 'delete':
                        headers.append('Action')
                    for header in headers:
                        with ui.element('th'):
                            ui.markdown(header)

                # Table Body
                with ui.element('tbody'):
                    for schema in filtered_schemas:
                        row_classes = 'clickable-row' if mode == 'resume' else ''
                        with ui.element('tr').classes(row_classes):
                            # Project Number
                            with ui.element('td'):
                                if mode == 'resume':
                                    href = ui.element('a').props(
                                        f'href="/checklist?project_number={quote(schema["project_number"])}"'
                                    )
                                if mode == 'delete':
                                    href = ui.element('a').props(
                                        f'href="/checklist?project_number={quote(schema["project_number"])}&view_only=true"'
                                    )
                                with href.style('color: #3498db; text-decoration: none; font-weight: 600;'):
                                    ui.label(f'📋 {schema["project_number"]}')

                            # Dataset Metadata
                            with ui.element('td'):
                                with ui.element('div'):
                                    ui.markdown(
                                        f'**Title:** {schema.get("dataset_title", "N/A")}',
                                    )
                                with ui.element('div'):
                                    ui.markdown(f'**PID:** {schema.get("dataset_pid", "N/A")} ').style(
                                        'display: inline;'
                                    )

                                with ui.element('div'):
                                    ui.markdown(
                                        f'**ID (Versioned):** {schema.get("dataset_id", "N/A")}',
                                    ).style('display: inline;')
                                with ui.element('div'):
                                    dataset_url = schema.get('dataset_url', 'N/A')
                                    parsed = urlparse(dataset_url)
                                    if parsed.scheme in {'http', 'https'}:
                                        # Use proper HTML escaping or NiceGUI's built-in link component
                                        ui.html('URL: ', sanitize=False).style('display: inline; font-weight: bold;')
                                        ui.link(dataset_url, dataset_url, new_tab=True).style('display: inline;')
                            # Curator
                            with ui.element('td'):
                                ui.label(schema.get('curator_name', 'N/A'))

                            # Last Modified
                            with ui.element('td'):
                                ui.label(schema['last_modified'])

                            # Action column (only for delete mode)
                            if mode == 'delete':
                                with ui.element('td').style('text-align: center; vertical-align: middle;'):
                                    ui.button(
                                        '🗑️ Delete',
                                        color='red',
                                        on_click=lambda s=schema: confirm_delete_project(s, refresh_callback),
                                    ).props('unelevated no-caps').classes('pdc-btn')

    # Define clear filters function
    def clear_filters(search_inp: ui.input, curator_sel: ui.select) -> None:
        search_inp.value = ''
        curator_sel.value = None
        render_filtered_table()

    # Connect filters to table refresh - bind directly to the function
    search_input.on_value_change(lambda e: render_filtered_table())
    curator_filter.on_value_change(lambda e: render_filtered_table())

    # Initial render
    render_filtered_table()
