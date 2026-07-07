"""Module for SQLmodels — backend-aware table definitions.

Supports both DuckDB and PostgreSQL column types through the ``backend`` parameter.
"""

from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import Any

from pydantic import field_serializer
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Interval
from sqlmodel import DATE
from sqlmodel import DATETIME
from sqlmodel import JSON
from sqlmodel import Field
from sqlmodel import SQLModel
from sqlmodel import SQLModel as BaseSQLModel
from sqlmodel import String
from sqlmodel import text

from pydatacuration.db.settings import DBType


def _json_column_type(backend: DBType):
    """Return the appropriate JSON column type for the backend.

    PostgreSQL benefits from JSONB (indexed, faster queries).
    DuckDB uses plain JSON.
    """
    if backend.db_type == 'postgresql':
        from sqlalchemy.dialects.postgresql import JSONB

        return JSONB
    return JSON


def _datetime_column_type(backend: DBType):
    """Return the appropriate datetime column type for the backend.

    PostgreSQL uses TIMESTAMP; DuckDB uses DATETIME.
    """
    if backend.db_type == 'postgresql':
        from sqlalchemy import TIMESTAMP

        return TIMESTAMP
    return DATETIME


# NOTE: The description field does not write into the database; it's just for documentation purposes in this python file.
class DBModels:
    """SQLModels implementation for writing to DuckDB or PostgreSQL.

    Args:
        schema_name: The schema name for table placement.
        backend: The database type ('duckdb' or 'postgresql').
    """

    def __init__(self, schema_name: str, db_type: DBType | None = None) -> None:
        """Initialize DBModels with the specified schema name and backend.

        Args:
            schema_name (str): The name of the schema to use for the tables.
            db_type (DBType): The database type ('duckdb' or 'postgresql').
        """
        self.schema_name = schema_name
        self.db_type = db_type if db_type is not None else DBType()

    def project_metadata_record(self) -> type[SQLModel]:
        """Create a ProjectMetadata table class with the specified schema.

        Returns:
            type[SQLModel]: The ProjectMetadata class with the specified schema.
        """
        dt_type = _datetime_column_type(self.db_type)

        # Only clear if table already exists in metadata
        table_key = f'{self.schema_name}.project_metadata'
        if table_key in BaseSQLModel.metadata.tables:
            BaseSQLModel.metadata.remove(BaseSQLModel.metadata.tables[table_key])

        class ProjectMetadata(SQLModel, table=True):
            """Project metadata table model."""

            __tablename__ = 'project_metadata'  # type: ignore[assignment]
            __table_args__ = {'schema': self.schema_name}
            project_number: str = Field(
                default='', sa_column=Column(String, nullable=False, unique=True), description='Unique project number'
            )
            curator_name: str = Field(
                default='', sa_column=Column(String, nullable=False), description='Name of the data curator'
            )
            curator_email: str = Field(
                default='', sa_column=Column(String, nullable=False), description='Email of the data curator'
            )
            dataset_title: str = Field(
                default='', sa_column=Column(String, nullable=False), description='Title of the dataset'
            )
            dataset_pid: str = Field(
                default='', sa_column=Column(String, nullable=False), description='Persistent identifier of the dataset'
            )
            dataset_id: int = Field(
                sa_column=Column(Integer, primary_key=True, autoincrement=False, nullable=False),
                description='Versioned ID of the dataset',
            )
            datasetid: int = Field(
                sa_column=Column(Integer, nullable=False), description='Persistent ID of the dataset'
            )
            dataset_url: str = Field(
                default='', sa_column=Column(String, nullable=False), description='URL of the dataset'
            )
            dataset_path: str | None = Field(
                default=None,
                sa_column=Column(String, nullable=True),
                description='Path of the dataset in the repository',
            )
            checklist_type: str = Field(
                default='default',
                sa_column=Column(String, nullable=False),
                description='Type of checklist used, defined by its suffix (e.g., "high" for "checklist-high.yaml"). checklist.yaml is considered "default".',  # noqa: E501
            )
            log_init_date: date = Field(
                sa_column=Column(DATE, nullable=False, server_default=text('CURRENT_DATE')),
                description='Date when the log was initialized',
            )
            log_last_update_date: date = Field(
                default=date.today(),
                sa_column=Column(DATE, nullable=False),
                description='Date when the log was last updated',
            )
            last_modified_datetime: datetime = Field(
                default_factory=datetime.today,
                nullable=False,
                sa_type=dt_type,
                sa_column_kwargs={'onupdate': lambda: datetime.today()},
                description='Last modified datetime',
            )

        return ProjectMetadata

    def checklist_metadata(self) -> type[SQLModel]:
        """Create a ChecklistMetadata table class with the specified schema.

        Returns:
            type[SQLModel]: The ChecklistMetadata class with the specified schema.
        """
        # Only clear if table already exists in metadata
        table_key = f'{self.schema_name}.checklist_metadata'
        if table_key in BaseSQLModel.metadata.tables:
            BaseSQLModel.metadata.remove(BaseSQLModel.metadata.tables[table_key])

        class ChecklistMetadata(SQLModel, table=True):
            """Checklist metadata table model."""

            __tablename__ = 'checklist_metadata'  # type: ignore[assignment]
            __table_args__ = {'schema': self.schema_name}
            name: str = Field(
                default='',
                sa_column=Column(String, nullable=False, primary_key=True),
                description='Name of the checklist',
            )
            version: str = Field(
                default='',
                sa_column=Column(String, nullable=False),
                description='Version of the checklist, should follow semantic versioning (e.g., "1.0.0")',
            )
            description: str = Field(
                default='',
                sa_column=Column(String, nullable=True),
                description='Description of the checklist',
            )
            created_by: list[str] = Field(
                default_factory=list,
                sa_column=Column(_json_column_type(self.db_type), nullable=False),
                description='List of people who created the checklist',
            )
            last_updated: date = Field(
                default=date.today(),
                sa_column=Column(DATE, nullable=False),
                description='Date when the checklist was last updated',
            )
            status: str = Field(
                default='draft',
                sa_column=Column(String, nullable=False),
                description='Status of the checklist, either draft, active, or deprecated',
            )

        return ChecklistMetadata

    def checklist(self) -> type[SQLModel]:
        """Create a Checklist table class with the specified schema.

        Returns:
            type[SQLModel]: The Checklist class with the specified schema.
        """
        json_type = _json_column_type(self.db_type)
        dt_type = _datetime_column_type(self.db_type)

        # Clear metadata to avoid "already defined" errors in long-running processes
        table_key = f'{self.schema_name}.checklist'
        if table_key in BaseSQLModel.metadata.tables:
            BaseSQLModel.metadata.remove(BaseSQLModel.metadata.tables[table_key])

        class Checklist(SQLModel, table=True):
            """Checklist table model."""

            __tablename__ = 'checklist'  # type: ignore[assignment]
            __table_args__ = {'schema': self.schema_name, 'extend_existing': True}

            id: str = Field(
                sa_column=Column(String, nullable=False, primary_key=True), description='Unique checklist identifier'
            )
            action: str = Field(sa_column=Column(String, nullable=True), description='Checklist action description')
            instructions: str = Field(sa_column=Column(String, nullable=True), description='Checklist instructions')
            priority: str = Field(sa_column=Column(String, nullable=True), description='Checklist priority')
            section: str = Field(sa_column=Column(String, nullable=True), description='Checklist section')
            automated_check_ids: list[str] = Field(
                sa_column=Column(json_type, nullable=True), description='List of automated check IDs'
            )
            tool_explanation: str = Field(
                sa_column=Column(String, nullable=True),
                description='Explanation of what automated tools check for this item (shown to user, supports markdown)',  # noqa: E501
            )
            curator_check_item: str = Field(
                sa_column=Column(String, nullable=True),
                description='Curator check item (shown to user, supports markdown)',
            )
            check_type: str = Field(sa_column=Column(String, nullable=True), description='Type of check')
            status: str = Field(sa_column=Column(String, nullable=True), description='Checklist status')
            comments: str = Field(sa_column=Column(String, nullable=True), description="Curator's Comments")
            time_spent: timedelta = Field(
                sa_column=Column(Interval, nullable=True), description='Time spent on this item'
            )
            last_modified_datetime: datetime = Field(
                default_factory=datetime.today,
                nullable=False,
                sa_type=dt_type,
                sa_column_kwargs={'onupdate': lambda: datetime.today()},
                description='Last modified datetime',
            )

            @field_serializer('time_spent')
            def serialize_time_spent(self, value: timedelta | None, _info: Any) -> str | None:
                """Serialize timedelta to MM:SS format for JSON compatibility."""
                if value is None:
                    return None
                total_seconds = int(value.total_seconds())
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                return f'{minutes:02d}:{seconds:02d}'

        return Checklist

    def check_results(self) -> type[SQLModel]:
        """Create a CheckResult table class with the specified schema.

        Returns:
            type[SQLModel]: The CheckResult class with the specified schema.
        """
        json_type = _json_column_type(self.db_type)
        dt_type = _datetime_column_type(self.db_type)

        # Clear metadata to avoid "already defined" errors in long-running processes
        table_key = f'{self.schema_name}.check_results'
        if table_key in BaseSQLModel.metadata.tables:
            BaseSQLModel.metadata.remove(BaseSQLModel.metadata.tables[table_key])

        class CheckResult(SQLModel, table=True):
            """Check result list table model."""

            __tablename__ = 'check_results'  # type: ignore[assignment]
            __table_args__ = {'schema': self.schema_name, 'extend_existing': True}

            check_name: str = Field(sa_column=Column(String, nullable=False), description='Name of the check')
            check_id: str = Field(
                sa_column=Column(String, nullable=False, primary_key=True), description='ID of the check'
            )
            description: str = Field(
                sa_column=Column(String, nullable=False),
                description='Description of the check for database documentation',
            )
            unit: str = Field(sa_column=Column(String, nullable=False), description='Unit of each result item')
            results: list[str] | list[dict] = Field(
                sa_column=Column(json_type, nullable=False), description='(Nested) List of check results'
            )
            last_modified_datetime: datetime = Field(
                default_factory=datetime.today,
                nullable=False,
                sa_type=dt_type,
                sa_column_kwargs={'onupdate': lambda: datetime.today()},
                description='Last modified datetime',
            )

        return CheckResult
