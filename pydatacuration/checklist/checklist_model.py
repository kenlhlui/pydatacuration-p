"""Models for validating checklist YAML files."""

from datetime import date
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ChecklistMetadata(BaseModel):
    """The metadata for a checklist YAML file."""

    model_config = ConfigDict(extra='forbid')

    name: str = Field(..., description='The name of the checklist.')
    version: str = Field(..., description='The version of the checklist.')
    description: str | None = Field(None, description='A description of the checklist.')
    created_by: str | list[str] | None = Field(None, description='The person who created the checklist.')
    last_updated: date | None = Field(None, description='The date the checklist was last updated. (YYYY-MM-DD)')
    status: Literal['draft', 'active', 'deprecated'] = Field(
        ..., description='The status of the checklist, either draft, active, or deprecated.'
    )


class ChecklistYAMLItem(BaseModel):
    """The content of each checklist item in the YAML file."""

    model_config = ConfigDict(extra='forbid')

    id: str = Field(..., description='The unique identifier for the checklist item.')
    action: str = Field(..., description='The action to be taken for the checklist item.')
    instructions: str | None = Field(None, description='Instructions for completing the checklist item.')
    priority: Literal['required', 'recommended', 'info'] = Field(..., description='The priority of the checklist item.')
    section: str = Field(..., description='The section to which the checklist item belongs.')
    automated_check_ids: list[str] | None = Field(
        None, description='The IDs of automated checks associated with the checklist item.'
    )
    tool_explanation: str | None = Field(None, description='An explanation of the tool used for the checklist item.')
    curator_check_item: str | None = Field(None, description='The checklist item for curators to check.')
    check_type: Literal['Fully-automated', 'Semi-automated', 'Manual'] = Field(
        ..., description='The type of the checklist item.'
    )
    information: str | None = Field(None, description='Additional information about the checklist item.')


class ChecklistYAML(BaseModel):
    """Model for validating the entire YAML file structure."""

    model_config = ConfigDict(extra='forbid')

    checklist_metadata: ChecklistMetadata = Field(..., description='The metadata for the checklist.')

    checklist: list[ChecklistYAMLItem] = Field(..., description='The list of checklist items.')
