"""Module to provide dataset tree information."""


class DatasetTreeInfo:
    """Class to provide dataset tree information."""

    def __init__(self, dv_tree: dict) -> None:
        """Initialize the DatasetTreeInfo class."""
        self.dv_tree = dv_tree

    # def get_dv_identifier(self) -> str | None:
    #     pass

    def get_ds_tree_info(self, identifier_of_dataverse: str) -> dict:
        """Get the dataset tree information in the Dataverse repository.

        Args:
            identifier_of_dataverse(str): The identifier of the dataverse parent dataverse.

        Returns:
            dict: A dictionary containing the path to the target node, empty if none.
        """

        def _process(data: dict, id_list: list, alias_list: list, name_list: list) -> dict:
            # Append the current node's alias and name to the respective lists
            # Create new lists with current node's information
            current_id_list = id_list + [data.get('id')]
            current_alias_list = alias_list + [data.get('alias')]
            current_name_list = name_list + [data.get('name')]

            # Check if the current node is the target
            if data.get('alias') == identifier_of_dataverse:
                result = {
                    'id': current_id_list,
                    'alias': current_alias_list,
                    'depth': data.get('depth'),
                    'name': current_name_list,
                }
                # Combine the paths with '/' separator
                result['path'] = '/'.join(current_name_list)
                # Turn the id, alias and name from list to tuple
                result['id'] = tuple(result['id'])
                result['alias'] = tuple(result['alias'])
                result['name'] = tuple(result['name'])
                return result

            # Recursively search through any children
            for child in data.get('children', []):
                result = _process(child, current_id_list, current_alias_list, current_name_list)
                if result:  # This is correct - if a non-empty result is returned from any child, pass it up
                    return result  # Return the result immediately when found

            # If we get here, no match was found in this branch
            return {}

        # Read the root node from the JSON once
        root = self.dv_tree.get('data', {}) if self.dv_tree.get('status') == 'OK' else {}
        result = _process(root, [], [], [])
        return result
