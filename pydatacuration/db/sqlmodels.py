"""Module for SQLmodels."""

from datetime import UTC
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
from sqlmodel import TIMESTAMP
from sqlmodel import Field
from sqlmodel import SQLModel
from sqlmodel import SQLModel as BaseSQLModel
from sqlmodel import String
from sqlmodel import text


class DatabaseModels:
    """SQLmodels implementation for writing to Database (SQLite and PostgreSQL).

    Uses a unified table naming convention: schema_name__table_name (double underscore separator)
    to maximize compatibility across both SQLite and PostgreSQL without relying on PostgreSQL schemas.
    """

    def __init__(self, schema_name: str) -> None:
        """Initialize DatabaseModels with the specified schema name.

        Args:
            schema_name (str): The name of the schema prefix to use for the Database tables.
        """
        self.schema_name = schema_name

    def project_metadata_record(self) -> type[SQLModel]:
        """Create a ProjectMetadata table class with the specified schema.

        Returns:
            type[SQLModel]: The ProjectMetadata class with the specified schema.
        """
        # Only clear if table already exists in metadata
        table_name = f'{self.schema_name}__project_metadata'
        if table_name in BaseSQLModel.metadata.tables:
            BaseSQLModel.metadata.remove(BaseSQLModel.metadata.tables[table_name])

        class ProjectMetadata(SQLModel, table=True):
            """Project metadata table model."""

            __tablename__ = table_name  # type: ignore[assignment]
            __table_args__ = {'extend_existing': True}
            ticket_number: str = Field(
                default='', sa_column=Column(String, nullable=False, unique=True), description='Unique ticket number'
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
            dataset_path: str = Field(
                default='',
                sa_column=Column(String, nullable=False),
                description='Path of the dataset in the repository',
            )
            checklist_type: str = Field(
                default='high',
                sa_column=Column(String, nullable=False),
                description='Type of checklist used (medium or high)',
            )
            log_init_date: date = Field(
                sa_column=Column(DATE, nullable=False, server_default=text('CURRENT_DATE')),
                description='Date when the log was initialized',
            )
            log_last_update_date: date = Field(
                default=datetime.now().astimezone().date(),
                sa_column=Column(DATE, nullable=False),
                description='Date when the log was last updated',
            )
            last_modified_datetime: datetime = Field(
                default_factory=lambda: datetime.now(UTC),
                sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
                description='Timestamp when the log was last modified (stored as UTC)',
            )

        return ProjectMetadata

    def checklist(self) -> type[SQLModel]:
        """Create a Checklist table class with the specified schema.

        Returns:
            type[SQLModel]: The Checklist class with the specified schema.
        """
        # Clear metadata to avoid "already defined" errors in long-running processes
        table_name = f'{self.schema_name}__checklist'
        if table_name in BaseSQLModel.metadata.tables:
            BaseSQLModel.metadata.remove(BaseSQLModel.metadata.tables[table_name])

        class Checklist(SQLModel, table=True):
            """Checklist table model."""

            __tablename__ = table_name  # type: ignore[assignment]
            __table_args__ = {'extend_existing': True}

            id: str = Field(
                sa_column=Column(String, nullable=False, primary_key=True), description='Unique checklist identifier'
            )
            action: str = Field(sa_column=Column(String, nullable=True), description='Checklist action description')
            instructions: str = Field(sa_column=Column(String, nullable=True), description='Checklist instructions')
            priority: str = Field(sa_column=Column(String, nullable=True), description='Checklist priority')
            section: str = Field(sa_column=Column(String, nullable=True), description='Checklist section')
            automated_check_ids: list[str] = Field(
                sa_column=Column(JSON, nullable=True), description='List of automated check IDs'
            )
            tool_explanation: str = Field(
                sa_column=Column(String, nullable=True),
                description='Explanation of what automated tools check for this item (shown to user, supports markdown)',
            )
            information_location: str = Field(
                sa_column=Column(String, nullable=True), description='Location of information'
            )
            check_type: str = Field(sa_column=Column(String, nullable=True), description='Type of check')
            status: str = Field(sa_column=Column(String, nullable=True), description='Checklist status')
            comments: str = Field(sa_column=Column(String, nullable=True), description="Curator's Comments")
            time_spent: timedelta = Field(
                sa_column=Column(Interval, nullable=True), description='Time spent on this item'
            )
            last_modified_datetime: datetime = Field(
                default_factory=lambda: datetime.now(UTC),
                sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
                description='Last modified datetime (stored as UTC)',
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
        """Check the result list for the specified schema.

        Returns:
            type[SQLModel]: The CheckResult class with the specified schema.
        """
        # Clear metadata to avoid "already defined" errors in long-running processes
        table_name = f'{self.schema_name}__check_results'
        if table_name in BaseSQLModel.metadata.tables:
            BaseSQLModel.metadata.remove(BaseSQLModel.metadata.tables[table_name])

        class CheckResult(SQLModel, table=True):
            """Check result list table model."""

            __tablename__ = table_name  # type: ignore[assignment]
            __table_args__ = {'extend_existing': True}

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
                sa_column=Column(JSON, nullable=False), description='(Nested) List of check results'
            )  # This support writing a list[str] and list[dict] to duckdb # noqa
            last_modified_datetime: datetime = Field(
                default_factory=lambda: datetime.now(UTC),
                sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
                description='Last modified datetime (stored as UTC)',
            )

        return CheckResult
