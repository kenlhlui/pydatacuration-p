"""The service module for retrieving tree information of a dataset in the dataverse repository."""

from loguru import logger


def _process_tree(
    identifier_of_dataverse: str,
    data: dict,
    id_list: list,
    alias_list: list,
    name_list: list,
) -> dict:
    """Recursively search for a dataverse node and build its path.

    Args:
        identifier_of_dataverse (str): Target dataverse alias.
        data (dict): Current node data.
        id_list (list): Accumulated id path.
        alias_list (list): Accumulated alias path.
        name_list (list): Accumulated name path.

    Returns:
        dict: Result dict if found, otherwise empty dict.

    """
    current_id_list = id_list + [data.get('id')]
    current_alias_list = alias_list + [data.get('alias')]
    current_name_list = name_list + [data.get('name')]

    if data.get('alias') == identifier_of_dataverse:
        result = {
            'id': tuple(current_id_list),
            'alias': tuple(current_alias_list),
            'depth': data.get('depth'),
            'name': tuple(current_name_list),
            'path': '/'.join(current_name_list),
        }
        return result

    for child in data.get('children', []):
        result = _process_tree(
            identifier_of_dataverse,
            child,
            current_id_list,
            current_alias_list,
            current_name_list,
        )

        if result:
            return result

    return {}


def get_tree_info(identifier_of_dataverse: str, dv_tree: dict) -> dict:
    """Get the dataset tree information in the Dataverse repository.

    Args:
        identifier_of_dataverse(str): The identifier of the dataverse parent dataverse.
        dv_tree(dict): The JSON data containing the tree structure of the dataverse repository.

    Returns:
        dict: A dictionary containing the path to the target node, empty if none.
    """
    # Read the root node from the JSON once

    root = dv_tree.get('data', {}) if dv_tree.get('status') == 'OK' else {}
    result = _process_tree(identifier_of_dataverse, root, [], [], [])
    logger.debug(f'Tree info retrieved for dataverse "{identifier_of_dataverse}": {result}')
    return result
