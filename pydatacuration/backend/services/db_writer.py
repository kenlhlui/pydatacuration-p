"""Database writer functions for writing metadata to the database."""

from loguru import logger

from pydatacuration.utils.utils import parse_dataset_url


# The below writes the to the database database
def write_project_metadata(db_instance, checker) -> None:
    """Write the project metadata to the database."""
    project_metadata_schema = db_instance.models.project_metadata_record()

    # Check if record already exists
    try:
        project_number = db_instance.schema_name
        curator_name: str | None = checker.curator_name
        curator_email: str | None = checker.curator_email
        dataset_title = checker.ds_title if checker.ds_title else 'No Title'
        dataset_pid = checker.ds_metadata.get('data', {}).get('latestVersion', {}).get('datasetPersistentId', 'No ID')
        datasetid = checker.ds_metadata.get('data', {}).get('latestVersion', {}).get('datasetId', 'No ID')
        dataset_url = parse_dataset_url(checker.base_url, dataset_pid)
        dataset_path = checker.check_ds_tree_info()

        db_instance.merge_records_to_table(
            project_metadata_schema(
                curator_name=curator_name,
                curator_email=curator_email,
                project_number=project_number,
                dataset_title=dataset_title,
                dataset_pid=dataset_pid,
                dataset_id=checker.dataset_id,
                datasetid=datasetid,
                dataset_url=dataset_url,
                dataset_path=dataset_path,
                checklist_type=checker.checklist_type,
            )
        )
    except Exception as e:
        logger.error(f'Failed to write to database: {e}')


def write_checklist_metadata(db_instance, body) -> None:
    pass


def write_checklist_items(db_instance, checklist) -> None:
    """Write the checklist items to database.

    Args:
        db_instance: The database instance to write to.
        checklist (ChecklistYAML): The checklist content to write.
    """
    try:
        checklist_schema = db_instance.models.checklist()

        for item in checklist.checklist:
            logger.debug(f'Writing checklist item to database: {item.id}')
            db_instance.merge_records_to_table(
                checklist_schema(
                    id=item.id,
                    action=item.action,
                    instructions=item.instructions,
                    priority=item.priority,
                    section=item.section,
                    automated_check_ids=item.automated_check_ids,
                    tool_explanation=item.tool_explanation,
                    curator_check_item=item.curator_check_item,
                    check_type=item.check_type,
                )
            )
    except Exception as e:
        logger.error(f'Failed to write checklist to database: {e}')
