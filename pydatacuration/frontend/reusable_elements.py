"""Reuseable form components for frontend."""

import contextlib
from collections.abc import Generator

from nicegui import ui


@contextlib.contextmanager
def form_section(title: str) -> Generator[None, None, None]:
    """Create a form section with a title.

    Args:
        title: The title of the form section.

    Yields:
        A NiceGUI element representing the form section.

    """
    with ui.element('div').classes('pdc-form-section'):
        ui.label(title).classes('pdc-form-section-title')
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


def action_buttons(label: str, on_click) -> ui.button:
    """Create a standardized action button.

    Args:
        label (str): The text to display on the button.
        on_click: The callback function to execute when the button is clicked.

    Returns:
        ui.button: The created button component.

    """
    return ui.button(label, on_click=on_click).classes('pdc-btn')
