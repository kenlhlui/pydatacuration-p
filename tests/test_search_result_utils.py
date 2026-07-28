"""Test utils.search_result_utils.py"""

import json
from pathlib import Path

import pytest

from pydatacuration.utils.search_result_utils import DataSetDataModel
from pydatacuration.utils.search_result_utils import DatasetItemModel
from pydatacuration.utils.search_result_utils import DatasetSearchResultModel
from pydatacuration.utils.search_result_utils import get_search_result


@pytest.fixture
def search_result_ok() -> dict:
    return json.loads(
        Path('tests/fixtures/search_result_ok.json').read_text(
            encoding='utf-8',
        ),
    )


def test_dataset_search_result_model(search_result_ok: dict) -> None:
    """Test loading a search result into the DatasetSearchResultModel."""
    result = DatasetSearchResultModel(**search_result_ok)

    assert isinstance(result, DatasetSearchResultModel)
    assert isinstance(result.data, DataSetDataModel)
    assert isinstance(result.data.items, list)
    assert isinstance(result.data.items[0], DatasetItemModel)
    assert result.data.items[0].name == 'Sample Dataset Alpha'


def test_load_search_result_ok(search_result_ok: dict) -> None:
    """Test loading a search result."""
    result = get_search_result(search_result_ok)
    result_num = 2

    assert isinstance(result, list)
    assert len(result) == result_num
    assert result[0]['name'] == 'Sample Dataset Alpha'
    assert result[1]['name'] == 'Sample Dataset Beta'
    assert result[0]['fileCount'] == 0
