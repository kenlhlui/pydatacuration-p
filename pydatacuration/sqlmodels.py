"""Module for SQLmodels."""

from datetime import date
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlmodel import DATE
from sqlmodel import DATETIME
from sqlmodel import JSON
from sqlmodel import Field
from sqlmodel import SQLModel
from sqlmodel import String
from sqlmodel import text


# NOTE: The description field does not write into DuckDB; it's just for documentation purposes in this python file.
class DuckDBmodels:
    """SQLmodels implementation for writing to DuckDB."""

    def __init__(self, schema_name: str) -> None:
        """Initialize DuckDBmodels with the specified schema name.

        Args:
            schema_name (str): The name of the schema to use for the DuckDB tables.
        """
        self.schema_name = schema_name

    def project_metadata_record(self) -> type[SQLModel]:
        """Create a ProjectMetadata table class with the specified schema.

        Returns:
            type[SQLModel]: The ProjectMetadata class with the specified schema.
        """

        class ProjectMetadata(SQLModel, table=True):
            """Project metadata table model."""

            __tablename__ = 'project_metadata'
            __table_args__ = {'schema': self.schema_name}

            ticket_number: str = Field(
                default='', sa_column=Column(String, nullable=False, unique=True), description='Unique ticket number'
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
                default=datetime.today(),
                sa_column=Column(DATETIME, nullable=False),
                description='Timestamp when the log was last modified',
            )

        return ProjectMetadata

    def checklist(self) -> type[SQLModel]:
        """Create a Checklist table class with the specified schema.

        Returns:
            type[SQLModel]: The Checklist class with the specified schema.
        """

        class Checklist(SQLModel, table=True):
            """Checklist table model."""

            __tablename__ = 'checklist'
            __table_args__ = {'schema': self.schema_name}

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
            information_location: str = Field(
                sa_column=Column(String, nullable=True), description='Location of information'
            )
            check_type: str = Field(sa_column=Column(String, nullable=True), description='Type of check')

        return Checklist

    def check_results(self) -> type[SQLModel]:
        """Check the result list for the specified schema.

        Returns:
            type[SQLModel]: The CheckResult class with the specified schema.
        """

        class CheckResult(SQLModel, table=True):
            """Check result list table model."""

            __tablename__ = 'check_results'
            __table_args__ = {'schema': self.schema_name, 'extend_existing': True}

            check_name: str = Field(sa_column=Column(String, nullable=False), description='Name of the check')
            check_id: str = Field(
                sa_column=Column(String, nullable=False, primary_key=True), description='ID of the check'
            )
            description: str = Field(sa_column=Column(String, nullable=False), description='Description of the check')
            result_name: str = Field(sa_column=Column(String, nullable=False), description='Name of the result')
            results: list[str] | list[dict] = Field(
                sa_column=Column(JSON, nullable=False), description='(Nested) List of check results'
            )  # This support writing a list[str] and list[dict] to duckdb # noqa
            last_modified_datetime: datetime = Field(
                default=datetime.today(),
                sa_column=Column(DATETIME, nullable=False),
                description='Last modified datetime',
            )

        return CheckResult
