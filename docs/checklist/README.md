# Checklist YAML file

A checklist YAML should be place under the `res` directory.

## The YAML file structure
The checklist YAML file should have the following structure:
```yaml
---
checklist_metadata:
    name: "Checklist Name"
    version: "1.0"
    description: "A brief description of the checklist."
    created_by: "Author Name"
    last_updated: "2024-06-01" # YYYY-MM-DD format
    status: "active" # or "draft", "archived", etc.
checklist:
  - id: "1.1"
    action: "Has the depositor (or their research group) previously created or submitted to a dataverse collection ?"
    instructions: |
      - Confirm whether the listed dataverse collection refers to the same researcher/author
    priority: "info"
    section: "1. Structure of deposit"
    automated_check_ids: ["author_dataverse_history"]
    curator_check_item: "Author metadata, dataverse collection history"
    check_type: "Fully-automated"
  - id: "1.2"
    action: "Does the dataset have a clear and descriptive title ?"
    ...
```

Check the `pydatacuration/checklist/checklist_model.py` file for the full definition of the expected structure and data types for the checklist YAML file.


## Prerequisites
1. Ensure you have the dependencies installed:
   ```bash
    pip install -e .
    ```

## Validate the checklist YAML file
Run the following command, replacing `${CHECKLIST_FILE_PATH}` with the path to your checklist YAML file:

```bash
python -m pydatacuration.checklist.cli ${CHECKLIST_FILE_PATH}
```

or if you have `uv` installed:

```bash
uv run python -m pydatacuration.checklist.cli pydatacuration.checklist.cli ${CHECKLIST_FILE_PATH}
```