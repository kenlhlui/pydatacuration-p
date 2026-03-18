"""Models for validating checklist YAML files."""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator


class ChecklistYAMLItem(BaseModel):
    """Model for validating checklist items from YAML files."""

    model_config = ConfigDict(extra='forbid')

    id: str
    action: str
    instructions: str | None = None
    priority: str  # Could add Literal["required", "recommended", "info"]
    section: str
    automated_check_ids: list[str] | None = None
    tool_explanation: str | None = None
    curator_check_item: str | None = None
    check_type: str  # Could add Literal["Fully-automated", "Semi-automated", "Manual"]
    information: str | None = None  # This field exists in YAML but not in DB

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: str) -> str:
        allowed = ['required', 'recommended', 'info']
        if v not in allowed:
            raise ValueError(f'priority must be one of {allowed}')
        return v

    @field_validator('check_type')
    @classmethod
    def validate_check_type(cls, v: str) -> str:
        allowed = ['Fully-automated', 'Semi-automated', 'Manual']
        if v not in allowed:
            raise ValueError(f'check_type must be one of {allowed}')
        return v


class ChecklistYAML(BaseModel):
    """Model for validating the entire YAML file structure."""

    model_config = ConfigDict(extra='forbid')

    checklist: list[ChecklistYAMLItem]
