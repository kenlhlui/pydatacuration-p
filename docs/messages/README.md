# Messages and Translations

All the text the app shows to users is in one file per language, in `pydatacuration/locales/`: [`en.yaml`]({{ repo_blob }}/pydatacuration/locales/en.yaml) for English. That covers page labels, buttons, notifications, form errors, error messages and automated check results. The code refers to each message by a key, such as `setup.form_reset`, and never contains the text itself.

- [For translators](#for-translators): changing the wording, or translating the file. No Python needed.
- [For developers](#for-developers): showing text, adding messages, showing errors, and the tests that keep the text in this file.

The `LOCALE` setting picks the file: `LOCALE=en`, the default, uses `en.yaml`. See [App Settings](../app_settings/README.md). Only English exists so far.

---

## How the File Is Organized

```yaml
setup:                                                 # section: the page or area
  form_reset: "Form reset to defaults"                 # key: "text"
  running: "Running curation process... ({elapsed}s)"  # {elapsed} is filled in by the app
projects:
  found:
    one: "Found {count} project"                       # used when the number is 1
    other: "Found {count} projects"                    # used for any other number, including 0
```

- **Key**: the path to a message, written with dots in the code, e.g. `setup.form_reset`. Keys never change, whatever the language.
- **Value**: the text users see.
- **Placeholder**: a name in braces, such as `{elapsed}`, that the app replaces with a value, e.g. `12`.
- **`one` and `other`**: two forms of a message that depends on a number.

| Section | Where the text appears |
|---|---|
| `common` | Text used on several pages, such as Cancel, Back and form field errors |
| `errors` | Error messages on the new dataset page and in API responses |
| `home` | Home page |
| `setup` | New dataset page |
| `projects` | Resume Project and Delete Project pages |
| `checklist` | Checklist page, including its notifications |
| `priority`, `check_type` | Badges in the checklist table |
| `checks` | Automated check results, one entry per check |

The app reads the file once, when it starts. Restart it to see your changes.

Log messages are not in this file. They stay in the code, in English, because they are read by the people running the app.

---

## For Translators

### Changing the English Wording

Edit the value in `en.yaml`, keeping the key and any placeholders, then restart the app. If you remove or rename a placeholder, the tests fail, because the code still fills in the old one.

### Translating into Another Language

1. **Copy `en.yaml`** to a file named with the language code, e.g. `pydatacuration/locales/fr.yaml`.
2. **Translate the values.** Leave the keys and the indentation as they are. You can translate the comments (lines starting with `#`) or leave them.
3. **Follow the rules below.**
4. **Check the file.** The tests compare it with `en.yaml` and list any missing keys and changed placeholders. Run them, or ask a developer to:
   ```sh
   uv run pytest tests/test_i18n.py
   ```
5. **See it in the app:** set `LOCALE=fr` in `.env`, using your file's name, and restart the app.

### Rules

- **Keep every key exactly as it is.** Only the text after the colon is translated.
- **Keep each placeholder, with the same name.** You can move it to wherever it belongs in your sentence:
  ```yaml
  # en.yaml
  timer_stopped: "Timer stopped for {item_id}: {time}"
  # fr.yaml
  timer_stopped: "Minuteur arrêté pour {item_id} : {time}"
  ```
- **Translate both `one` and `other`** for messages that have them.
- **Keep the double quotes around each value.** Without them, YAML reads some words, such as `No` and `Off`, as true or false.
- **Inside the text, use your language's quotation marks** (« », “ ”, „ “), not straight double quotes (`"`). Some messages go inside HTML attributes, where a straight double quote breaks the page. A few English values are wrapped in single quotes (`'…'`) because they contain straight double quotes; your translation can use double quotes like the rest.
- **Indent with spaces, never tabs.**
- **Don't add `*`, `_` or backticks around words.** Some messages are shown as Markdown, where these become bold, italics or code.
- **Adapt punctuation to your language.** For example, `"Title:"` can become `"Titre :"`.

### Things to Know

- **Placeholder values are not translated.** They are data, such as project numbers, file names or times.
- **`MM:SS`** (`checklist.time_placeholder`) is a format hint for a time field. Translate the letters if your language uses others, but keep the format.
- **`checks.<check>.unit`** is stored in the database with each result, not shown on screen.
- **`checks.depositor_history.entry`** is written into the results when the checks run, so existing projects keep the language they were created in.
- **`checklist.results_found`** is only shown for projects created by older versions of the app.
- **Emoji** at the start of some messages are optional.

### Plural Forms

The app uses `one` only when the number is exactly 1, and `other` for every other number, including 0. In languages where 0 takes the singular, such as French, make the `other` form read acceptably for 0 too, or ask a developer to add your language's rule. Languages with more than two plural forms, such as Polish or Arabic, aren't supported yet.

---

## For Developers

### Showing Text

```python
from pydatacuration.i18n import t

ui.notify(t('setup.form_reset'))
ui.notify(t('checklist.status_updated', item_id=item.id))
ui.label(t('projects.found', count=len(projects)))
```

- `t(key, **params)` returns the message with its placeholders filled in, in the language set by `LOCALE`. It raises `KeyError` if the key isn't in that language's file.
- Pass `count=` for messages with `one` and `other` forms. It picks the form and also fills in `{count}`.
- `has_message(key)` tells you whether a key exists. You only need it for keys built at run time, such as [check results](#check-results).

Both are in [`pydatacuration/i18n.py`]({{ repo_blob }}/pydatacuration/i18n.py).

### Adding or Changing a Message

1. **Add the message to `en.yaml`** under the section for its page, or under `common` if several pages use it. Name the key after what the message is for, not its wording: `setup.form_reset`, not `setup.form_reset_to_defaults`. Quote the value.
2. **Use it** with `t('section.key', ...)`, passing exactly the placeholders the message has. Write the key as a string literal, not a variable, so the tests can check it.
3. **Run the tests:**
   ```sh
   uv run pytest tests/test_i18n.py
   ```

When you remove the last use of a message, remove it from `en.yaml` too. The tests flag unused messages.

Keep markup out of messages, so translators only see words:

```python
ui.markdown(f'**{t("checklist.guidance")}**')                       # en.yaml has "Guidance", not "**Guidance**"
ui.html(f'<img alt="{escape(t("common.logo_alt"))}" ...>', sanitize=False)  # escape catalogue text put in HTML
```

Don't build sentences from pieces, such as `f'{count} {unit} found'`. Word order and plurals differ between languages, so add a whole message with placeholders instead.

### What the Tests Check

[`tests/test_i18n.py`]({{ repo_blob }}/tests/test_i18n.py) fails when:

| Problem | Test |
|---|---|
| The code uses a key that isn't in `en.yaml` | `test_literal_key_should_exist_in_catalogue` |
| A `t()` call passes different values from the message's placeholders | `test_literal_call_should_pass_exactly_the_placeholders_of_its_message` |
| A message in `en.yaml` isn't used anywhere | `test_every_catalogue_message_should_be_used` |
| UI text is written in the code instead of using `t()` | `test_ui_text_should_come_from_catalogue` |
| A check ID has no entry under `checks`, or an entry has no checker | `test_every_check_id_written_by_checkers_should_be_in_catalogue`, `test_every_check_in_catalogue_should_be_written_by_a_checker` |
| An error class's `message_key` isn't in `en.yaml` | `test_exception_message_key_should_exist_in_catalogue` |
| A value isn't text, or has a broken placeholder such as `{name` | `test_catalogue_message_should_be_text_or_plural_forms`, `test_catalogue_message_should_have_valid_placeholders` |

The UI text test scans `pydatacuration/frontend/` and `pydatacuration/backend/api.py`. It fails on a string or f-string containing letters passed to `ui.notify`, `ui.label`, `ui.markdown`, `ui.button`, `ui.tab`, `ui.checkbox`, `.tooltip`, the `label` or `placeholder` of `ui.input` and `ui.textarea`, `action_button`, `form_section`, `dropdown_menu`, `floating_menu`, `text_input_box`, or the `detail` of `HTTPException`. Text without letters, such as `'📁'` or `'--'`, is allowed.

It can't see text in `ui.html()`, in `.props()` (such as `aria-label`), or in lists and dicts that are shown later (such as table headers), so check those in review. If you use a new kind of element that shows text, add it to `UI_TEXT_CALLS` in the test.

### Showing Errors

Users see generic text from the catalogue plus a reference ID. The details go to the log under that ID:

```
Page: Something went wrong. Reference: 3f9a1c2e
Log:  ... | ERROR | Reference: 3f9a1c2e | RuntimeError: <details>
      Traceback (most recent call last):
        ...
```

When someone reports a reference, search the log for it. The log is `logs/debug.log` in the main working directory (`MAIN_DIR`):

```sh
grep -A20 "Reference: 3f9a1c2e" workdir/logs/debug.log
```

Errors users should understand are subclasses of `UserFacingError` in [`exceptions.py`]({{ repo_blob }}/pydatacuration/exceptions.py). Each one names its message with `message_key`. The text you pass when raising is for the log only, and keyword arguments fill in the message's placeholders:

```python
class DirectoryExistsError(UserFacingError):
    message_key = 'errors.project_exists'  # "Project {project_number} already exists. ..."

raise DirectoryExistsError(f'Directory {path} already exists.', project_number=body.project_number)
#                          log only                             fills {project_number}
```

Where an error reaches the user, call `describe_error(exc)`. It logs the error and its traceback under a new reference ID, and returns the text to show: the error's message, or `errors.unexpected` for any other exception. The new dataset page and `/api/run-curation` already do this. The API sets the HTTP status for each error type in `ERROR_STATUS_CODES` in [`api.py`]({{ repo_blob }}/pydatacuration/backend/api.py); other errors return 500.

To add an error users should understand:

1. Add a subclass of `UserFacingError` with a `message_key`.
2. Add the message under `errors` in `en.yaml`.
3. If the API should return something other than 500 for it, add it to `ERROR_STATUS_CODES`, before any parent class.

> [!IMPORTANT]
> - Never show `str(exc)` to users. It can contain server paths and other internal details.
> - Don't log the error before raising it. `describe_error` logs it once, under its reference.
> - Don't use `logger.exception()` or `logger.opt(exception=...)` on these paths. Loguru prints the values of local variables in tracebacks, and those can include API tokens. `describe_error` logs the traceback without them.

### Check Results

The text for each automated check is under `checks.<check_id>`:

```yaml
checks:
  readme_files:
    name: "File names for README"                        # heading
    description: "README files detected in the dataset"  # shown under the heading
    unit: "file"                                         # stored in the database with the results
    found:                                               # the count line
      one: "{count} file found"
      other: "{count} files found"
```

- **Checkers write only the ID and the results:** `self.check_result_writer.write(check_id='readme_files', results=files)`. The writer stores the name, description and unit from the catalogue alongside them.
- **The checklist page looks up** the name, description and count line by check ID. For IDs no longer in the catalogue, from projects created by older versions, it shows the stored name and description, and `checklist.results_found` for the count.
- **To add a check**, add its entry under `checks` with all four fields.
- **If you rename a check ID**, existing projects keep the old ID and show their stored text.

The unused-message test skips `checks`. Instead, the tests check that the IDs under `checks` match the `check_id=` values in `pydatacuration/checker/`, and that each entry has all four fields.

### What Isn't in the Catalogue

- Log messages.
- Errors meant for the people running the app, such as configuration errors and `SchemaVersionError`.
- Data: the checklist YAML files and status options in `RES_DIR`, the Word template, and values from Dataverse.
- The field names in check results that are dictionaries, such as `field`, `typo` and `context` in the spelling check.
- The app title, which comes from the `APP_TITLE` setting.

### Languages

The `LOCALE` setting in [`AppSettings`]({{ repo_blob }}/pydatacuration/backend/models/app_settings.py) picks the file, and defaults to `en`. The app refuses to start if there is no file for it, and lists the ones there are. At startup, `app.py` passes it to `set_locale()`, and from then on `t()` and `has_message()` read that file. There is no fallback to English, so a translation must have every key.

Each translation is checked against `en.yaml` by two tests, which are skipped until a translation exists:

| Problem | Test |
|---|---|
| A key is missing, or isn't in `en.yaml` | `test_translation_should_have_the_same_keys_as_english` |
| A message has different placeholders, or lost its `one`/`other` forms | `test_translation_should_have_the_same_placeholders_and_plural_forms_as_english` |

When you add a language, also check:

- **Its plural rule.** `t()` uses the English rule: `one` when the count is 1. French, for example, also uses the singular for 0.
- **NiceGUI's built-in text**, such as date pickers. It follows `ui.run(language=...)` in `app.py`, which isn't set, so it stays in US English.

Text stored in the database, which is each check's `unit` and the depositor history lines, stays in the language that was active when the checks ran.
