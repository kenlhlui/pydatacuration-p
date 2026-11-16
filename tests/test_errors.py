"""Tests for showing errors to users: generic text from the catalogue, with a reference ID that is in the log."""

import re

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from loguru import logger

from pydatacuration.backend import api
from pydatacuration.backend.models.setup_form import SetupForm
from pydatacuration.backend.models.setup_form import validate_setup_form_input
from pydatacuration.backend.services import curation
from pydatacuration.exceptions import DatasetAccessError
from pydatacuration.exceptions import DatasetNotFoundError
from pydatacuration.exceptions import DatasetUnauthorizedError
from pydatacuration.exceptions import DirectoryExistsError
from pydatacuration.exceptions import FileMatchError
from pydatacuration.exceptions import describe_error
from pydatacuration.i18n import t


SECRET_DETAIL = 'connection to /srv/private/path failed: token=abc123'
REFERENCE = re.compile(r'\b[0-9a-f]{8}\b')


@pytest.fixture
def log_messages():
    messages: list[str] = []
    sink_id = logger.add(messages.append, format='{message}', level='DEBUG')
    yield messages
    logger.remove(sink_id)


# ---------------------------------------------------------------------------
# describe_error
# ---------------------------------------------------------------------------


def test_describe_error_should_not_show_exception_text_for_unexpected_error():
    assert SECRET_DETAIL not in describe_error(RuntimeError(SECRET_DETAIL))


def test_describe_error_should_show_generic_message_for_unexpected_error():
    assert describe_error(RuntimeError(SECRET_DETAIL)).startswith(t('errors.unexpected'))


def test_describe_error_should_include_reference_id():
    assert REFERENCE.search(describe_error(RuntimeError(SECRET_DETAIL)))


def test_describe_error_should_give_each_error_its_own_reference_id():
    first = REFERENCE.search(describe_error(RuntimeError('a'))).group()
    second = REFERENCE.search(describe_error(RuntimeError('a'))).group()
    assert first != second


def test_describe_error_should_log_reference_id_with_exception_detail(log_messages):
    reference = REFERENCE.search(describe_error(RuntimeError(SECRET_DETAIL))).group()
    assert any(reference in m and SECRET_DETAIL in m for m in log_messages)


def test_describe_error_should_start_log_entry_with_reference_as_shown_and_the_error(log_messages):
    reference = REFERENCE.search(describe_error(RuntimeError(SECRET_DETAIL))).group()
    first_lines = [m.splitlines()[0] for m in log_messages]
    assert f'Reference: {reference} | RuntimeError: {SECRET_DETAIL}' in first_lines


def test_describe_error_should_log_traceback(log_messages):
    try:
        raise RuntimeError(SECRET_DETAIL)
    except RuntimeError as exc:
        describe_error(exc)
    assert any('Traceback' in m for m in log_messages)


def test_describe_error_should_not_log_local_variable_values(log_messages):
    def run_with_token():
        api_token = 'TOKEN-VALUE-0000'  # a local variable, as in the curation code path
        msg = f'failed after {len(api_token)} chars'
        raise RuntimeError(msg)

    try:
        run_with_token()
    except RuntimeError as exc:
        describe_error(exc)
    assert not any('TOKEN-VALUE-0000' in m for m in log_messages)


@pytest.mark.parametrize(
    ('exc', 'key'),
    [
        (DatasetUnauthorizedError(SECRET_DETAIL), 'errors.dataset_unauthorized'),
        (DatasetNotFoundError(SECRET_DETAIL), 'errors.dataset_not_found'),
        (DatasetAccessError(SECRET_DETAIL), 'errors.dataset_access'),
        (FileMatchError(SECRET_DETAIL), 'errors.file_mismatch'),
    ],
)
def test_describe_error_should_show_catalogue_message_for_known_error(exc, key):
    assert describe_error(exc).startswith(t(key))


def test_describe_error_should_not_show_detail_of_known_error():
    assert SECRET_DETAIL not in describe_error(DatasetAccessError(SECRET_DETAIL))


def test_describe_error_should_fill_in_params_of_known_error():
    text = describe_error(DirectoryExistsError(SECRET_DETAIL, project_number='CUR-1'))
    assert text.startswith(t('errors.project_exists', project_number='CUR-1'))


def test_known_error_str_should_keep_detail_for_the_log():
    assert str(DirectoryExistsError(SECRET_DETAIL, project_number='CUR-1')) == SECRET_DETAIL


# ---------------------------------------------------------------------------
# curation service
# ---------------------------------------------------------------------------


def test_dataset_access_error_should_not_include_underlying_exception_text(monkeypatch):
    def fail(*_args):
        raise RuntimeError(SECRET_DETAIL)

    monkeypatch.setattr(curation, 'check_ds_read_access', fail)
    with pytest.raises(DatasetAccessError) as exc_info:
        curation._ensure_dataset_read_access(SetupForm(pid='doi:10.1/X', project_number='CUR-1'))
    assert SECRET_DETAIL not in str(exc_info.value)


def test_directory_exists_error_should_carry_project_number(tmp_path):
    (tmp_path / 'projects' / 'CUR-1').mkdir(parents=True)
    with pytest.raises(DirectoryExistsError) as exc_info:
        curation.init_curation(SetupForm(project_number='CUR-1', main_dir=tmp_path))
    assert exc_info.value.params == {'project_number': 'CUR-1'}


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


def _client(monkeypatch, exc: Exception) -> TestClient:
    async def fail(_body):
        raise exc

    monkeypatch.setattr(api, 'run_curation', fail)
    app = FastAPI()
    app.include_router(api.router)
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    ('exc', 'status_code'),
    [
        (DirectoryExistsError(SECRET_DETAIL, project_number='CUR-1'), 409),
        (DatasetUnauthorizedError(SECRET_DETAIL), 401),
        (DatasetNotFoundError(SECRET_DETAIL), 404),
        (DatasetAccessError(SECRET_DETAIL), 503),
        (RuntimeError(SECRET_DETAIL), 500),
    ],
)
def test_run_curation_endpoint_should_return_status_code_for_error(monkeypatch, exc, status_code):
    response = _client(monkeypatch, exc).post('/run-curation', json={'project_number': 'CUR-1'})
    assert response.status_code == status_code


@pytest.mark.parametrize(
    'exc',
    [DatasetAccessError(SECRET_DETAIL), RuntimeError(SECRET_DETAIL)],
)
def test_run_curation_endpoint_should_not_return_exception_text(monkeypatch, exc):
    response = _client(monkeypatch, exc).post('/run-curation', json={'project_number': 'CUR-1'})
    assert SECRET_DETAIL not in response.json()['detail']


def test_run_curation_endpoint_should_return_reference_id(monkeypatch):
    response = _client(monkeypatch, RuntimeError(SECRET_DETAIL)).post('/run-curation', json={'project_number': 'CUR-1'})
    assert REFERENCE.search(response.json()['detail'])


# ---------------------------------------------------------------------------
# Setup form field validation
# ---------------------------------------------------------------------------


def test_form_rule_should_return_required_message_when_empty():
    assert validate_setup_form_input(SetupForm, 'pid', required=True)('') == t('common.required_field')


def test_form_rule_should_return_invalid_message_when_value_is_invalid():
    rule = validate_setup_form_input(SetupForm, 'curator_email', invalid_message='Bad email')
    assert rule('not-an-email') == 'Bad email'


def test_form_rule_should_return_none_when_value_is_valid():
    rule = validate_setup_form_input(SetupForm, 'curator_email', invalid_message='Bad email')
    assert rule('name@example.com') is None
