"""The module for writing checklist results to the database."""

from pydatacuration.db.base import DatabaseBackend


class CheckResultWriter:
    """Write checklist results to the database."""

    def __init__(self, db_instance: DatabaseBackend) -> None:
        """Initialize the ChecklistResultWriter with a database instance."""
        self.db_instance = db_instance
        self.checklist_model = self.db_instance.models.check_results()

    def write(
        self,
        *,
        check_id: str,
        check_name: str,
        description: str,
        unit: str,
        results: list[str] | list[dict] | None,
    ) -> None:
        """Write the result to the database.

        Args:
        check_id (str): The unique identifier for the checklist item.
        check_name (str): The name of the checklist item.
        description (str): A description of the checklist item.
        unit (str): The unit of measurement for the checklist results.
        results (list[str] | list[dict] | None): The results of the checklist item, which can be a list of strings, a list of dictionaries, or None.

        """  # noqa: E501
        record = self.checklist_model(
            check_id=check_id,
            check_name=check_name,
            description=description,
            unit=unit,
            results=results or [],
        )
        self.db_instance.merge_records_to_table(record)
