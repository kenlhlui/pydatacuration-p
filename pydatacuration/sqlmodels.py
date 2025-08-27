"""Module for SQLmodels."""
from datetime import date

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Sequence
from sqlmodel import DATE
from sqlmodel import DATETIME
from sqlmodel import JSON
from sqlmodel import Field
from sqlmodel import SQLModel
from sqlmodel import String


class DuckDBmodels:
    def __init__(self, schema_name: str) -> None:
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

            id: int | None = Field(
                default=None,
                sa_column=Column(
                    Integer,
                    Sequence('project_metadata_id_seq'),
                    server_default=Sequence('project_metadata_id_seq').next_value(),
                    primary_key=True
                )
            )
            ticket_number: str = Field(sa_column=Column(String, nullable=False, unique=True))
            dataset_title: str = Field(sa_column=Column(String, nullable=False))
            dataset_pid: str = Field(sa_column=Column(String, nullable=False))
            dataset_id: str = Field(sa_column=Column(String, nullable=False))
            dataset_url: str = Field(sa_column=Column(String, nullable=False))
            dataset_path: str = Field(sa_column=Column(String, nullable=False))
            log_init_date: date = Field(sa_column=Column(DATE, nullable=False))
            log_last_update_date: date = Field(sa_column=Column(DATE, nullable=False))
            last_modified_datetime: date = Field(sa_column=Column(DATETIME, nullable=False))

        return ProjectMetadata

    def check_result_json(self, table_name: str) -> type[SQLModel]:
        """Check the result list for the specified schema.

        Returns:
            type[SQLModel]: The CheckResultjson class with the specified schema.
        """
        class CheckResultjson(SQLModel, table=True):
            """Check result list table model."""

            __tablename__ = table_name
            __table_args__ = {'schema': self.schema_name}

            id: int | None = Field(
                default=None,
                sa_column=Column(
                    Integer,
                    Sequence('check_result_list_id_seq'),
                    server_default=Sequence('check_result_list_id_seq').next_value(),
                    primary_key=True
                )
            )
            check_id: str = Field(sa_column=Column(String, nullable=False))
            description: str = Field(sa_column=Column(String, nullable=False))
            result_name: str = Field(sa_column=Column(String, nullable=False))
            results: list[str] | list[dict] = Field(sa_column=Column(JSON, nullable=False))  # This support writing a list[str] and list[dict] to duckdb # noqa
            last_modified_datetime: date = Field(sa_column=Column(DATETIME, nullable=False))

        return CheckResultjson