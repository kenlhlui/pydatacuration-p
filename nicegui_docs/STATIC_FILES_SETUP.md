# Static Files Setup for NiceGUI POC

## Problem
The logo image `/static/UTL.png` returns 404 because NiceGUI doesn't know where to find static files.

## Solution
The POC automatically mounts your existing `pydatacuration/frontend` directory as `/static`.

## How It Works

### Automatic Mounting (Already Configured)

The `nicegui_poc_styled.py` file includes this code:

```python
if __name__ in {'__main__', '__mp_main__'}:
    from nicegui import app as nicegui_app

    # Find your frontend directory
    static_path = Path('pydatacuration/frontend')
    if not static_path.exists():
        static_path = Path(__file__).parent / 'pydatacuration' / 'frontend'

    # Mount it at /static
    if static_path.exists():
        nicegui_app.add_static_files('/static', str(static_path))
        print(f'✓ Mounted static files from: {static_path.absolute()}')
```

### When You Run the App

```bash
python nicegui_poc_styled.py
```

You should see:
```
✓ Mounted static files from: /home/kenlhlui/github/pydatacuration-p/pydatacuration/frontend
```

## File Structure

Your existing structure:
```
pydatacuration/
├── frontend/
│   ├── UTL.png          ← Logo file
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   └── *.js files
│   ├── index.html
│   ├── landing.html
│   └── main.html
└── ...
```

Now accessible as:
- `/static/UTL.png` → Logo
- `/static/css/styles.css` → CSS (if needed)
- `/static/js/validation.js` → JS files (if needed)

## Verification

1. **Start the app:**
   ```bash
   python nicegui_poc_styled.py
   ```

2. **Check the console output:**
   - Should see: `✓ Mounted static files from: ...`
   - If you see `⚠ Warning: Static directory not found` → Path issue

3. **Test in browser:**
   - Go to: http://127.0.0.1:9005
   - Logo should display at the top
   - Check browser console (F12) for 404 errors

4. **Direct access test:**
   - Visit: http://127.0.0.1:9005/static/UTL.png
   - Should display the logo image directly

## Troubleshooting

### Logo Still Not Showing?

**Check 1: File exists**
```bash
ls -la pydatacuration/frontend/UTL.png
```
Should show the file (17KB size).

**Check 2: Run from correct directory**
```bash
# Make sure you're in the project root
pwd
# Should be: /home/kenlhlui/github/pydatacuration-p

python nicegui_poc_styled.py
```

**Check 3: Path in code**
The code uses `/static/UTL.png`:
```python
ui.image('/static/UTL.png').classes('pdc-logo')
```

**Check 4: Browser cache**
- Clear browser cache
- Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)

### Error: "Static directory not found"

If you see this warning, manually set the path:

```python
# At the top of nicegui_poc_styled.py, add:
STATIC_DIR = Path('/home/kenlhlui/github/pydatacuration-p/pydatacuration/frontend')

# Then in the main block, use:
nicegui_app.add_static_files('/static', str(STATIC_DIR))
```

## For Production Integration

When integrating into your main `app.py`:

```python
# app.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from nicegui import ui
from pathlib import Path

app = FastAPI()

# Mount static files for both FastAPI and NiceGUI
FRONTEND_DIR = Path(__file__).parent / 'pydatacuration' / 'frontend'
app.mount('/static', StaticFiles(directory=str(FRONTEND_DIR)), name='static')

# Your NiceGUI pages
@ui.page('/')
def landing_page():
    ui.image('/static/UTL.png')  # Works!
    # ... rest of page

# Run with NiceGUI
ui.run_with(app, storage_secret='your-secret')
```

## Alternative: Use Local Static Folder

If you want to keep POC files separate:

1. **Create a local static folder:**
   ```bash
   mkdir -p static
   cp pydatacuration/frontend/UTL.png static/
   ```

2. **Update the POC:**
   ```python
   static_path = Path('static')  # Use local folder
   ```

3. **Simpler for testing:**
   ```
   project/
   ├── nicegui_poc_styled.py
   ├── nicegui_styles.py
   └── static/
       └── UTL.png
   ```

## Summary

- ✅ POC automatically mounts `pydatacuration/frontend` as `/static`
- ✅ Logo accessible at `/static/UTL.png`
- ✅ All other frontend assets also available
- ✅ Works with your existing file structure
- ✅ No need to copy files

**Just run it and the logo should appear!**

---

*If you still see 404, check the terminal output when starting the app*
