"""Look up user-facing text in the message catalogue (pydatacuration/locales/<locale>.yaml)."""

import string
from functools import cache
from pathlib import Path

import yaml
from loguru import logger


LOCALES_DIR = Path(__file__).parent / 'locales'

# The language messages are shown in; set at startup from the LOCALE setting
_locale = 'en'


def available_locales() -> list[str]:
    """Return the locales that have a catalogue file, e.g. ['en', 'fr']."""
    return sorted(path.stem for path in LOCALES_DIR.glob('*.yaml'))


def set_locale(locale: str) -> None:
    """Show messages from this locale's catalogue from now on. app.py calls it at startup.

    Logs one warning listing the messages that are shown in English instead: those the catalogue doesn't have,
    and those that can't be filled in like the English ones.

    Args:
        locale (str): A locale from available_locales(); AppSettings checks the LOCALE setting is one.
    """
    global _locale  # noqa: PLW0603
    _locale = locale
    problems = {
        'Missing': missing_translations(locale),
        'Placeholders or one/other forms differ from English': mismatched_translations(locale),
    }
    if any(problems.values()):
        count = sum(len(keys) for keys in problems.values())
        details = '. '.join(f'{label} ({len(keys)}): {", ".join(keys)}' for label, keys in problems.items() if keys)
        logger.warning(f'{locale}.yaml: {count} messages are shown in English. {details}')


@cache
def load_catalogue(locale: str = 'en') -> dict:
    """Return the message catalogue for a locale, read once."""
    with (LOCALES_DIR / f'{locale}.yaml').open(encoding='utf-8') as f:
        return yaml.safe_load(f)


def _find(locale: str, key: str) -> str | dict | None:
    """Return the message for key in a locale's catalogue: text, or one/other forms. None if there isn't one."""
    node = load_catalogue(locale)
    for part in key.split('.'):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    is_message = isinstance(node, str) or (isinstance(node, dict) and set(node) == {'one', 'other'})
    return node if is_message else None


def _message_keys(node: dict, prefix: str = '') -> list[str]:
    """Return the dotted keys of the messages in a catalogue, or in a section of one."""
    keys = []
    for name, value in node.items():
        key = f'{prefix}{name}'
        if isinstance(value, dict) and set(value) != {'one', 'other'}:
            keys.extend(_message_keys(value, f'{key}.'))
        else:
            keys.append(key)
    return keys


def _placeholders(message: str | dict) -> set[str] | None:
    """Return the placeholder names in a message, across its one/other forms. None if it can't be read, e.g. '{name'."""
    forms = list(message.values()) if isinstance(message, dict) else [message]
    if not all(isinstance(form, str) for form in forms):
        return None
    try:
        return {name for form in forms for _, name, _, _ in string.Formatter().parse(form) if name is not None}
    except ValueError:
        return None


def _fills_in_like(translated: str | dict, english: str | dict) -> bool:
    """Return whether a translated message can be filled in like the English one: same placeholders and forms."""
    placeholders = _placeholders(translated)
    return (
        isinstance(translated, dict) == isinstance(english, dict)
        and placeholders is not None
        and placeholders == _placeholders(english)
    )


def missing_translations(locale: str) -> list[str]:
    """Return the keys of the messages in en.yaml that a locale's catalogue doesn't have, sorted."""
    return sorted(key for key in _message_keys(load_catalogue('en')) if _find(locale, key) is None)


def mismatched_translations(locale: str) -> list[str]:
    """Return the keys of a locale's messages that can't be filled in like the English ones, sorted.

    For example, a translation using {item} where the English message, and so the code, uses {item_id}.
    """
    keys = []
    for key in _message_keys(load_catalogue('en')):
        translated = _find(locale, key)
        if translated is not None and not _fills_in_like(translated, _find('en', key)):
            keys.append(key)
    return sorted(keys)


def _lookup(key: str) -> str | dict | None:
    """Return the message for key in the active locale.

    Falls back to English if the translation doesn't have the message, or can't be filled in like the English one.
    """
    message = _find(_locale, key)
    if _locale == 'en':
        return message
    english = _find('en', key)
    if message is None or (english is not None and not _fills_in_like(message, english)):
        return english
    return message


def has_message(key: str) -> bool:
    """Return whether there is a message for key, in the active locale or in English."""
    return _lookup(key) is not None


def t(key: str, /, count: int | None = None, **params: object) -> str:
    """Return the catalogue message for key, with its {placeholders} filled in from params.

    Args:
        key (str): Dotted key of the message, e.g. 'setup.form_reset'.
        count (int | None): For messages with 'one' and 'other' forms: picks the form, and fills in {count}.
        **params: Values for the message's other placeholders.

    Returns:
        str: The message text, in English if the active locale's catalogue doesn't have it.

    Raises:
        KeyError: If neither the active locale's catalogue nor the English one has a message for key.
    """
    message = _lookup(key)
    if message is None:
        raise KeyError(key)
    if count is not None:
        message = message['one' if count == 1 else 'other']
        params['count'] = count
    return message.format(**params)
