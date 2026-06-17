"""The database settings model."""

# pydatacuration/db/settings.py
from typing import Literal

from pydantic import BaseModel
from pydantic import model_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class DBType(BaseModel):
    """Type for supported database backends."""

    db_type: Literal['duckdb', 'postgresql'] = 'duckdb'

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

    database_url: str | None = None
    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_host: str = 'localhost'
    postgres_port: int = 5432
    postgres_db: str | None = None

    def build_postgres_url(self) -> str:
        if self.database_url:
            url = self.database_url
            if url.startswith('postgresql://'):
                url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
            return url
        if not all([self.postgres_user, self.postgres_password, self.postgres_db]):
            msg = 'PostgreSQL backend requires either DATABASE_URL or POSTGRES_USER + POSTGRES_PASSWORD + POSTGRES_DB.'
            raise ValueError(msg)
        return f'postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}'
