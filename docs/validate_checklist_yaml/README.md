# To validate a checklist YAML file

A checklist YAML should be place under the `res` directory.

You can check the checklist YAML file using the `ChecklistYAML` model defined in `pydatacuration.checklist.checklist_model`. This will ensure that the YAML file adheres to the expected structure and data types, and will raise validation errors if there are any issues with the file.

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