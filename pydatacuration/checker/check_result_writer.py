"""The module for writing checklist results to the database."""

from pydatacuration.db.base import DatabaseBackend
from pydatacuration.db.sqlmodels import CheckResult
from pydatacuration.i18n import t


class CheckResultWriter:
    """Write checklist results to the database."""

    def __init__(self, db_instance: DatabaseBackend) -> None:
        """Initialize the ChecklistResultWriter with a database instance."""
        self.db_instance = db_instance

    def write(self, *, check_id: str, results: list[str] | list[dict] | None) -> None:
        """Write the result to the database, with the check's name, description and unit from the catalogue.

        Args:
        check_id (str): The unique identifier for the check; its text is under checks.<check_id> in en.yaml.
        results (list[str] | list[dict] | None): The results of the checklist item, which can be a list of strings, a list of dictionaries, or None.

        """  # noqa: E501
        record = CheckResult(
            project_number=self.db_instance.project_number,
            check_id=check_id,
            check_name=t(f'checks.{check_id}.name'),
            description=t(f'checks.{check_id}.description'),
            unit=t(f'checks.{check_id}.unit'),
            results=results or [],
        )
        self.db_instance.merge_records_to_table(record)
