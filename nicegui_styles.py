"""
NiceGUI Styling Module for PyDataCuration
Replicates the exact look and feel from styles.css
"""

from nicegui import ui


# ============================================================================
# Complete CSS - Direct port from your styles.css
# ============================================================================

PYDATACURATION_CSS = """
<style>
/* ========================================================================
   Base Styles
   ======================================================================== */
body {
    font-family: Arial, sans-serif;
    margin: 20px;
    background-color: #f5f5f5;
    line-height: 1.6;
}

/* ========================================================================
   Container & Layout
   ======================================================================== */
.pdc-container {
    max-width: 1600px;
    width: 100%;
    margin: 0 auto;
    background-color: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    box-sizing: border-box;
}

.pdc-container > * {
    width: 100%;
    box-sizing: border-box;
}

.pdc-header {
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 15px;
    margin-bottom: 30px;
    font-size: 2rem;
    font-weight: bold;
}

/* ========================================================================
   Info Section (Metadata Display)
   ======================================================================== */
.pdc-info-section {
    background-color: #ecf0f1;
    padding: 25px;
    border-radius: 8px;
    margin-bottom: 30px;
}

.pdc-info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px 40px;
}

.pdc-info-item {
    display: flex;
    flex-direction: column;
    margin-bottom: 15px;
}

.pdc-info-item.full-width {
    grid-column: 1 / -1;
}

.pdc-info-label {
    font-weight: bold;
    margin-bottom: 8px;
    color: #34495e;
    font-size: 16px;
}

.pdc-info-value {
    padding: 10px 12px;
    border: 1.5px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    background-color: transparent;
    min-height: 20px;
}

.pdc-info-value input {
    transition: border-color 0.3s ease;
}

.pdc-info-value input:focus {
    outline: none;
    border-color: #3498db;
    box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

/* ========================================================================
   Status Legend
   ======================================================================== */
.pdc-status-legend {
    background-color: #fff3cd;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 30px;
    border-left: 4px solid #ffc107;
}

.pdc-status-legend h3 {
    margin-top: 0;
    color: #856404;
    font-size: 1.25rem;
}

.pdc-status-list {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
}

.pdc-status-item {
    font-size: 14px;
}

.pdc-status-code {
    font-weight: bold;
    color: #495057;
}

/* ========================================================================
   Status Select Colors
   ======================================================================== */
.status-select {
    width: 100%;
    min-width: 140px;
    padding: 3px;
    min-height: 1px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 12px;
    transition: background-color 0.3s ease;
}

.status-P,
.status-select.status-P,
select.status-P {
    background-color: #d4edda !important;
    color: #155724 !important;
    border-color: #c3e6cb !important;
}

.status-F,
.status-select.status-F,
select.status-F {
    background-color: #f8d7da !important;
    color: #721c24 !important;
    border-color: #f5c6cb !important;
}

.status-TBD,
.status-select.status-TBD,
select.status-TBD {
    background-color: #fff3cd !important;
    color: #856404 !important;
    border-color: #ffeaa7 !important;
}

.status-NA,
.status-select.status-NA,
select.status-NA {
    background-color: #e2e3e5 !important;
    color: #383d41 !important;
    border-color: #d6d8db !important;
}

/* ========================================================================
   Row Status Background Colors
   ======================================================================== */
tr.row-status-P {
    background-color: rgba(212, 237, 218, 0.3) !important;
}

tr.row-status-F {
    background-color: rgba(248, 215, 218, 0.3) !important;
}

tr.row-status-TBD {
    background-color: rgba(255, 243, 205, 0.3) !important;
}

tr.row-status-NA {
    background-color: rgba(226, 227, 229, 0.3) !important;
}

/* ========================================================================
   Checklist Table
   ======================================================================== */
.pdc-checklist-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 30px;
}

.pdc-checklist-table th,
.pdc-checklist-table td {
    border: 1px solid #ddd;
    padding: 12px;
    text-align: left;
    vertical-align: top;
}

.pdc-checklist-table th {
    background-color: #f8f9fa;
    font-weight: bold;
    position: sticky;
    top: 0;
    z-index: 10;
}

.pdc-section-header {
    background-color: #1E3765;
    color: white;
    font-weight: bold;
    text-align: center;
}

.pdc-item-id {
    font-weight: bold;
    width: 60px;
}

.pdc-action-item {
    width: 100%;
    font-weight: bold;
}

.pdc-instructions-header {
    font-size: 14px;
    margin: 8px 0 4px 0;
    padding: 0;
}

.pdc-instructions {
    width: 100%;
    font-size: 12px;
    color: #666;
}

/* ========================================================================
   Automated Check Results
   ======================================================================== */
.pdc-automated-check-cell {
    font-size: 12px;
}

.pdc-dynamic-check-results {
    max-height: 300px;
    overflow-y: scroll;
    overflow-x: hidden;
    background-color: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    padding: 10px;
    box-sizing: border-box;
    display: block;
    margin-bottom: 8px;
    min-height: 50px;
}

.pdc-check-result {
    min-height: 40px;
    margin-bottom: 8px;
    padding: 6px;
    border-left: 3px solid #00A189;
    background-color: #ffffff;
}

.pdc-static-info-location {
    margin-top: 0px;
    font-size: 12px;
    color: #000000;
    font-weight: 500;
    display: block;
}

.pdc-static-info-location:empty {
    display: none;
}

.pdc-check-details-list {
    margin: 8px 0 0 0;
    padding-left: 20px;
    list-style: decimal;
    font-size: 11px;
}

.pdc-check-details-list .result-item {
    margin-bottom: 4px;
    display: list-item;
}

.pdc-check-details-list .result-item code {
    color: #0D534D;
}

.pdc-check-description {
    color: #6C757D;
    font-style: italic;
    margin-top: 5px;
    font-size: 11px;
}

.pdc-information-location {
    background-color: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 4px;
    padding: 8px;
    margin-top: 10px;
    font-size: 12px;
    color: #495057;
    font-weight: 500;
}

.pdc-information-location p {
    margin: 0.25em 0;
    line-height: 1.3;
}

.pdc-information-location ul,
.pdc-information-location ol {
    margin: 0.25em 0;
    padding-left: 1.2em;
}

.pdc-information-location li {
    margin: 0.1em 0;
    line-height: 1.3;
}

/* ========================================================================
   Form Inputs
   ======================================================================== */
.pdc-comments-input {
    width: 100%;
    min-height: 80px;
    min-width: 400px;
    max-width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-family: Arial, sans-serif;
    font-size: 12px;
    white-space: pre-wrap;
    box-sizing: border-box;
    resize: vertical;
}

.pdc-time-input {
    width: 70px;
    padding: 8px 8px;
    min-height: 1px;
    border: 1px solid #ddd;
    border-radius: 1px;
    font-family: monospace;
}

.pdc-pre-filled {
    background-color: #e8f5e8;
    font-style: italic;
}

/* ========================================================================
   Priority Badges
   ======================================================================== */
.pdc-priority-badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: bold;
    color: white;
}

.pdc-priority-required {
    background-color: #dc4633;
}

.pdc-priority-recommended {
    background-color: #f1c500;
}

.pdc-priority-info {
    background-color: #6fc7ea;
}

.pdc-priority-badge-container {
    width: 100px;
    min-width: 100px;
    max-width: 100px;
}

/* ========================================================================
   Buttons
   ======================================================================== */
.pdc-actions {
    margin-top: 30px;
    text-align: center;
}

.pdc-btn {
    padding: 12px 25px;
    margin: 0 10px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s ease;
}

.pdc-btn-primary {
    background-color: #3498db;
    color: white;
}

.pdc-btn-secondary {
    background-color: #95a5a6;
    color: white;
}

.pdc-btn-calculate {
    background-color: #6D247A;
    color: white;
}

.pdc-btn-danger {
    background-color: #DC4633;
    color: white;
}

.pdc-btn:hover {
    opacity: 0.8;
    transform: translateY(-1px);
}

/* ========================================================================
   Checklist Selection Colors (for landing page)
   ======================================================================== */
.checklist-high,
select.checklist-high {
    border-color: #3498db !important;
    background-color: #ebf5fb !important;
}

.checklist-medium,
select.checklist-medium {
    border-color: #27ae60 !important;
    background-color: #e8f8f0 !important;
}

/* ========================================================================
   Logo
   ======================================================================== */
.pdc-logo {
    height: 60px !important;
    width: auto !important;
    display: block;
    margin: 8px;
    object-fit: contain;
}

/* ========================================================================
   Form Sections (Landing Page)
   ======================================================================== */
.pdc-form-section {
    background-color: #ecf0f1;
    padding: 15px;  /* Reduced from 20px */
    border-radius: 5px;
    margin-bottom: 15px;  /* Reduced from 20px */
    width: 100%;
    box-sizing: border-box;
}

.pdc-form-section h3 {
    margin-top: 0;
    margin-bottom: 12px;  /* Reduced from default */
    color: #2c3e50;
    font-size: 1.1rem;  /* Slightly smaller */
}

.pdc-form-group {
    margin-bottom: 12px;  /* Reduced from 20px */
    width: 100%;
    box-sizing: border-box;
}

.pdc-form-label {
    display: block;
    font-weight: bold;
    margin-bottom: 3px;  /* Reduced from 5px */
    color: #34495e;
}

.pdc-form-input {
    width: 100% !important;
    min-width: 100% !important;
    padding: 8px;  /* Reduced from 10px */
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    box-sizing: border-box;
    background-color: white !important;  /* Force white background */
}

.pdc-form-helper {
    color: #666;
    font-size: 12px;
    margin-top: 2px;  /* Reduced from 5px */
    display: block;
    line-height: 1.3;  /* Tighter line height */
}

/* ========================================================================
   Messages
   ======================================================================== */
.pdc-error {
    background-color: #e74c3c;
    color: white;
    padding: 10px;
    border-radius: 4px;
    margin-bottom: 20px;
}

.pdc-success {
    background-color: #27ae60;
    color: white;
    padding: 10px;
    border-radius: 4px;
    margin-bottom: 20px;
}

.pdc-info {
    background-color: #3498db;
    color: white;
    padding: 10px;
    border-radius: 4px;
    margin-bottom: 20px;
}

/* ========================================================================
   Loading Spinner
   ======================================================================== */
.pdc-loading {
    text-align: center;
    margin-top: 20px;
}

.pdc-loading-spinner {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid #f3f3f3;
    border-top: 3px solid #3498db;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* ========================================================================
   Responsive Design
   ======================================================================== */
@media (max-width: 768px) {
    .pdc-info-grid {
        grid-template-columns: 1fr;
        gap: 15px;
    }

    .pdc-container {
        padding: 20px;
        margin: 10px;
    }

    .pdc-comments-input {
        min-width: 100%;
    }
}

/* ========================================================================
   NiceGUI Specific Overrides
   ======================================================================== */
/* Override NiceGUI's default input widths */
.pdc-form-input .q-field,
.pdc-form-input.q-field {
    width: 100% !important;
    min-width: 100% !important;
}

.pdc-form-input .q-field__control,
.pdc-form-input.q-field .q-field__control {
    width: 100% !important;
    background-color: white !important;  /* Force white background */
}

.pdc-form-group .q-field,
.pdc-form-group .q-input {
    width: 100% !important;
}

/* Force white background on all input controls in form groups */
.pdc-form-group .q-field__control,
.pdc-form-group input,
.pdc-form-group textarea,
.pdc-form-group select {
    background-color: white !important;
    border: 1px solid #ddd !important;
    border-radius: 4px !important;
    box-shadow: none !important;  /* Remove inner shadow/border */
}

/* Reduce padding on Quasar fields */
.pdc-form-group .q-field__control {
    padding: 0 !important;
    min-height: 40px !important;  /* Slightly taller for better UX */
}

/* For text inputs only - not select dropdowns */
.pdc-form-group .q-input .q-field__control {
    height: 40px !important;  /* Fixed height only for text inputs */
}

.pdc-form-group .q-field__native {
    padding: 8px !important;
}

/* Remove bottom border line from Quasar inputs */
.pdc-form-group .q-field__control:before,
.pdc-form-group .q-field__control:after {
    display: none !important;  /* Remove the weird bottom line */
}

.pdc-form-group .q-field__bottom {
    display: none !important;  /* Hide hint/error area */
}

/* Remove inner border/shadow from Quasar components */
.pdc-form-group .q-field__control-container {
    border: none !important;
}

.pdc-form-group .q-field__marginal {
    height: auto !important;
}

/* Override NiceGUI's default card styling */
.q-card.pdc-card {
    background-color: #ecf0f1;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
}

/* Override NiceGUI's select styling for status */
.q-select.status-P .q-field__control {
    background-color: #d4edda !important;
    color: #155724 !important;
}

.q-select.status-F .q-field__control {
    background-color: #f8d7da !important;
    color: #721c24 !important;
}

.q-select.status-TBD .q-field__control {
    background-color: #fff3cd !important;
    color: #856404 !important;
}

.q-select.status-NA .q-field__control {
    background-color: #e2e3e5 !important;
    color: #383d41 !important;
}

/* Override NiceGUI input focus colors */
.q-field--focused .q-field__control {
    border-color: #3498db !important;
    box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2) !important;
}

/* ========================================================================
   Checklist Table Input Overrides - Compact Heights
   ======================================================================== */
/* Status select in table - force compact height */
.pdc-checklist-table .status-select.q-select .q-field__control {
    min-height: 28px !important;
    height: 28px !important;
    padding: 2px 8px !important;
    border: 1px solid #ddd !important;
    border-radius: 4px !important;
    box-shadow: none !important;
    box-sizing: border-box !important;
}

/* Remove Quasar's default border lines */
.pdc-checklist-table .status-select.q-select .q-field__control:before,
.pdc-checklist-table .status-select.q-select .q-field__control:after {
    display: none !important;
    border: none !important;
}

.pdc-checklist-table .status-select.q-select .q-field__native {
    padding: 0 !important;
    min-height: 24px !important;
    line-height: 24px !important;
    font-size: 12px !important;
}

.pdc-checklist-table .status-select.q-select .q-field__marginal {
    height: 28px !important;
}

.pdc-checklist-table .status-select.q-select .q-field__control-container {
    padding: 0 !important;
    min-height: 28px !important;
}

/* Time input in table - force compact height */
.pdc-checklist-table .pdc-time-input .q-field__control {
    min-height: 28px !important;
    height: 28px !important;
    padding: 0 !important;
    border: none !important;
    box-shadow: none !important;
}

/* Remove Quasar's default border lines */
.pdc-checklist-table .pdc-time-input .q-field__control:before,
.pdc-checklist-table .pdc-time-input .q-field__control:after {
    display: none !important;
    border: none !important;
}

.pdc-checklist-table .pdc-time-input .q-field__native,
.pdc-checklist-table .pdc-time-input input {
    padding: 2px 4px !important;
    min-height: 28px !important;
    height: 28px !important;
    line-height: 24px !important;
    font-size: 12px !important;
    border: 1px solid #ddd !important;
    border-radius: 4px !important;
    box-sizing: border-box !important;
}

.pdc-checklist-table .pdc-time-input .q-field__marginal {
    height: 28px !important;
}

.pdc-checklist-table .pdc-time-input .q-field__control-container {
    min-height: 28px !important;
    padding: 0 !important;
}

/* Remove extra padding from Quasar field wrapper */
.pdc-checklist-table .q-field__inner {
    padding: 0 !important;
}

.pdc-checklist-table .q-field__control-container {
    padding: 0 !important;
}

/* ========================================================================
   Project List Cards (Resume Work & Delete Project Pages)
   ======================================================================== */
.project-card {
    background-color: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.3s ease;
}

.project-card:hover {
    border-color: #3498db;
    box-shadow: 0 4px 12px rgba(52, 152, 219, 0.15);
    transform: translateY(-2px);
}

.project-card.clickable {
    cursor: pointer;
}

.project-card-info {
    flex-grow: 1;
}

.project-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.project-ticket {
    font-size: 1.2rem;
    font-weight: 600;
    color: #2c3e50;
}

.project-date {
    color: #7f8c8d;
    font-size: 0.9rem;
}

.project-info {
    color: #34495e;
    margin: 5px 0;
}

.project-badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.85rem;
    margin-right: 8px;
}

.badge-high {
    background-color: #e74c3c;
    color: white;
}

.badge-medium {
    background-color: #f39c12;
    color: white;
}

.no-projects {
    text-align: center;
    padding: 40px;
    color: #7f8c8d;
}

.warning-banner {
    background-color: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 20px;
}
</style>
"""


# ============================================================================
# Tailwind Class Mappings (for inline usage)
# ============================================================================


class PDCStyles:
    """Predefined style classes for PyDataCuration components"""

    # Container
    CONTAINER = 'w-full max-w-7xl mx-auto bg-white p-8 rounded-lg shadow-lg'

    # Header
    HEADER = 'text-3xl font-bold text-gray-800 border-b-2 border-blue-500 pb-4 mb-8'

    # Cards
    CARD_INFO = 'w-full bg-gray-100 p-6 rounded-lg mb-8'
    CARD_FORM = 'w-full bg-gray-100 p-5 rounded-md mb-5'
    CARD_LEGEND = 'w-full bg-yellow-50 p-5 rounded-lg mb-8 border-l-4 border-yellow-400'

    # Info Grid
    INFO_GRID = 'grid grid-cols-2 gap-3 gap-x-10'
    INFO_ITEM = 'flex flex-col mb-4'
    INFO_LABEL = 'font-bold mb-2 text-gray-700 text-base'
    INFO_VALUE = 'p-3 border border-gray-300 rounded bg-white text-sm min-h-5'

    # Form Elements
    FORM_GROUP = 'mb-5'
    FORM_LABEL = 'block font-bold mb-1 text-gray-700'
    FORM_INPUT = 'w-full p-2.5 border border-gray-300 rounded text-sm'
    FORM_HELPER = 'text-gray-600 text-xs mt-1'

    # Buttons
    BTN_PRIMARY = 'px-6 py-3 mx-2 bg-blue-500 text-white rounded cursor-pointer text-sm transition-all hover:opacity-80 hover:-translate-y-0.5'
    BTN_SECONDARY = 'px-6 py-3 mx-2 bg-gray-400 text-white rounded cursor-pointer text-sm transition-all hover:opacity-80 hover:-translate-y-0.5'
    BTN_CALCULATE = 'px-6 py-3 mx-2 bg-purple-700 text-white rounded cursor-pointer text-sm transition-all hover:opacity-80 hover:-translate-y-0.5'
    BTN_DANGER = 'px-6 py-3 mx-2 bg-red-600 text-white rounded cursor-pointer text-sm transition-all hover:opacity-80 hover:-translate-y-0.5'

    # Priority Badges
    PRIORITY_REQUIRED = 'inline-block px-2 py-1 rounded-xl text-xs font-bold text-white bg-red-600'
    PRIORITY_RECOMMENDED = 'inline-block px-2 py-1 rounded-xl text-xs font-bold text-white bg-yellow-500'
    PRIORITY_INFO = 'inline-block px-2 py-1 rounded-xl text-xs font-bold text-white bg-blue-400'

    # Status Classes (for programmatic application)
    STATUS_P = 'status-P'
    STATUS_F = 'status-F'
    STATUS_TBD = 'status-TBD'
    STATUS_NA = 'status-NA'

    # Checklist Selection
    CHECKLIST_HIGH = 'checklist-high'
    CHECKLIST_MEDIUM = 'checklist-medium'


# ============================================================================
# Helper Functions
# ============================================================================


def apply_pdc_styles():
    """Apply PyDataCuration CSS to the current page"""
    ui.add_head_html(PYDATACURATION_CSS)


def create_info_grid(metadata: dict, columns: list[tuple[str, str]]):
    """
    Create a standardized info grid matching your current design

    Args:
        metadata: Dictionary of metadata values
        columns: List of (key, label) tuples

    Returns:
        NiceGUI grid element
    """
    with ui.element('div').classes('pdc-info-section'):
        with ui.grid(columns=2).classes('pdc-info-grid'):
            for key, label in columns:
                with ui.element('div').classes('pdc-info-item'):
                    ui.label(label).classes('pdc-info-label')
                    ui.label(metadata.get(key, 'N/A')).classes('pdc-info-value')


def create_priority_badge(priority: str):
    """Create a priority badge with correct styling"""
    priority_map = {
        'required': ('Required', 'pdc-priority-required'),
        'recommended': ('Recommended', 'pdc-priority-recommended'),
        'info': ('Info', 'pdc-priority-info'),
    }

    text, css_class = priority_map.get(priority.lower(), (priority.title(), 'pdc-priority-info'))
    return ui.label(text).classes(f'pdc-priority-badge {css_class}')


def create_status_select(item_id: str, current_value: str = '', on_change=None):
    """Create a status select dropdown with proper styling.

    Args:
        item_id: Checklist item ID
        current_value: Current status value
        on_change: Callback function for value changes

    Returns:
        NiceGUI select element
    """
    select = ui.select(
        options={
            '': None,
            'P': 'In Progress',
            'F': 'Failed',
            'TBD': 'To Be Determined',
            'NA': 'Not Applicable',
        },
        value=current_value,
        with_input=False,
    ).classes('status-select')

    # Apply status-specific styling
    def update_status_style(value):
        select.classes(remove='status-P status-F status-TBD status-NA')
        if value:
            select.classes(add=f'status-{value}')

    # Initial styling
    if current_value:
        update_status_style(current_value)

    # Handle changes
    if on_change:
        select.on_value_change(lambda e: [update_status_style(e.value), on_change(e)])
    else:
        select.on_value_change(lambda e: update_status_style(e.value))

    return select


def create_checklist_select(current_value: str = 'high', on_change=None):
    """
    Create a checklist level select with proper styling

    Args:
        current_value: Current checklist level
        on_change: Callback function for value changes

    Returns:
        NiceGUI select element
    """
    # Create label outside the select
    ui.label('Select Checklist Level').classes('pdc-form-label')

    # Create select without internal label - display capitalized but use lowercase values
    select = (
        ui.select(options={'high': 'High', 'medium': 'Medium'}, value=current_value)
        .classes('w-full')
        .style('width: 100%')
    )

    # Apply checklist-specific styling
    def update_checklist_style(value):
        select.classes(remove='checklist-high checklist-medium')
        select.classes(add=f'checklist-{value}')

    # Initial styling
    update_checklist_style(current_value)

    # Handle changes
    if on_change:
        select.on_value_change(lambda e: [update_checklist_style(e.value), on_change(e)])
    else:
        select.on_value_change(lambda e: update_checklist_style(e.value))

    return select


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == '__main__':
    """Example usage of the styling module"""

    # Apply styles
    apply_pdc_styles()

    with ui.column().classes(PDCStyles.CONTAINER):
        ui.label('PyDataCuration Tool').classes(PDCStyles.HEADER)

        # Example info grid
        metadata = {'ticket_number': 'TICKET-123', 'curator_name': 'John Doe', 'dataset_title': 'Sample Dataset'}

        create_info_grid(
            metadata,
            [('ticket_number', 'Ticket Number'), ('curator_name', 'Curator Name'), ('dataset_title', 'Dataset Title')],
        )

        # Example status select
        with ui.row():
            ui.label('Status:')
            create_status_select('ABC-001', 'P')

        # Example priority badge
        with ui.row():
            ui.label('Priority:')
            create_priority_badge('required')

        # Example buttons
        with ui.row().classes('pdc-actions'):
            ui.button('Primary Action').classes(PDCStyles.BTN_PRIMARY)
            ui.button('Secondary').classes(PDCStyles.BTN_SECONDARY)
            ui.button('Calculate').classes(PDCStyles.BTN_CALCULATE)
            ui.button('Danger').classes(PDCStyles.BTN_DANGER)

    ui.run(title='PDC Styles Demo')
