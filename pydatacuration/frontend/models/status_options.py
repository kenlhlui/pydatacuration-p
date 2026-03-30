"""Status options for checklist items in the frontend."""

from pydantic import BaseModel


class StatusOptions(BaseModel):
    """Model for the main directory."""

    P: str = 'Pass'
    F: str = 'Follow-up'
    TBD: str = 'To Be Determined'
    NA: str = 'Not Applicable'
