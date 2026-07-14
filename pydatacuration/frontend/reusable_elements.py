"""Reuseable form components for frontend."""

import contextlib
from collections.abc import Callable
from collections.abc import Generator
from typing import Literal

from nicegui import ui
from nicegui.elements.page_sticky import PageStickyPositions


@contextlib.contextmanager
def form_section(title: str, header_slot: Callable | None = None) -> Generator[None, None, None]:
    """Create a form section with a title.

    Args:
        title: The title of the form section.
        header_slot: Optional callable rendered in the title row at the top-right.

    Yields:
        A NiceGUI element representing the form section.

    """
    with ui.element('div').classes('pdc-form-section'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label(title).classes('pdc-form-section-title')
            if header_slot:
                header_slot()
        yield


def text_input_box(  # noqa: PLR0913
    label: str,
    form_data: dict,
    key: str,
    *,
    helper_text: str | None = None,
    props: str = '',
    **input_kwargs,
) -> ui.input:
    """Build a labeled text input.

    Args:
        label (str): The field label.
        form_data (dict): The bound form data dictionary.
        key (str): The key in the form data dictionary.
        helper_text (str | None): Optional helper text shown below the field.
        props (str): Extra NiceGUI props string.
        input_kwargs: Additional keyword arguments passed to ui.input().

    Returns:
        ui.input: The created input component.

    """
    with ui.element('div').classes('pdc-form-group'):
        ui.label(label).classes('pdc-form-label')

        input_component = (
            ui.input(**input_kwargs).bind_value(form_data, key).classes('pdc-input').style('width: 100%; flex: 1;')
        )

        if props:
            input_component.props(props)

        if helper_text:
            ui.label(helper_text).classes('pdc-form-helper')

    return input_component


def scroll_to_top_button(text: str = '↑') -> None:
    """Create a button that scrolls the page to the top when clicked.

        Default text is an upwards arrow (↑). Can be customized by passing a different string to the `text` parameter.

    Args:
        text (str): The text to display on the button.

    """
    with ui.page_scroller(position='bottom-right', x_offset=20, y_offset=20):
        ui.button(text).classes('pdc-btn pdc-btn--lg')


def action_button(label: str, on_click) -> ui.button:
    """Create a standardized action button.

    Args:
        label (str): The text to display on the button.
        on_click: The callback function to execute when the button is clicked.

    Returns:
        ui.button: The created button component.

    """
    return ui.button(label, on_click=on_click).classes('pdc-btn')


def dropdown_menu(label: str, options: list) -> ui.select:
    """Create a standardized filter dropdown.

    Args:
        label (str): The text to display on the dropdown label.
        options (list): The list of options for the dropdown.

    Returns:
        ui.select: The created dropdown component.

    """
    with ui.element('div').style('flex: 1'):
        ui.label(label).classes('pdc-form-label')
        value = ui.select(options, value=None, with_input=False).classes('pdc-input').style('width: 100%;')
        return value


def floating_menu(  # noqa: PLR0913, PLR0917
    actions: dict[str, Callable[[], None]],
    menu_label: str = '',
    position: PageStickyPositions = 'bottom',
    x_offset: int = 0,
    y_offset: int = 0,
    direction: Literal['up', 'down', 'left', 'right'] = 'up',
    show_on_scroll: bool = True,
    hide_delay_ms: int = 2500,
) -> None:
    """Create a floating menu with a button that opens a dropdown menu.

    Args:
        actions: Mapping of menu label to click callback.
        menu_label: The label for the floating menu button.
        position: The position of the floating menu.
        x_offset: The horizontal offset of the floating menu.
        y_offset: The vertical offset of the floating menu.
        direction: The direction of the floating menu.
        show_on_scroll: Whether to show the menu only when scrolling.
        hide_delay_ms: How long to wait after scrolling stops before hiding again (in milliseconds).
    """
    sticky = ui.page_sticky(position=position, x_offset=x_offset, y_offset=y_offset)
    if show_on_scroll:
        sticky.classes('pdc-show-on-scroll')

    with sticky, ui.fab(icon='menu', direction=direction, label=menu_label) as fab:
        for label, action in actions.items():
            ui.fab_action(icon='', label=label, on_click=action)

    if not show_on_scroll:
        return

    state = {'scrolling': False}

    def sync_visibility() -> None:
        if state['scrolling'] or fab.value:  # keep visible while the menu is open
            sticky.classes(add='pdc-scrolling')
        else:
            sticky.classes(remove='pdc-scrolling')

    # Opening/closing the menu counts as activity, so closing restarts the hide delay
    # instead of hiding instantly.
    fab.on_value_change(lambda: ui.run_javascript('window.pdcActivity?.()'))

    def on_scroll_event(e) -> None:
        state['scrolling'] = bool(e.args.get('scrolling', False))
        sync_visibility()

    ui.on('pdc-scroll', on_scroll_event)

    ui.add_head_html(f"""
        <script>
        (() => {{
            let hideTimer = null;

            const emitScrolling = (scrolling) => {{
                emitEvent('pdc-scroll', {{ scrolling }});
            }};

            const onActivity = () => {{
                emitScrolling(true);
                clearTimeout(hideTimer);
                hideTimer = setTimeout(() => emitScrolling(false), {hide_delay_ms});
            }};

            window.pdcActivity = onActivity;

            document.addEventListener('scroll', onActivity, {{ capture: true, passive: true }});
            window.addEventListener('wheel', onActivity, {{ passive: true }});
            window.addEventListener('touchmove', onActivity, {{ passive: true }});
        }})();
        </script>
    """)
