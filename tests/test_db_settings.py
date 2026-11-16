"""Test building the PostgreSQL URL in DBSettings (db/settings.py)."""

import pytest
from sqlalchemy import make_url

from pydatacuration.db.settings import DBSettings


SPECIAL_VALUES = ['p@ss', 'p/ss', 'p:ss', 'p ss', 'p%ss', 'p@ss/w:rd']


def make_settings(user: str = 'curation', password: str = 'curation') -> DBSettings:
    """Return settings built from arguments only, ignoring any .env file and DATABASE_URL.

    Returns:
        DBSettings: The settings.
    """
    return DBSettings(
        _env_file=None,
        database_url=None,
        postgres_user=user,
        postgres_password=password,
        postgres_host='localhost',
        postgres_port=5432,
        postgres_db='curation',
    )


@pytest.mark.parametrize('password', SPECIAL_VALUES)
def test_build_postgres_url_keeps_special_characters_in_password(password: str) -> None:
    """Test that a password with URL special characters is escaped and parses back unchanged."""
    url = make_settings(password=password).build_postgres_url()

    assert make_url(url).password == password


@pytest.mark.parametrize('user', SPECIAL_VALUES)
def test_build_postgres_url_keeps_special_characters_in_user(user: str) -> None:
    """Test that a user name with URL special characters is escaped and parses back unchanged."""
    url = make_settings(user=user).build_postgres_url()

    assert make_url(url).username == user


def test_build_postgres_url_is_unchanged_for_plain_values() -> None:
    """Test that a URL without special characters looks the same as before escaping was added."""
    url = make_settings().build_postgres_url()

    assert url == 'postgresql+psycopg://curation:curation@localhost:5432/curation'
