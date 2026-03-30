"""Priority options for checklist items in the frontend."""

from pydantic import BaseModel


class PriorityOptions(BaseModel):
    """Model for priority options."""

    Info: str = 'Info'
    Required: str = 'Required'
    Recommended: str = 'Recommended'
