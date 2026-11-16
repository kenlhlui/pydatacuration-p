"""Look up user-facing text in the message catalogue (pydatacuration/locales/en.yaml)."""

from functools import cache
from pathlib import Path

import yaml


LOCALES_DIR = Path(__file__).parent / 'locales'


@cache
def load_catalogue(locale: str = 'en') -> dict:
    """Return the message catalogue for a locale, read once."""
    with (LOCALES_DIR / f'{locale}.yaml').open(encoding='utf-8') as f:
        return yaml.safe_load(f)


def _lookup(key: str) -> str | dict | None:
    node = load_catalogue()
    for part in key.split('.'):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def has_message(key: str) -> bool:
    """Return whether the catalogue has a message for key."""
    node = _lookup(key)
    return isinstance(node, str) or (isinstance(node, dict) and set(node) == {'one', 'other'})


def t(key: str, /, count: int | None = None, **params: object) -> str:
    """Return the catalogue message for key, with its {placeholders} filled in from params.

    Args:
        key (str): Dotted key of the message, e.g. 'setup.form_reset'.
        count (int | None): For messages with 'one' and 'other' forms: picks the form, and fills in {count}.
        **params: Values for the message's other placeholders.

    Returns:
        str: The message text.

    Raises:
        KeyError: If the catalogue has no message for key.
    """
    if not has_message(key):
        raise KeyError(key)
    message = _lookup(key)
    if count is not None:
        message = message['one' if count == 1 else 'other']
        params['count'] = count
    return message.format(**params)
