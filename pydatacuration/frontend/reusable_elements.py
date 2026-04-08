"""Reuseable form components for frontend."""

import contextlib
from collections.abc import Generator

from nicegui import ui


@contextlib.contextmanager
def form_section(title: str) -> Generator[None, None, None]:
    """Create a form section with a title.

    Args:
        title: The title of the form section of the form section.

    Returns:
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
            ui.input(**input_kwargs).classes('pdc-form-input').bind_value(form_data, key).style('width: 100%')
        )

        if props:
            input_component.props(props)

        if helper_text:
            ui.label(helper_text).classes('pdc-form-helper')

    return input_component
