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


def form_group(label: str, input_component: ui.element, helper: str | None = None) -> None:
    """Create a form group with a label, input component, and optional helper text."""
    with ui.element('div').classes('pdc-form-group'):
        ui.label(label).classes('pdc-form-label')
        input_component  # noqa: B018
        if helper:
            ui.label(helper).classes('pdc-form-helper')
