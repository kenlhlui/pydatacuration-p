"""Tests the setup form models."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from pydatacuration.backend.models.setup_form import SetupBase
from pydatacuration.backend.models.setup_form import SetupForm
from pydatacuration.backend.models.setup_form import validate_setup_form_input


@pytest.mark.parametrize(
    ('project_number'),
    [
        'Project_123',
        'Project-456',
        'Project789',
        '',
    ],
)
def test_setup_base_accepts_valid_project_number(project_number: str) -> None:
    """Test valid project numbers."""
    model = SetupBase(project_number=project_number)
    assert model.project_number == project_number


@pytest.mark.parametrize(
    ('project_number'),
    ['Invalid Project!', 'Invalid@Project', 'Invalid#Project', 'Invalid Project', 'Invalid Project'],
)
def test_setup_base_rejects_invalid_project_number(project_number: str) -> None:
    """Test invalid project numbers."""
    with pytest.raises(ValidationError):
        SetupBase(project_number=project_number)


@pytest.mark.parametrize(
    ('base_url', 'expected'),
    [
        ('https://example.com', 'https://example.com/'),
        ('https://example.com/', 'https://example.com/'),
        ('http://example.com', 'http://example.com/'),
        ('https://demo.example.com/', 'https://demo.example.com/'),
        (None, None),
    ],
)
def test_setup_form_serializes_base_url(
    base_url: str | None,
    expected: str | None,
) -> None:
    """Test base_url serialization."""
    form = SetupForm(base_url=base_url)

    assert form.model_dump()['base_url'] == expected


def test_setup_form_serializes_base_url_and_dirs(tmp_path: Path) -> None:
    """Test SetupForm serialization."""
    main_dir = tmp_path / 'main'
    res_dir = tmp_path / 'res'
    main_dir.mkdir()
    res_dir.mkdir()

    form = SetupForm(
        base_url='https://example.com',
        main_dir=str(main_dir),
        res_dir=str(res_dir),
    )

    dumped = form.model_dump()

    assert dumped['base_url'] == 'https://example.com/'
    assert dumped['main_dir'] == str(main_dir.resolve())
    assert dumped['res_dir'] == str(res_dir.resolve())


@pytest.mark.parametrize(
    ('field_name', 'value'),
    [
        ('base_url', 'https://example.com'),
        ('api_token', '12345678-1234-1234-1234-123456789012'),
        ('curator_email', 'alice@example.com'),
    ],
)
def test_validate_setup_form_input_accepts_valid_values(
    field_name: str,
    value: str,
) -> None:
    """Test valid values pass annotation validation."""
    rule = validate_setup_form_input(SetupBase, field_name)

    assert rule(value) is None


@pytest.mark.parametrize(
    ('field_name', 'value'),
    [
        ('base_url', 'not-a-url'),
        ('api_token', 'not-a-uuid'),
        ('curator_email', 'not-an-email'),
    ],
)
def test_validate_setup_form_input_rejects_invalid_values(
    field_name: str,
    value: str,
) -> None:
    """Test invalid values return an error message."""
    rule = validate_setup_form_input(SetupBase, field_name)

    assert rule(value) is not None


@pytest.mark.parametrize(
    ('field_name', 'value'),
    [
        ('project_number', ''),
        ('project_number', None),
        ('base_url', None),
    ],
)
def test_validate_setup_form_input_required_rejects_empty_values(
    field_name: str,
    value: object,
) -> None:
    """Test required fields reject empty input."""
    rule = validate_setup_form_input(SetupBase, field_name, required=True)

    assert rule(value) == 'This field is required'


def test_validate_setup_form_input_does_not_apply_project_number_validator() -> None:
    """Test annotation validation does not run custom field validators."""
    rule = validate_setup_form_input(SetupBase, 'project_number')

    assert rule('Invalid Project!') is None


@pytest.mark.parametrize(
    ('field_name', 'value', 'expected_error'),
    [
        ('base_url', 'not-a-url', 'Input should be a valid URL, relative URL without a base'),
        (
            'api_token',
            'not-a-uuid',
            'Input should be a valid UUID, invalid character: expected an optional prefix of `urn:uuid:` followed by [0-9a-fA-F-], found `n` at 1',  # noqa: E501
        ),
    ],
)
def test_validate_setup_form_input_return_errors(
    field_name: str,
    value: str,
    expected_error: str,
) -> None:
    """Test annotation validation returns error messages."""
    rule = validate_setup_form_input(SetupBase, field_name)
    assert rule(value) == expected_error
