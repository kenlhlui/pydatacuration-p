from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Sequence
from sqlalchemy import String
from sqlmodel import Field
from sqlmodel import SQLModel
from sqlmodel import DATE


class DuckDBmodels:
    def __init__(self, schema_name: str) -> None:
        self.schema_name = schema_name

    def project_metadata_record(self) -> type[SQLModel]:
        """Create a ProjectMetadata table class with the specified schema.

        Args:
            schema_name (str): The schema name to use for the table.

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
            log_init_date: str = Field(sa_column=Column(DATE, nullable=False))
            log_last_update_date: str = Field(sa_column=Column(DATE, nullable=False))

        return ProjectMetadata
