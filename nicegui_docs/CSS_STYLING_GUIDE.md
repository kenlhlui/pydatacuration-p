# Input Width Fix for NiceGUI

## Problem
By default, NiceGUI input fields don't automatically fill the full width of their container. They appear narrow.

## Solution
Apply **both** CSS classes and inline style to ensure full width:

```python
ui.input(
    placeholder='Your placeholder'
).classes('pdc-form-input w-full').bind_value(form_data, 'field_name').style('width: 100%')
```

## Breakdown

### 1. CSS Class: `pdc-form-input`
- Applies styling (padding, border, border-radius)
- Defined in `nicegui_styles.py`

### 2. Tailwind Class: `w-full`
- Tailwind utility class for `width: 100%`
- Works with Tailwind-based layouts

### 3. Inline Style: `.style('width: 100%')`
- Ensures 100% width regardless of parent container
- Overrides any NiceGUI defaults

## Standard Pattern

For all form inputs in your pages, use this pattern:

```python
with ui.element('div').classes('pdc-form-group'):
    # Label
    ui.label('Field Name *').classes('pdc-form-label')

    # Input with full width
    ui.input(
        placeholder='Placeholder text'
    ).classes('pdc-form-input w-full').bind_value(form_data, 'field_key').style('width: 100%')

    # Helper text
    ui.label('Helper text here').classes('pdc-form-helper')
```

## Different Input Types

### Text Input
```python
ui.input(
    placeholder='Enter text'
).classes('pdc-form-input w-full').bind_value(form_data, 'field').style('width: 100%')
```

### Password Input
```python
ui.input(
    placeholder='Enter password',
    password=True,
    password_toggle_button=True
).classes('pdc-form-input w-full').bind_value(form_data, 'password').style('width: 100%')
```

### Textarea
```python
ui.textarea(
    placeholder='Enter comments'
).classes('pdc-comments-input w-full').style('width: 100%')
```

### Select/Dropdown
```python
ui.select(
    options=['Option 1', 'Option 2'],
    label='Select option'
).classes('w-full').style('width: 100%')
```

## Why Three Declarations?

1. **`.classes('pdc-form-input')`** - Your custom styling (colors, padding, etc.)
2. **`.classes('w-full')`** - Tailwind utility for responsive width
3. **`.style('width: 100%')`** - Force override for NiceGUI's Quasar components

NiceGUI uses Quasar framework internally, which has its own width management. The inline style ensures our width takes precedence.

## CSS Added to nicegui_styles.py

The following CSS has been added to force full width:

```css
/* Form inputs */
.pdc-form-input {
    width: 100% !important;
    min-width: 100% !important;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    box-sizing: border-box;
}

/* NiceGUI Quasar overrides */
.pdc-form-input .q-field,
.pdc-form-input.q-field {
    width: 100% !important;
    min-width: 100% !important;
}

.pdc-form-group .q-field,
.pdc-form-group .q-input {
    width: 100% !important;
}
```

## Quick Reference Card

**Copy this pattern for all inputs:**

```python
# Standard input
ui.input(placeholder='...').classes('pdc-form-input w-full').bind_value(form_data, 'key').style('width: 100%')

# Textarea
ui.textarea(placeholder='...').classes('pdc-comments-input w-full').style('width: 100%')

# Select
ui.select(options=[...]).classes('w-full').style('width: 100%')
```

## Testing

After applying the fix:
1. Restart your NiceGUI app: `python nicegui_poc_styled.py`
2. Open http://localhost:8080
3. Input boxes should now fill the full width of their containers
4. Test on different screen sizes to ensure responsiveness

## If Inputs Are Still Narrow

Try adding to the parent container:

```python
with ui.element('div').classes('pdc-form-group').style('width: 100%'):
    # Your inputs here
```

Or wrap in a full-width column:

```python
with ui.column().classes('w-full'):
    with ui.element('div').classes('pdc-form-group'):
        # Your inputs here
```

---

*This fix has been applied to all inputs in `nicegui_poc_styled.py`*
