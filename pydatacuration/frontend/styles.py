"""NiceGUI Styling Module for pydatacuration.

Replicates the exact look and feel from styles.css.
"""

from collections.abc import Callable

from nicegui import ui


# ============================================================================
# Complete CSS - Direct port from your styles.css
# ============================================================================

PYDATACURATION_CSS = """
<style>
/* ========================================================================
   Base Styles
   ======================================================================== */
* {
    box-sizing: border-box;
}

html {
    overflow-x: hidden;
    width: 100%;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans',
                 Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji';
    margin: 20px;
    background-color: #f6f8fa;
    color: #1f2328;
    line-height: 1.6;
    overflow-x: hidden;
    max-width: 100vw;
    box-sizing: border-box;
}

code, pre,
.pdc-time-input,
.pdc-check-details-list code {
    font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas,
                 'Liberation Mono', monospace;
}

/* ========================================================================
   Container & Layout
   ======================================================================== */
.pdc-container {
    max-width: 90%;
    width: 100%;
    min-width: 320px;
    margin: 0 auto;
    background-color: #ffffff;
    padding: 30px;
    border-radius: 6px;
    border: 1px solid #d0d7de;
    box-shadow: 0 1px 0 rgba(31, 35, 40, 0.04);
    box-sizing: border-box;
    overflow-x: auto;
}

.pdc-container > * {
    width: 100%;
    box-sizing: border-box;
}

.pdc-container-narrow {
    max-width: 50%;
    width: 100%;
    margin: 0 auto;
    background-color: #ffffff;
    padding: 30px;
    border-radius: 6px;
    border: 1px solid #d0d7de;
    box-shadow: 0 1px 0 rgba(31, 35, 40, 0.04);
    box-sizing: border-box;
    overflow-x: auto;
}

.pdc-container-narrow > * {
    width: 100%;
    box-sizing: border-box;
}

.pdc-header {
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 10px;
    font-size: 2rem;
    font-weight: 600;
}

/* ========================================================================
   Tab Panels — strip Quasar's default 16px padding so content aligns with
   the rest of pdc-container (specificity 0,2,0 beats Quasar's 0,1,0)
   ======================================================================== */
.pdc-container .q-tab-panel {
    padding: 0;
}

/* ========================================================================
   Info Section (Metadata Display)
   ======================================================================== */
.pdc-info-section {
    background-color: #f6f8fa;
    padding: 25px;
    border-radius: 6px;
    border: 1px solid #d0d7de;
    margin-bottom: 30px;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
}

.pdc-info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px 40px;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
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
   Checklist Table
   ======================================================================== */
.pdc-checklist-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 30px;
    table-layout: fixed;
}

/* Column widths: ID, Action Item, Info Location, Priority, Comments, Status, Time */
.pdc-checklist-table th:nth-child(1),
.pdc-checklist-table td:nth-child(1) { width: 3%; }

.pdc-checklist-table th:nth-child(2),
.pdc-checklist-table td:nth-child(2) { width: 25%; }

.pdc-checklist-table th:nth-child(3),
.pdc-checklist-table td:nth-child(3) { width: 25%; }

.pdc-checklist-table th:nth-child(4),
.pdc-checklist-table td:nth-child(4) { width: 8%; }

.pdc-checklist-table th:nth-child(5),
.pdc-checklist-table td:nth-child(5) { width: 25%; }

.pdc-checklist-table th:nth-child(6),
.pdc-checklist-table td:nth-child(6) { width: 10%; overflow: hidden; }

.pdc-checklist-table th:nth-child(7),
.pdc-checklist-table td:nth-child(7) { width: 5%; }

/* Prevent table from forcing horizontal scroll */
.pdc-checklist-table td,
.pdc-checklist-table th {
    overflow-wrap: break-word;
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

/* Clickable table rows (for resume work page) */
.pdc-checklist-table tbody tr.clickable-row {
    cursor: pointer;
    transition: background-color 0.2s ease;
}

.pdc-checklist-table tbody tr.clickable-row:hover {
    background-color: #ebf3fd;
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

.pdc-check-result-header {
    font-weight: bold;
    font-size: 12px;
}

.pdc-check-result {
    min-height: 40px;
    margin-bottom: 8px;
    padding: 6px;
    border-left: 3px solid #00A189;
    background-color: #ffffff;
}

.pdc-static-curator-check-item {
    margin-top: 0px;
    font-size: 12px;
    color: #000000;
    display: block;
}

.pdc-static-curator-check-item:empty {
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

/* ========================================================================
   Form Inputs — GitHub style
   ======================================================================== */
.pdc-comments-input {
    width: 100%;
    min-height: 80px;
    max-width: 100%;
    padding: 6px 12px;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    background-color: #ffffff;
    color: #1f2328;
    font-family: inherit;
    font-size: 12px;
    line-height: 20px;
    white-space: pre-wrap;
    box-sizing: border-box;
    resize: vertical;
    box-shadow: inset 0 1px 0 rgba(208, 215, 222, 0.2);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.pdc-comments-input:focus {
    outline: none;
    border-color: #0969da;
    box-shadow: 0 0 0 3px rgba(9, 105, 218, 0.3);
}

.pdc-time-input {
    width: 70px;
    font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace;
    font-size: 12px;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}


/* ========================================================================
   Priority Badges — GitHub Primer Label style
   ======================================================================== */
.pdc-badge {
    display: inline-block;
    padding: 0 8px;
    height: 20px;
    line-height: 18px;
    border-radius: 2em;
    font-size: 12px;
    font-weight: 500;
    white-space: nowrap;
    border: 1px solid transparent;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    box-sizing: border-box;
}

/* Required → Primer danger (red) */
.pdc-priority-required {
    background-color: #ffebe9;
    color: #cf222e;
    border-color: rgba(207, 34, 46, 0.4);
}

/* Recommended → Primer attention (yellow) */
.pdc-priority-recommended {
    background-color: #fff8c5;
    color: #9a6700;
    border-color: rgba(154, 103, 0, 0.4);
}

/* Info → Primer accent (blue) */
.pdc-priority-info {
    background-color: #ddf4ff;
    color: #0969da;
    border-color: rgba(9, 105, 218, 0.4);
}

.pdc-badge-container {
    overflow: hidden;
}

/* ========================================================================
   Check Type Badges — GitHub Primer Label style
   ======================================================================== */

/* Automated → solid blue */
.pdc-check-type-automated {
    background-color: #0969da;
    color: #ffffff;
    border-color: #0969da;
}

/* Manual → solid yellow/amber */
.pdc-check-type-manual {
    background-color: #9a6700;
    color: #ffffff;
    border-color: #9a6700;
}

/* Hybrid → solid orange */
.pdc-check-type-hybrid {
    background-color: #bc4c00;
    color: #ffffff;
    border-color: #bc4c00;
}

.pdc-check-type-automated,
.pdc-check-type-manual,
.pdc-check-type-hybrid {
    margin-bottom: 8px;
}

/* ========================================================================
   Buttons — GitHub Primer style
   ======================================================================== */
.pdc-actions {
    margin-top: 30px;
    text-align: center;
}

.pdc-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 5px 16px;
    margin: 0 6px;
    font-size: 14px;
    font-weight: 500;
    line-height: 20px;
    border-radius: 6px;
    border: 1px solid rgba(31, 35, 40, 0.15);
    cursor: pointer;
    white-space: nowrap;
    box-shadow: 0 1px 0 rgba(31, 35, 40, 0.04);
    transition: background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

/* Quasar overrides for pdc-btn — strip uppercase and normalise sizing */
.pdc-btn.q-btn {
    padding: 5px 16px;
    min-height: 32px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: normal;
    box-shadow: 0 1px 0 rgba(31, 35, 40, 0.04);
}

.pdc-btn .q-btn__content {
    text-transform: none;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: normal;
}

.pdc-btn.pdc-btn--lg.q-btn {
    font-size: 15px;
    padding: 8px 18px;
    min-height: 44px;
}

.pdc-btn.pdc-btn--lg .q-btn__content {
    font-size: 15px;
}

/* ========================================================================
   Form Sections (Landing Page)
   ======================================================================== */
.pdc-form-section {
    background-color: #f6f8fa;
    padding: 15px;
    border-radius: 6px;
    border: 1px solid #d0d7de;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
    margin-bottom: 20px;
}

.pdc-form-section-title {
    font-size: 18px;
    font-weight: 600; /* font-semibold */
    color: #374151; /* text-gray-700 */
    margin-bottom: 12px;
}

.pdc-form-group {
    margin-bottom: 12px;  /* Reduced from 20px */
    width: 100%;
    max-width: 100%;
}

.pdc-form-label {
    display: block;
    font-weight: bold;
    margin-bottom: 3px;  /* Reduced from 5px */
    color: #34495e;
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

========================================================================
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

/* pdc-input: compact GitHub-style input, applied directly to ui.input / ui.select */
.pdc-input.q-field,
.pdc-input.q-input {
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    padding-bottom: 0 !important;
    min-width: 0 !important;
}

.pdc-input .q-field__control {
    min-height: 28px !important;
    height: 28px !important;
    padding: 0 8px !important;
    background-color: #ffffff !important;
    border: 1px solid #d0d7de !important;
    border-radius: 6px !important;
    box-shadow: inset 0 1px 0 rgba(208, 215, 222, 0.2) !important;
    box-sizing: border-box !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    color: #1f2328 !important;
}

.pdc-input .q-field__control:focus-within {
    border-color: #0969da !important;
    box-shadow: 0 0 0 3px rgba(9, 105, 218, 0.3) !important;
}

.pdc-input .q-field__control:before,
.pdc-input .q-field__control:after {
    display: none !important;
}

.pdc-input .q-field__native {
    padding: 0 !important;
    min-height: 26px !important;
    height: 26px !important;
    line-height: 26px !important;
    font-size: 13px !important;
    color: #1f2328 !important;
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    box-sizing: border-box !important;
}

.pdc-input .q-field__marginal,
.pdc-input .q-field__control-container {
    height: 28px !important;
    min-height: 28px !important;
    padding: 0 !important;
    border: none !important;
    box-sizing: border-box !important;
}

.pdc-input .q-field__bottom {
    display: none !important;
}

/* pdc-form-group: layout/spacing only — no input styling */
.pdc-form-group .q-field,
.pdc-form-group .q-input {
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}

/* ========================================================================
   Checklist Table Input Overrides — GitHub style, compact heights
   ======================================================================== */

/* Shared GitHub input appearance for all table field controls */
.pdc-checklist-table .status-select.q-select .q-field__control,
.pdc-checklist-table .pdc-time-input .q-field__control {
    min-height: 28px !important;
    height: 28px !important;
    padding: 0 8px !important;
    border: 1px solid #d0d7de !important;
    border-radius: 6px !important;
    background-color: #ffffff !important;
    box-shadow: inset 0 1px 0 rgba(208, 215, 222, 0.2) !important;
    box-sizing: border-box !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

/* Focus state */
.pdc-checklist-table .status-select.q-select .q-field__control:focus-within,
.pdc-checklist-table .pdc-time-input .q-field__control:focus-within {
    border-color: #0969da !important;
    box-shadow: 0 0 0 3px rgba(9, 105, 218, 0.3) !important;
}

/* Remove Quasar's animated underline on both */
.pdc-checklist-table .status-select.q-select .q-field__control:before,
.pdc-checklist-table .status-select.q-select .q-field__control:after,
.pdc-checklist-table .pdc-time-input .q-field__control:before,
.pdc-checklist-table .pdc-time-input .q-field__control:after {
    display: none !important;
}

/* Status select */
.pdc-checklist-table .status-select {
    min-width: 0 !important;
    width: 100% !important;
}

.pdc-checklist-table .status-select.q-select .q-field__native {
    padding: 0 !important;
    min-height: 26px !important;
    line-height: 26px !important;
    font-size: 12px !important;
    color: #1f2328 !important;
}

.pdc-checklist-table .status-select.q-select .q-field__marginal,
.pdc-checklist-table .status-select.q-select .q-field__control-container {
    height: 28px !important;
    min-height: 28px !important;
    padding: 0 !important;
}

/* Time input */
.pdc-checklist-table .pdc-time-input .q-field__native,
.pdc-checklist-table .pdc-time-input input {
    padding: 0 !important;
    min-height: 26px !important;
    height: 26px !important;
    line-height: 26px !important;
    font-size: 12px !important;
    color: #1f2328 !important;
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    box-sizing: border-box !important;
}

.pdc-checklist-table .pdc-time-input .q-field__marginal,
.pdc-checklist-table .pdc-time-input .q-field__control-container {
    height: 28px !important;
    min-height: 28px !important;
    padding: 0 !important;
}

/* Remove extra padding from Quasar field wrapper */
.pdc-checklist-table .q-field__inner,
.pdc-checklist-table .q-field__control-container {
    padding: 0 !important;
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

.utl-logo {
    height: 60px;
    width: auto;
    margin: 8px 0;
    display: block;
}

.pdc-show-on-scroll {opacity: 0; visibility: hidden; transition: opacity .3s, visibility .3s}

.pdc-show-on-scroll.pdc-scrolling {opacity: 1; visibility: visible}


</style>
"""

MAIN_PAGE_HEAD_CSS: str = """
<style>
        /* Center everything on the page */
        .nicegui-content {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 100vh !important;
            padding: 20px !important;
        }
        .main-container {
            max-width: 1000px;
            width: 90%;
            background-color: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
            align-items: center;
        }
        .main-container > * {
            width: 100%;
        }
        body {
            background: #1E3765 !important;
            min-height: 100vh;
        }
        .option-card {
            background-color: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 35px;
            margin: 0;
            cursor: pointer;
            transition: all 0.3s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .option-card:hover {
            border-color: #3498db;
            background-color: #ebf3fd;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.2);
        }
        .option-title {
            font-size: 1.4rem;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 12px;
        }
        .option-description {
            color: #6c757d;
            font-size: 1rem;
        }
        .icon {
            font-size: 2.5rem;
            margin-bottom: 15px;
        }
        .options-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
            margin-bottom: 25px;
        }
        .resume-container {
            display: flex;
            justify-content: center;
            width: 100%;
            margin-top: 0;
        }
        .resume-card {
            width: 70%;
            max-width: 600px;
        }
        @media (max-width: 768px) {
            .options-grid {
                grid-template-columns: 1fr;
            }
            .resume-card {
                width: 100%;
            }
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


# ============================================================================
# Helper Functions
# ============================================================================


def apply_pdc_styles() -> None:
    """Apply PyDataCuration CSS to the current page and configure external links."""
    # Primer CSS — design tokens and components (no base reset to avoid Quasar conflicts)
    _PRIMER_CDN = 'https://unpkg.com/@primer/css@latest/dist'
    for module in ('primitives', 'buttons', 'forms', 'labels', 'navigation', 'utilities'):
        ui.add_head_html(f'<link rel="stylesheet" href="{_PRIMER_CDN}/{module}.css">')

    # Custom styles — loaded after Primer so .pdc-* rules take precedence
    ui.add_head_html(PYDATACURATION_CSS)

    # Add JavaScript to make all external links open in new tab
    ui.add_body_html("""
    <script>
        // Make all external links open in new tab with security attributes
        document.addEventListener('DOMContentLoaded', function() {
            function updateExternalLinks() {
                const links = document.querySelectorAll('a[href^="http"]');
                links.forEach(link => {
                    if (!link.hasAttribute('target')) {
                        link.setAttribute('target', '_blank');
                        link.setAttribute('rel', 'noopener noreferrer');
                    }
                });
            }

            // Run initially
            updateExternalLinks();

            // Re-run when content changes (for dynamically added content)
            const observer = new MutationObserver(updateExternalLinks);
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        });
    </script>
    """)


def create_info_grid(metadata: dict, columns: list[tuple[str, str]]) -> None:
    """Create a standardized info grid matching your current design.

    Args:
        metadata: Dictionary of metadata values
        columns: List of (key, label) tuples

    Returns:
        NiceGUI grid element
    """
    with ui.element('div').classes('pdc-info-section'), ui.grid(columns=2).classes('pdc-info-grid w-full'):
        for key, label in columns:
            with ui.element('div').classes('pdc-info-item'):
                ui.label(label).classes('pdc-info-label')
                ui.label(metadata.get(key, 'N/A')).classes('pdc-info-value')


def create_priority_badge(priority: str) -> ui.label:
    """Create a priority badge with correct styling.

    Args:
        priority: Priority value (Required, Recommended, Info)

    """
    priority_map = {
        'required': ('Required', 'pdc-priority-required'),
        'recommended': ('Recommended', 'pdc-priority-recommended'),
        'info': ('Info', 'pdc-priority-info'),
    }

    text, css_class = priority_map.get(priority.lower(), (priority.title(), 'pdc-priority-info'))
    return ui.label(text).classes(f'pdc-badge {css_class}')


def create_check_type_badge(check_type: str) -> ui.label:
    """Create a check type badge with correct styling.

    Args:
        check_type: Check type value (Fully-automated, Manual, Semi-automated)

    Returns:
        NiceGUI label element with appropriate styling
    """
    check_type_map = {
        'fully-automated': ('Automated Check', 'pdc-check-type-automated'),
        'manual': ('Manual Review', 'pdc-check-type-manual'),
        'semi-automated': ('Hybrid Check & Review', 'pdc-check-type-hybrid'),
    }

    text, css_class = check_type_map.get(check_type.lower(), (check_type.title(), 'pdc-check-type-manual'))
    return ui.label(text).classes(f'pdc-badge {css_class}')


def create_status_select(
    item_id: str,
    status_options: list,
    current_value: str | None = None,
    on_change: Callable | None = None,
    color_map: dict[str, str] | None = None,
):
    """Create a status select dropdown with proper styling.

    Args:
        item_id: Checklist item ID
        status_options: List of available status options
        current_value: Current status value
        on_change: Callback function for value changes
        color_map: Optional mapping of label → text_color

    Returns:
        NiceGUI select element
    """
    select = ui.select(
        options=status_options,
        value=current_value,
        with_input=False,
        clearable=True,
    ).classes('pdc-input')

    # Apply status-specific styling via inline styles
    def update_status_style(value: str) -> None:
        if color_map and value and value in color_map:
            select.style(f'color: {color_map[value]};')
        else:
            select.style('')

    # Initial styling
    if current_value:
        update_status_style(current_value)

    # Handle changes
    if on_change:
        select.on_value_change(lambda e: [update_status_style(e.value), on_change(e)])
    else:
        select.on_value_change(lambda e: update_status_style(e.value))

    return select


# ============================================================================
# Usage Example
# ============================================================================

# if __name__ == '__main__':
#     """Example usage of the styling module"""

#     # Apply styles
#     apply_pdc_styles()

#     with ui.column().classes(PDCStyles.CONTAINER):
#         ui.label('PyDataCuration Tool').classes(PDCStyles.HEADER)

#         # Example info grid
#         metadata = {'ticket_number': 'TICKET-123', 'curator_name': 'John Doe', 'dataset_title': 'Sample Dataset'}

#         create_info_grid(
#             metadata,
#             [('ticket_number', 'Ticket Number'), ('curator_name', 'Curator Name'), ('dataset_title', 'Dataset Title')],  # noqa: E501
#         )

#         # Example status select
#         with ui.row():
#             ui.label('Status:')
#             create_status_select('ABC-001', 'P')

#         # Example priority badge
#         with ui.row():
#             ui.label('Priority:')
#             create_priority_badge('required')

#         # Example buttons
#         with ui.row().classes('pdc-actions'):
#             ui.button('Primary Action').classes(PDCStyles.BTN_PRIMARY)
#             ui.button('Secondary').classes(PDCStyles.BTN_SECONDARY)
#             ui.button('Calculate').classes(PDCStyles.BTN_CALCULATE)
#             ui.button('Danger').classes(PDCStyles.BTN_DANGER)

#     ui.run(title='PDC Styles Demo')
