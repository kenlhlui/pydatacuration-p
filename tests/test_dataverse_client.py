"""Tests for the request URLs built by DataverseClient."""

import httpx2
import pytest

from pydatacuration.services.api_calls import httpx_client as httpx_client_module
from pydatacuration.services.api_calls.dataverse_client import DataverseClient
from pydatacuration.services.api_calls.httpx_client import HTTPXClient


BASE_URL = 'https://dataverse.example.org'
MALICIOUS_PID = 'doi:10.5683/SP3/ABC&version=1.0#frag'


@pytest.fixture
def captured(monkeypatch):
    """Route sync_get through a MockTransport and record each request sent."""
    requests: list[httpx2.Request] = []
    real_client = httpx2.Client

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(200, json={'status': 'OK', 'data': {}})

    def fake_client(**kwargs):
        return real_client(transport=httpx2.MockTransport(handler), **kwargs)

    monkeypatch.setattr(httpx_client_module.httpx2, 'Client', fake_client)
    return requests


@pytest.fixture
def dv_client():
    """DataverseClient pointed at a fake base URL."""
    return DataverseClient(HTTPXClient(BASE_URL, api_token='dummy-token'))


# get_ds_metadata


def test_get_ds_metadata_should_call_persistent_id_endpoint(captured, dv_client):
    dv_client.get_ds_metadata('doi:10.5683/SP3/ABC')

    assert captured[0].url.path == '/api/datasets/:persistentId/'


def test_get_ds_metadata_should_send_pid_and_return_owners(captured, dv_client):
    dv_client.get_ds_metadata('doi:10.5683/SP3/ABC')

    assert dict(captured[0].url.params) == {'persistentId': 'doi:10.5683/SP3/ABC', 'returnOwners': 'true'}


def test_get_ds_metadata_should_keep_special_chars_inside_pid(captured, dv_client):
    dv_client.get_ds_metadata(MALICIOUS_PID)

    assert captured[0].url.params.get_list('persistentId') == [MALICIOUS_PID]


def test_get_ds_metadata_should_not_inject_version_param(captured, dv_client):
    dv_client.get_ds_metadata(MALICIOUS_PID)

    assert 'version' not in captured[0].url.params


def test_get_ds_metadata_should_not_produce_fragment(captured, dv_client):
    dv_client.get_ds_metadata(MALICIOUS_PID)

    assert captured[0].url.fragment == ''


# search_depositor_record


def test_search_depositor_record_should_send_search_params(captured, dv_client):
    dv_client.search_depositor_record('Jane Doe')

    assert dict(captured[0].url.params) == {
        'q': '*',
        'type': 'dataset',
        'per_page': '1000',
        'fq': 'depositor:"Jane Doe"',
    }


def test_search_depositor_record_should_add_subtree_when_alias_given(captured, dv_client):
    dv_client.search_depositor_record('Jane Doe', collection_alias='econ')

    assert captured[0].url.params['subtree'] == 'econ'


def test_search_depositor_record_should_omit_subtree_when_no_alias(captured, dv_client):
    dv_client.search_depositor_record('Jane Doe')

    assert 'subtree' not in captured[0].url.params


def test_search_depositor_record_should_escape_double_quotes(captured, dv_client):
    dv_client.search_depositor_record('Jane "JD" Doe')

    assert captured[0].url.params['fq'] == r'depositor:"Jane \"JD\" Doe"'


def test_search_depositor_record_should_escape_backslashes(captured, dv_client):
    dv_client.search_depositor_record('DOMAIN\\jdoe')

    assert captured[0].url.params['fq'] == r'depositor:"DOMAIN\\jdoe"'


def test_search_depositor_record_should_not_allow_breaking_out_of_phrase(captured, dv_client):
    dv_client.search_depositor_record('x" OR depositor:"*')

    assert captured[0].url.params['fq'] == r'depositor:"x\" OR depositor:\"*"'


def test_search_depositor_record_should_not_let_trailing_backslash_escape_closing_quote(captured, dv_client):
    dv_client.search_depositor_record('jdoe\\')

    assert captured[0].url.params['fq'] == r'depositor:"jdoe\\"'


# search_dataset_by_version_id


def test_search_dataset_by_version_id_should_send_search_params(captured, dv_client):
    dv_client.search_dataset_by_version_id(123)

    assert dict(captured[0].url.params) == {
        'q': '*',
        'type': 'dataset',
        'per_page': '1',
        'fq': 'datasetVersionId:123',
    }


# get_ds_access_status


def test_get_ds_access_status_should_send_only_pid(captured, dv_client):
    dv_client.get_ds_access_status(MALICIOUS_PID)

    assert dict(captured[0].url.params) == {'persistentId': MALICIOUS_PID}


# get_ds_export_metadata


def test_get_ds_export_metadata_should_send_default_params(captured, dv_client):
    dv_client.get_ds_export_metadata('doi:10.5683/SP3/ABC')

    assert dict(captured[0].url.params) == {
        'exporter': 'OAI_ORE',
        'persistentId': 'doi:10.5683/SP3/ABC',
        'version': ':latest',
    }


def test_get_ds_export_metadata_should_omit_version_when_none(captured, dv_client):
    dv_client.get_ds_export_metadata('doi:10.5683/SP3/ABC', version=None)

    assert 'version' not in captured[0].url.params


def test_get_ds_export_metadata_should_not_let_pid_override_version(captured, dv_client):
    dv_client.get_ds_export_metadata(MALICIOUS_PID, version='2.0')

    assert captured[0].url.params.get_list('version') == ['2.0']
