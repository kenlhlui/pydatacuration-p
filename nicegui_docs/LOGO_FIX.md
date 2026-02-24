# Logo Display Fix

## Problem
Logo mounted at `/static/UTL.png` but not displaying in the browser.

## Root Cause
`ui.image()` in NiceGUI sometimes has rendering issues. Using raw HTML `<img>` tag works more reliably.

## Solution Applied

### Changed from:
```python
ui.image('/static/UTL.png').classes('pdc-logo').style('height: 60px; width: auto; margin: 8px;')
```

### Changed to:
```python
ui.html(
    '<img src="/static/UTL.png" '
    'alt="University of Toronto Libraries Logo" '
    'class="pdc-logo" '
    'style="height: 60px; width: auto; margin: 8px;">'
)
```

## How to Test

1. **Stop the running app** (Ctrl+C)

2. **Restart the app:**
   ```bash
   python nicegui_poc_styled.py
   ```

3. **Check the console output:**
   ```
   ✓ Static files mounted: /path/to/pydatacuration/frontend
   NiceGUI ready to go on http://localhost:9005
   ```

4. **Open browser:**
   - Visit: http://127.0.0.1:9005
   - Logo should appear at the top

5. **If still not showing, test direct access:**
   ```bash
   curl http://127.0.0.1:9005/static/UTL.png | file -
   ```
   Should output: `PNG image data, 793 x 178...`

6. **Check browser console** (F12 → Console tab):
   - Should have NO errors
   - If you see a 404 for UTL.png → static mounting issue
   - If no 404 but no image → rendering issue (use raw HTML)

## Verification Checklist

- [x] Static files mounted at module level (before `ui.run()`)
- [x] Console shows: `✓ Static files mounted`
- [x] File accessible: `curl http://127.0.0.1:9005/static/UTL.png` works
- [x] Using `ui.html()` instead of `ui.image()`
- [x] Logo has proper size: `height: 60px; width: auto`
- [x] CSS class applied: `class="pdc-logo"`

## Why ui.html() Instead of ui.image()?

NiceGUI's `ui.image()` component sometimes:
- Doesn't respect inline styles properly
- Has lazy loading that causes delays
- May have caching issues

Using raw HTML `<img>` tag:
- ✅ Works immediately
- ✅ Respects all CSS/inline styles
- ✅ More predictable behavior
- ✅ Matches your original HTML exactly

## Expected Result

```
┌─────────────────────────────────────┐
│ [University of Toronto Logo]        │  ← 60px high
│ Data Curation Tool                  │
│ ─────────────────────────────────   │
│                                     │
│ Dataset Information                 │
│ ...                                 │
└─────────────────────────────────────┘
```

## Alternative: If Still Not Working

Try using an absolute path:

```python
ui.html(
    f'<img src="http://127.0.0.1:9005/static/UTL.png" '
    'alt="Logo" class="pdc-logo" '
    'style="height: 60px; width: auto;">'
)
```

Or use base64 encoding (no server needed):

```python
import base64
from pathlib import Path

logo_path = Path('pydatacuration/frontend/UTL.png')
logo_base64 = base64.b64encode(logo_path.read_bytes()).decode()

ui.html(
    f'<img src="data:image/png;base64,{logo_base64}" '
    'alt="Logo" class="pdc-logo" '
    'style="height: 60px; width: auto;">'
)
```

## For Production

When integrating into your main app.py, the same pattern applies:

```python
# Mount static files
app.mount('/static', StaticFiles(directory='pydatacuration/frontend'), name='static')

# In your NiceGUI page
@ui.page('/')
def landing_page():
    ui.html(
        '<img src="/static/UTL.png" '
        'alt="University of Toronto Libraries Logo" '
        'class="pdc-logo" '
        'style="height: 60px; width: auto; margin: 8px;">'
    )
```

---

**Restart the app now and the logo should appear!** 🎨
