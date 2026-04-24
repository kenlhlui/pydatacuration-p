"""The module for writing checklist results to the database."""

from loguru import logger

from pydatacuration.db.base import DatabaseBackend


class ChecklistResultWriter:
    """Write checklist results to the database."""

    def __init__(self, db_instance: DatabaseBackend) -> None:
        """Initialize the ChecklistResultWriter with a database instance."""
        self.db_instance = db_instance
        self.checklist_model = self.db_instance.models.check_results()

    def write_results(self, check_result_list_obj) -> None:  # noqa: ANN001
        """Write the checklist results to the database."""
        try:
            self.db_instance.merge_records_to_table(check_result_list_obj)
        except Exception as e:
            check_id = check_result_list_obj.check_id
            logger.error(f'Failed to write {check_id} results to the database: {e}')
