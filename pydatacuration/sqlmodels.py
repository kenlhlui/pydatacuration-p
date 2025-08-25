from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Sequence
from sqlalchemy import String
from sqlmodel import Field
from sqlmodel import SQLModel


def project_metadata_table(schema_name: str) -> type[SQLModel]:
    """Create a ProjectMetadata table class with the specified schema.

    Args:
        schema_name (str): The schema name to use for the table.

    Returns:
        type[SQLModel]: The ProjectMetadata class with the specified schema.
    """
    class ProjectMetadata(SQLModel, table=True):
        """Project metadata table model."""

        __tablename__ = 'project_metadata'
        __table_args__ = {'schema': schema_name}

        id: int | None = Field(
            default=None,
            sa_column=Column(
                Integer,
                Sequence('project_metadata_id_seq'),
                server_default=Sequence('project_metadata_id_seq').next_value(),
                primary_key=True
            )
        )
        name: str = Field(sa_column=Column(String, nullable=False))
        description: str = Field(sa_column=Column(String, nullable=False))
        created_at: str = Field(sa_column=Column(String, nullable=False))

    return ProjectMetadata