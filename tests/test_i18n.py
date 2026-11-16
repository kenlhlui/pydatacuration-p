"""Tests for the message catalogue (pydatacuration/locales/en.yaml) and the code that uses it."""

import ast
import re
import string
import warnings
from pathlib import Path

import pytest
import yaml
from loguru import logger
from pydantic import ValidationError

from pydatacuration import i18n
from pydatacuration.backend.models.app_settings import AppSettings
from pydatacuration.i18n import LOCALES_DIR
from pydatacuration.i18n import available_locales
from pydatacuration.i18n import has_message
from pydatacuration.i18n import load_catalogue
from pydatacuration.i18n import mismatched_translations
from pydatacuration.i18n import missing_translations
from pydatacuration.i18n import set_locale
from pydatacuration.i18n import t


PACKAGE_DIR = Path(__file__).parent.parent / 'pydatacuration'
CHECKER_DIR = PACKAGE_DIR / 'checker'

# Calls that put text on screen (or in an API response), and the keyword arguments that carry that text.
# Positional string arguments of these calls are checked too.
UI_TEXT_CALLS = {
    'notify': set(),
    'label': set(),
    'markdown': set(),
    'button': {'text'},
    'tab': {'label'},
    'tooltip': {'text'},
    'checkbox': {'text'},
    'input': {'label', 'placeholder'},
    'textarea': {'label', 'placeholder'},
    'action_button': {'label'},
    'form_section': {'title'},
    'dropdown_menu': {'label'},
    'floating_menu': {'menu_label'},
    'text_input_box': {'label', 'placeholder', 'helper_text'},
    'HTTPException': {'detail'},
}
UI_TEXT_FILES = [*sorted((PACKAGE_DIR / 'frontend').rglob('*.py')), PACKAGE_DIR / 'backend' / 'api.py']
TRANSLATIONS = sorted(path.stem for path in LOCALES_DIR.glob('*.yaml') if path.stem != 'en')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _package_trees() -> list[tuple[Path, ast.Module]]:
    return [(path, ast.parse(path.read_text(encoding='utf-8'))) for path in sorted(PACKAGE_DIR.rglob('*.py'))]


def _literal_t_calls() -> list[tuple[str, ast.Call]]:
    """Return (location, call) for every t('literal.key', ...) call in the package."""
    calls = []
    for path, tree in _package_trees():
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == 't'
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                calls.append((f'{path.relative_to(PACKAGE_DIR.parent)}:{node.lineno}', node))
    return calls


def _exception_message_keys() -> set[str]:
    """Return the catalogue keys set as message_key on exception classes."""
    keys = set()
    for _, tree in _package_trees():
        for node in ast.walk(tree):
            target = node.target if isinstance(node, ast.AnnAssign) else None
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == 'message_key' and isinstance(node.value, ast.Constant):
                keys.add(node.value.value)
    return keys


def _leaves(node: dict, prefix: str = '') -> dict[str, str | dict]:
    """Flatten the catalogue to {dotted.key: message}, keeping one/other plural forms as one message."""
    leaves = {}
    for key, value in node.items():
        dotted = f'{prefix}{key}'
        if isinstance(value, dict) and set(value) != {'one', 'other'}:
            leaves.update(_leaves(value, f'{dotted}.'))
        else:
            leaves[dotted] = value
    return leaves


def _placeholders(message: str | dict) -> set[str]:
    forms = message.values() if isinstance(message, dict) else [message]
    return {name for form in forms for _, name, _, _ in string.Formatter().parse(form) if name}


def _has_words(node: ast.expr) -> bool:
    """True if node is a string literal or f-string whose fixed text contains letters."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return bool(re.search(r'[A-Za-z]', node.value))
    if isinstance(node, ast.JoinedStr):
        return any(_has_words(part) for part in node.values)
    return False


def _checker_check_ids() -> set[str]:
    ids = set()
    for path in CHECKER_DIR.rglob('*.py'):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node, ast.keyword) and node.arg == 'check_id' and isinstance(node.value, ast.Constant):
                ids.add(node.value.value)
    return ids


# ---------------------------------------------------------------------------
# t() and has_message()
# ---------------------------------------------------------------------------


def test_t_should_return_message_for_key():
    assert t('common.cancel') == 'Cancel'


def test_t_should_fill_in_placeholders():
    assert t('checklist.status_updated', item_id='1.1') == 'Status updated for 1.1'


def test_t_should_pick_one_form_when_count_is_one():
    assert t('projects.found', count=1) == 'Found 1 project'


def test_t_should_pick_other_form_when_count_is_not_one():
    assert t('projects.found', count=3) == 'Found 3 projects'


def test_t_should_pick_other_form_when_count_is_zero():
    assert t('projects.found', count=0) == 'Found 0 projects'


def test_t_should_raise_key_error_for_unknown_key():
    with pytest.raises(KeyError):
        t('no.such.key')


def test_t_should_raise_key_error_for_section_key():
    with pytest.raises(KeyError):
        t('common')


def test_has_message_should_be_true_for_known_key():
    assert has_message('common.cancel')


def test_has_message_should_be_false_for_unknown_key():
    assert not has_message('checks.data_sources_entires.name')


# ---------------------------------------------------------------------------
# The catalogue itself
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(('key', 'message'), _leaves(load_catalogue()).items())
def test_catalogue_message_should_be_text_or_plural_forms(key, message):
    if isinstance(message, dict):
        assert all(isinstance(form, str) for form in message.values()), key
    else:
        assert isinstance(message, str), key


@pytest.mark.parametrize(('key', 'message'), _leaves(load_catalogue()).items())
def test_catalogue_message_should_have_valid_placeholders(key, message):
    _placeholders(message)  # raises ValueError on a broken placeholder such as '{name'


@pytest.mark.parametrize(('location', 'call'), _literal_t_calls())
def test_literal_key_should_exist_in_catalogue(location, call):
    assert has_message(call.args[0].value), f'{location}: {call.args[0].value!r} is not in en.yaml'


@pytest.mark.parametrize(('location', 'call'), _literal_t_calls())
def test_literal_call_should_pass_exactly_the_placeholders_of_its_message(location, call):
    message = _leaves(load_catalogue())[call.args[0].value]
    passed = {kw.arg for kw in call.keywords if kw.arg}
    assert passed == _placeholders(message), f'{location}: {call.args[0].value!r}'


@pytest.mark.parametrize('key', sorted(_exception_message_keys()))
def test_exception_message_key_should_exist_in_catalogue(key):
    assert has_message(key)


def test_api_token_prefilled_placeholder_should_not_take_any_part_of_the_token():
    assert _placeholders(load_catalogue()['setup']['api_token_placeholder_prefilled']) == set()


def test_every_catalogue_message_should_be_used():
    used = {call.args[0].value for _, call in _literal_t_calls()} | _exception_message_keys()
    # checks.* is looked up by check ID (see the check ID tests below)
    unused = {key for key in _leaves(load_catalogue()) if key not in used and not key.startswith('checks.')}
    assert not unused, f'Messages in en.yaml that no code uses: {sorted(unused)}'


# ---------------------------------------------------------------------------
# Check result text, looked up by check ID
# ---------------------------------------------------------------------------


def test_every_check_id_written_by_checkers_should_be_in_catalogue():
    assert _checker_check_ids() <= set(load_catalogue()['checks'])


def test_every_check_in_catalogue_should_be_written_by_a_checker():
    assert set(load_catalogue()['checks']) <= _checker_check_ids()


@pytest.mark.parametrize('check_id', sorted(load_catalogue()['checks']))
def test_check_should_have_name_description_unit_and_found(check_id):
    assert {'name', 'description', 'unit', 'found'} <= set(load_catalogue()['checks'][check_id])


@pytest.mark.parametrize('check_id', sorted(load_catalogue()['checks']))
def test_check_found_message_should_use_only_count(check_id):
    assert _placeholders(load_catalogue()['checks'][check_id]['found']) == {'count'}


# ---------------------------------------------------------------------------
# Language setting
# ---------------------------------------------------------------------------


ENGLISH = {
    'common': {
        'cancel': 'Cancel',
        'back': 'Back',
        'updated': 'Updated {item_id}',
        'found': {'one': '{count} file found', 'other': '{count} files found'},
    }
}
FRENCH = {
    'common': {
        'cancel': 'Annuler',
        'updated': '{item_id} mis à jour',
        'found': {'one': '{count} fichier trouvé', 'other': '{count} fichiers trouvés'},
    }
}


def _write_catalogue(folder: Path, locale: str, catalogue: dict) -> None:
    (folder / f'{locale}.yaml').write_text(yaml.safe_dump(catalogue, allow_unicode=True), encoding='utf-8')


def _french_with(**messages: object) -> dict:
    return {'common': {**FRENCH['common'], **messages}}


@pytest.fixture
def two_locales(tmp_path, monkeypatch):
    """Use a locales folder with a small English and French catalogue; English is active.

    common.back is only in English, as in an incomplete translation.
    """
    _write_catalogue(tmp_path, 'en', ENGLISH)
    _write_catalogue(tmp_path, 'fr', FRENCH)
    monkeypatch.setattr(i18n, 'LOCALES_DIR', tmp_path)
    monkeypatch.setattr(i18n, '_locale', 'en')
    load_catalogue.cache_clear()
    yield tmp_path
    load_catalogue.cache_clear()


@pytest.fixture
def warnings_logged():
    messages: list[str] = []
    sink_id = logger.add(messages.append, format='{message}', level='WARNING')
    yield messages
    logger.remove(sink_id)


def test_available_locales_should_list_catalogue_files(two_locales):
    assert available_locales() == ['en', 'fr']


def test_t_should_use_english_by_default(two_locales):
    assert t('common.cancel') == 'Cancel'


def test_t_should_use_locale_set_with_set_locale(two_locales):
    set_locale('fr')
    assert t('common.cancel') == 'Annuler'


def test_has_message_should_use_locale_set_with_set_locale(two_locales):
    (two_locales / 'fr.yaml').write_text('other:\n  key: "Texte"\n', encoding='utf-8')
    set_locale('fr')
    assert has_message('other.key')


def test_t_should_fall_back_to_english_for_key_missing_from_locale(two_locales):
    set_locale('fr')
    assert t('common.back') == 'Back'


def test_missing_translations_should_list_keys_missing_from_locale(two_locales):
    assert missing_translations('fr') == ['common.back']


def test_set_locale_should_log_one_warning_listing_missing_keys(two_locales, warnings_logged):
    set_locale('fr')
    assert len(warnings_logged) == 1
    assert 'common.back' in warnings_logged[0]


def test_set_locale_should_not_warn_for_complete_translation(two_locales, warnings_logged):
    _write_catalogue(two_locales, 'fr', _french_with(back='Retour'))
    set_locale('fr')
    assert warnings_logged == []


def test_t_should_use_translation_whose_placeholders_match_english(two_locales):
    set_locale('fr')
    assert t('common.updated', item_id='1.1') == '1.1 mis à jour'


@pytest.mark.parametrize(
    ('key', 'translation', 'params', 'english'),
    [
        ('updated', 'Mis à jour {item}', {'item_id': '1.1'}, 'Updated 1.1'),  # placeholder renamed
        ('updated', 'Mis à jour {item_id', {'item_id': '1.1'}, 'Updated 1.1'),  # broken brace
        ('updated', 'Mis à jour {}', {'item_id': '1.1'}, 'Updated 1.1'),  # unnamed placeholder
        ('updated', 'Mis à jour', {'item_id': '1.1'}, 'Updated 1.1'),  # placeholder left out
        ('found', '{count} fichiers trouvés', {'count': 3}, '3 files found'),  # one/other forms lost
    ],
)
def test_t_should_use_english_when_translation_cannot_be_filled_in_like_english(
    two_locales, key, translation, params, english
):
    _write_catalogue(two_locales, 'fr', _french_with(**{key: translation}))
    set_locale('fr')
    assert t(f'common.{key}', **params) == english


def test_mismatched_translations_should_list_keys_whose_placeholders_differ(two_locales):
    _write_catalogue(two_locales, 'fr', _french_with(updated='Mis à jour {item}', found='{count} trouvés'))
    assert mismatched_translations('fr') == ['common.found', 'common.updated']


def test_set_locale_should_list_missing_and_mismatched_keys_in_one_warning(two_locales, warnings_logged):
    _write_catalogue(two_locales, 'fr', _french_with(updated='Mis à jour {item}'))
    set_locale('fr')
    assert len(warnings_logged) == 1
    assert 'common.back' in warnings_logged[0]
    assert 'common.updated' in warnings_logged[0]


def test_t_should_not_log_warning_when_falling_back_to_english(two_locales, warnings_logged):
    set_locale('fr')
    warnings_logged.clear()
    t('common.back')
    assert warnings_logged == []


def test_t_should_raise_key_error_for_key_missing_from_locale_and_english(two_locales):
    set_locale('fr')
    with pytest.raises(KeyError):
        t('common.unknown')


def test_has_message_should_be_true_for_key_only_in_english(two_locales):
    set_locale('fr')
    assert has_message('common.back')


def test_app_settings_locale_should_default_to_en(monkeypatch):
    monkeypatch.delenv('LOCALE', raising=False)
    assert AppSettings(_env_file=None).locale == 'en'


def test_app_settings_should_accept_locale_with_catalogue():
    assert AppSettings(_env_file=None, locale='en').locale == 'en'


def test_app_settings_should_reject_locale_without_catalogue():
    with pytest.raises(ValidationError, match='Available: en'):
        AppSettings(_env_file=None, locale='xx')


@pytest.mark.parametrize('locale', TRANSLATIONS)
def test_translation_should_report_problems(locale):
    """Translation problems don't break the app (it shows English for those messages): report them, don't fail."""
    problems = {
        'not translated yet': missing_translations(locale),
        'whose placeholders or one/other forms differ from English': mismatched_translations(locale),
        'not in en.yaml': sorted(set(_leaves(load_catalogue(locale))) - set(_leaves(load_catalogue('en')))),
    }
    for problem, keys in problems.items():
        if keys:
            warnings.warn(f'{locale}.yaml: {len(keys)} messages {problem}: {", ".join(keys)}', stacklevel=1)


# ---------------------------------------------------------------------------
# Guard: user-facing text must come from the catalogue
# ---------------------------------------------------------------------------


def _inline_ui_text() -> list[str]:
    found = []
    for path in UI_TEXT_FILES:
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, 'id', None)
            if name not in UI_TEXT_CALLS:
                continue
            text_args = [*node.args, *(kw.value for kw in node.keywords if kw.arg in UI_TEXT_CALLS[name])]
            if any(_has_words(arg) for arg in text_args):
                found.append(f'{path.relative_to(PACKAGE_DIR.parent)}:{node.lineno} {name}()')
    return found


def test_ui_text_should_come_from_catalogue():
    inline = _inline_ui_text()
    assert not inline, 'Inline user-facing text; add it to pydatacuration/locales/en.yaml and use t():\n' + '\n'.join(
        inline
    )
