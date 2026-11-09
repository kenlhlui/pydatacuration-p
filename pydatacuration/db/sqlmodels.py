"""Module for SQLModels — table definitions shared by the DuckDB and PostgreSQL backends.

Column types that differ per backend use SQLAlchemy variants, so one class works for both.
"""

from datetime import UTC
from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import Any

from pydantic import field_serializer
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import Interval
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import DATE
from sqlmodel import JSON
from sqlmodel import Field
from sqlmodel import SQLModel
from sqlmodel import String
from sqlmodel import text


# PostgreSQL benefits from JSONB (indexed, faster queries); DuckDB uses plain JSON.
JSON_TYPE = JSON().with_variant(JSONB(), 'postgresql')


def utc_now() -> datetime:
    """Return the current UTC time as a naive datetime.

    The datetime columns store UTC with no time zone attached. Do not write an aware datetime to them:
    the database would silently convert it to the session's local time.
    """
    return datetime.now(UTC).replace(tzinfo=None)


def utc_today() -> date:
    """Return the current date in UTC."""
    return datetime.now(UTC).date()


# The same as utc_today(), computed by the database. CURRENT_DATE would use the session's local time zone.
UTC_TODAY_SQL = text("CAST(timezone('UTC', now()) AS DATE)")


# NOTE: The description field does not write into the database; it's just for documentation purposes in this python file.
class ProjectMetadata(SQLModel, table=True):
    """Project metadata table model."""

    __tablename__ = 'project_metadata'  # type: ignore[assignment]

    project_number: str = Field(
        sa_column=Column(
            String,
            nullable=False,
            unique=True,
            primary_key=True,
        ),
        description='Unique project number',
    )
    curator_name: str = Field(
        default='', sa_column=Column(String, nullable=False), description='Name of the data curator'
    )
    curator_email: str = Field(
        default='', sa_column=Column(String, nullable=False), description='Email of the data curator'
    )
    dataset_title: str = Field(default='', sa_column=Column(String, nullable=False), description='Title of the dataset')
    dataset_pid: str = Field(
        default='', sa_column=Column(String, nullable=False), description='Persistent identifier of the dataset'
    )
    dataset_id: int = Field(
        sa_column=Column(Integer, autoincrement=False, nullable=False),
        description='Versioned ID of the dataset',
    )
    datasetid: int = Field(sa_column=Column(Integer, nullable=False), description='Persistent ID of the dataset')
    dataset_url: str = Field(default='', sa_column=Column(String, nullable=False), description='URL of the dataset')
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
        sa_column=Column(DATE, nullable=False, server_default=UTC_TODAY_SQL),
        description='Date when the log was initialized, in UTC',
    )
    log_last_update_date: date = Field(
        default_factory=utc_today,
        sa_column=Column(DATE, nullable=False),
        description='Date when the log was last updated, in UTC',
    )
    last_modified_datetime: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_type=DateTime,
        sa_column_kwargs={'onupdate': utc_now},
        description='Last modified datetime, in UTC (naive)',
    )


class ChecklistMetadata(SQLModel, table=True):
    """Checklist metadata table model."""

    __tablename__ = 'checklist_metadata'  # type: ignore[assignment]

    project_number: str = Field(
        foreign_key='project_metadata.project_number',
        primary_key=True,
    )
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
        sa_column=Column(JSON_TYPE, nullable=False),
        description='List of people who created the checklist',
    )
    last_updated: date = Field(
        default_factory=utc_today,
        sa_column=Column(DATE, nullable=False),
        description='Date when the checklist was last updated (from the checklist YAML; UTC if missing)',
    )
    status: str = Field(
        default='draft',
        sa_column=Column(String, nullable=False),
        description='Status of the checklist, either draft, active, or deprecated',
    )


class Checklist(SQLModel, table=True):
    """Checklist table model."""

    __tablename__ = 'checklist'  # type: ignore[assignment]

    project_number: str = Field(foreign_key='project_metadata.project_number', primary_key=True)
    id: str = Field(
        sa_column=Column(String, nullable=False, primary_key=True), description='Unique checklist identifier'
    )
    action: str = Field(sa_column=Column(String, nullable=True), description='Checklist action description')
    instructions: str = Field(sa_column=Column(String, nullable=True), description='Checklist instructions')
    priority: str = Field(sa_column=Column(String, nullable=True), description='Checklist priority')
    section: str = Field(sa_column=Column(String, nullable=True), description='Checklist section')
    automated_check_ids: list[str] = Field(
        sa_column=Column(JSON_TYPE, nullable=True), description='List of automated check IDs'
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
    time_spent: timedelta = Field(sa_column=Column(Interval, nullable=True), description='Time spent on this item')
    last_modified_datetime: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_type=DateTime,
        sa_column_kwargs={'onupdate': utc_now},
        description='Last modified datetime, in UTC (naive)',
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


class CheckResult(SQLModel, table=True):
    """Check result list table model."""

    __tablename__ = 'check_results'  # type: ignore[assignment]

    project_number: str = Field(foreign_key='project_metadata.project_number', primary_key=True)
    check_name: str = Field(sa_column=Column(String, nullable=False), description='Name of the check')
    check_id: str = Field(sa_column=Column(String, nullable=False, primary_key=True), description='ID of the check')
    description: str = Field(
        sa_column=Column(String, nullable=False),
        description='Description of the check for database documentation',
    )
    unit: str = Field(sa_column=Column(String, nullable=False), description='Unit of each result item')
    results: list[str] | list[dict] = Field(
        sa_column=Column(JSON_TYPE, nullable=False), description='(Nested) List of check results'
    )
    last_modified_datetime: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_type=DateTime,
        sa_column_kwargs={'onupdate': utc_now},
        description='Last modified datetime, in UTC (naive)',
    )


# Any of the shared tables; all of them have a project_number column.
TableModel = ProjectMetadata | ChecklistMetadata | Checklist | CheckResult
