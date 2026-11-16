"""The database settings model."""

# pydatacuration/db/settings.py
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from sqlalchemy import URL


class DBType(BaseModel):
    """Type for supported database backends."""

    db_type: Literal['duckdb', 'postgresql'] = Field(
        'duckdb', description='The database backend. DuckDB needs no setup; PostgreSQL needs a running server.'
    )

    @model_validator(mode='before')
    @classmethod
    def _coerce_string(cls, v: object) -> object:
        """Allow plain strings like ``"postgresql"`` in addition to dicts."""
        if isinstance(v, str):
            return {'db_type': v}
        return v


class DBSettings(BaseSettings, DBType):
    """Settings for database configuration."""

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    database_url: str | None = Field(
        None, description='PostgreSQL connection URL. If set, the other POSTGRES_* settings are ignored.'
    )
    postgres_user: str | None = Field(None, description='PostgreSQL user name. Required if DATABASE_URL is not set.')
    postgres_password: str | None = Field(None, description='PostgreSQL password. Required if DATABASE_URL is not set.')
    postgres_host: str = Field('localhost', description='PostgreSQL server host name.')
    postgres_port: int = Field(5432, description='PostgreSQL server port.')
    postgres_db: str | None = Field(None, description='PostgreSQL database name. Required if DATABASE_URL is not set.')

    def build_postgres_url(self) -> str:
        if self.database_url:
            url = self.database_url
            if url.startswith('postgresql://'):
                url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
            return url
        if not all([self.postgres_user, self.postgres_password, self.postgres_db]):
            msg = 'PostgreSQL backend requires either DATABASE_URL or POSTGRES_USER + POSTGRES_PASSWORD + POSTGRES_DB.'
            raise ValueError(msg)
        return URL.create(
            'postgresql+psycopg',
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)
