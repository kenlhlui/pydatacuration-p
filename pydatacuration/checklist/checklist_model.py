"""Models for validating checklist YAML files."""

from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict


class ChecklistYAMLItem(BaseModel):
    """Model for validating checklist items from YAML files."""

    model_config = ConfigDict(extra='forbid')

    id: str
    action: str
    instructions: str | None = None
    priority: Literal['required', 'recommended', 'info']
    section: str
    automated_check_ids: list[str] | None = None
    tool_explanation: str | None = None
    curator_check_item: str | None = None
    check_type: Literal['Fully-automated', 'Semi-automated', 'Manual']
    information: str | None = None  # This field exists in YAML but not in DB


class ChecklistYAML(BaseModel):
    """Model for validating the entire YAML file structure."""

    model_config = ConfigDict(extra='forbid')

    checklist: list[ChecklistYAMLItem]
