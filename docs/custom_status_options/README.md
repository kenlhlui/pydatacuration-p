# Custom Status Options

The checklist supports user-defined status options via a configuration file. 

If no file is found, the following defaults are used automatically, as defined in the [`StatusOptions` model](pydatacuration/frontend/models/status_options.py):

| Key | Label |
|---|---|
| `Pass` | Pass |
| `Follow_up` | Follow-up |
| `TBD` | To Be Determined |
| `NA` | Not Applicable |

---

## Adding a Custom Configuration File

Place a file named `status_options.yaml` or `status_options.json` in the resources directory (`RES_DIR`).

When a file is present, it becomes the **complete source of truth** — the defaults above are ignored entirely.

---

## File Format

### YAML

```yaml
# status_options.yaml
Approved: Approved
Rejected: Rejected
Pending: Pending Review
```

### JSON

```json
{
  "Approved": "Approved",
  "Rejected": "Rejected",
  "Pending": "Pending Review"
}
```

The format is a flat key-value mapping where:
- **Key** — internal identifier (used in code/data)
- **Value** — display label shown in the UI dropdown

---

## Notes

- The file is loaded at startup. Restart the application after making changes.
- If the file is malformed or unreadable, the application logs an error and falls back to the defaults automatically.
- Only `.yaml`, `.yml`, and `.json` extensions are supported. Any other extension is ignored and defaults are used.
- There is no limit on the number of status options you can define.