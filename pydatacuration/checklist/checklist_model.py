"""Models for validating checklist YAML files."""

from pydantic import BaseModel
from pydantic import field_validator


# from pydatacuration.db.sqlmodels import DuckDBmodels


# Checklist = DuckDBmodels.checklist


class ChecklistYAMLItem(BaseModel):
    """Model for validating checklist items from YAML files."""

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

    checklist: list[ChecklistYAMLItem]


# # Convert from YAML model to SQLModel when inserting to DB
# def yaml_item_to_db_checklist(yaml_item: ChecklistYAMLItem, schema_name: str) -> 'Checklist':
#     """Convert a validated YAML item to a Checklist SQLModel instance."""
#     ChecklistModel = DuckDBmodels(schema_name).checklist()
#     return ChecklistModel(
#         id=yaml_item.id,
#         action=yaml_item.action,
#         instructions=yaml_item.instructions,
#         priority=yaml_item.priority,
#         section=yaml_item.section,
#         automated_check_ids=yaml_item.automated_check_ids,
#         tool_explanation=yaml_item.tool_explanation,
#         curator_check_item=yaml_item.curator_check_item,
#         check_type=yaml_item.check_type,
#         # Runtime fields get default values or are set later
#         status=None,
#         comments=None,
#         time_spent=None,
#     )
