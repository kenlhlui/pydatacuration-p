# Documentation Site

The docs are built with [Zensical](https://zensical.org/) from the Markdown files in `docs/`, using the settings in [`zensical.toml`]({{ repo_blob }}/zensical.toml). The [docs workflow]({{ repo_blob }}/.github/workflows/docs.yml) deploys them to GitHub Pages on every push to `main`.

To preview locally:

```sh
uv run zensical serve
```

Then open <http://localhost:8000>.

---

## Generated Settings Tables

The settings tables on [App settings](../app_settings/README.md) and [Custom status options](../custom_status_options/README.md) are generated from the Pydantic models at build time, not written by hand.

### Why

The hand-written tables had drifted from the code. They listed a `DEBUG` setting that didn't exist and were missing `APP_RELOAD` and `APP_RECONNECT_TIMEOUT`. Because `AppSettings` ignores unknown variables (`extra='ignore'`), setting `DEBUG=true` had no effect and raised no error. A generated table can't drift.

Options considered:

| Option | Outcome |
|---|---|
| [mkdocstrings](https://mkdocstrings.github.io/) + [griffe-pydantic](https://mkdocstrings.github.io/griffe-pydantic/), with a custom template | **Chosen.** Standard tooling, supported by Zensical, little custom code. |
| mkdocstrings with its default layout | Rejected. It renders API reference docs: a field summary list, a code-styled heading and a `pydantic-field` badge for every field, too noisy for a settings page. |
| A pytest check comparing each doc to `model_fields` | Rejected. It catches drift, but the tables still have to be edited by hand. |
| The macros plugin, building the table in Python | Not needed. It gives full control over the format (for example, uppercase variable names), but it's more custom code to maintain. |

### How It Works

- `mkdocstrings-python` and `griffe-pydantic` are in the `dev` dependency group. The docs workflow runs `uv run`, which installs that group.
- griffe-pydantic reads each field's default and `description=` from `Field(...)` by parsing the source. It doesn't import or run the app.
- [`docs_templates/python/material/pydantic_model.html.jinja`]({{ repo_blob }}/docs_templates/python/material/pydantic_model.html.jinja) overrides griffe-pydantic's template. It renders the first paragraph of the class docstring, prefixed with **Description:**, then one table with **Name**, **Type**, **Default** and **Description** columns.
- The override drops griffe-pydantic's Config and Validators lists and the per-field headings. It applies to every Pydantic model rendered with `:::` on any page.
- `zensical.toml` points mkdocstrings at the override with `custom_templates = "docs_templates"`, and sets `show_source = false` and `show_bases = false`.
- The "Copy as Markdown" button outputs the table as a Markdown table.

### Adding or Changing a Setting

- Give every field a `description=` in `Field(...)`. It becomes the **Description** column; without one, the cell is empty.
- Keep the class docstring's first paragraph short. It appears as the **Description:** line above the table.
- To show a model on a page, add a line with its dotted path:

    ```markdown
    ::: pydatacuration.backend.models.app_settings.AppSettings
    ```

### Known Limitations

- Names are shown as the Python field names (`app_port`). The environment variable is the same name in uppercase (`APP_PORT`), which the App settings page explains.
- Fields inherited from a parent model, such as `main_dir` and `res_dir` from `DirectoryDefaults`, are listed first.
- Hand-written text around the tables, such as the `LOG_LEVEL` values and the example `.env`, can still drift.
- The override relies on the block names in griffe-pydantic's template (`docstring`, `config`, `fields`, `validators` and `children`). After upgrading griffe-pydantic, check that both pages still render a single table.

---

## Custom CSS

[`docs/stylesheets/extra.css`]({{ repo_blob }}/docs/stylesheets/extra.css) is loaded through `extra_css` in `zensical.toml`.

It styles the two GitHub callout types the theme doesn't style natively:

| Callout | Colour |
|---|---|
| `> [!IMPORTANT]` | Purple, as on GitHub |
| `> [!CAUTION]` | Red, as on GitHub |

The `pymdownx.quotes.callouts` extension turns GitHub callouts into admonitions. The theme styles `[!NOTE]`, `[!TIP]` and `[!WARNING]` itself. For the other two, the stylesheet sets the background, title colour and a [Lucide](https://lucide.dev/) icon, matching the icons the theme uses for the built-in types. This lets Markdown files use the same callouts on GitHub and on the docs site.
