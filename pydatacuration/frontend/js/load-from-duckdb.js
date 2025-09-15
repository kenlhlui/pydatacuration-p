/**
 * DuckDB Read Module for Curation Log
 * Loads saved checklist data from DuckDB on page refresh
 */

// Configuration
const DUCKDB_LOAD_CONFIG = {
    checklistEndpoint: '/api/checklist-data',
    debugMode: false
};

// Debug logging function
function duckdbLoadDebugLog(message, data = null) {
    if (DUCKDB_LOAD_CONFIG.debugMode) {
        console.log(`[DuckDB Load] ${message}`, data || '');
    }
}

/**
 * Load checklist data from DuckDB for the current ticket
 * @returns {Promise<object|null>} - Checklist data or null if failed
 */
async function loadChecklistDataFromDuckDB() {
    const ticketNumber = sessionStorage.getItem('ticket_number');
    if (!ticketNumber) {
        duckdbLoadDebugLog('No ticket number found in sessionStorage, skipping DuckDB load');
        return null;
    }

    try {
        duckdbLoadDebugLog(`Loading checklist data for ticket ${ticketNumber} from DuckDB`);

        const response = await fetch(`${DUCKDB_LOAD_CONFIG.checklistEndpoint}?ticket_number=${encodeURIComponent(ticketNumber)}`);

        if (!response.ok) {
            console.warn(`Failed to load checklist data from DuckDB: ${response.status} ${response.statusText}`);
            return null;
        }

        const data = await response.json();
        duckdbLoadDebugLog('Successfully loaded checklist data from DuckDB', data);

        return data;
    } catch (error) {
        console.error('Error loading checklist data from DuckDB:', error);
        return null;
    }
}

/**
 * Populate form fields with saved data from DuckDB
 * @param {object} checklistData - The checklist data from DuckDB
 */
function populateFormWithDuckDBData(checklistData) {
    if (!checklistData) {
        duckdbLoadDebugLog('No checklist data available to populate form');
        return;
    }

    let populatedCount = 0;

    // Populate curator information if available
    if (checklistData.curator_name) {
        const curatorNameField = document.querySelector('[name="curator_name"]');
        if (curatorNameField) {
            if (curatorNameField.tagName === 'INPUT' || curatorNameField.tagName === 'TEXTAREA') {
                curatorNameField.value = checklistData.curator_name;
            } else {
                curatorNameField.textContent = checklistData.curator_name;
            }
            curatorNameField.classList.add('pre-filled');
            // Also store in sessionStorage for consistency
            sessionStorage.setItem('curator_name', checklistData.curator_name);
            populatedCount++;
        }
    }

    if (checklistData.curator_email) {
        const curatorEmailField = document.querySelector('[name="curator_email"]');
        if (curatorEmailField) {
            if (curatorEmailField.tagName === 'INPUT' || curatorEmailField.tagName === 'TEXTAREA') {
                curatorEmailField.value = checklistData.curator_email;
            } else {
                curatorEmailField.textContent = checklistData.curator_email;
            }
            curatorEmailField.classList.add('pre-filled');
            // Also store in sessionStorage for consistency
            sessionStorage.setItem('curator_email', checklistData.curator_email);
            populatedCount++;
        }
    }

    // Populate log dates if available
    if (checklistData.log_init_date) {
        const logInitDateField = document.querySelector('[name="log_initial_date"]');
        if (logInitDateField) {
            if (logInitDateField.tagName === 'INPUT' || logInitDateField.tagName === 'TEXTAREA') {
                logInitDateField.value = checklistData.log_init_date;
            } else {
                logInitDateField.textContent = checklistData.log_init_date;
            }
            logInitDateField.classList.add('pre-filled');
            sessionStorage.setItem('log_generated_date', checklistData.log_init_date);
            populatedCount++;
        }
    }

    if (checklistData.log_last_update_date) {
        const logUpdatedDateField = document.querySelector('[name="log_updated_date"]');
        if (logUpdatedDateField) {
            if (logUpdatedDateField.tagName === 'INPUT' || logUpdatedDateField.tagName === 'TEXTAREA') {
                logUpdatedDateField.value = checklistData.log_last_update_date;
            } else {
                logUpdatedDateField.textContent = checklistData.log_last_update_date;
            }
            logUpdatedDateField.classList.add('pre-filled');
            sessionStorage.setItem('log_updated_date', checklistData.log_last_update_date);
            populatedCount++;
        }
    }

    // Populate checklist items if available
    if (!checklistData.checklist) {
        duckdbLoadDebugLog('No checklist items available to populate form');
        return;
    }

    const checklist = checklistData.checklist;

    checklist.forEach(item => {
        if (!item.id) return;

        // Update status field
        if (item.status) {
            const statusField = document.querySelector(`select[name="status-${item.id}"]`);
            if (statusField) {
                statusField.value = item.status;
                statusField.classList.add('pre-filled');
                // Trigger change event to ensure any listeners are notified
                statusField.dispatchEvent(new Event('change', { bubbles: true }));
                populatedCount++;
            }
        }

        // Update comments field
        if (item.comments) {
            const commentsField = document.querySelector(`textarea[name="comments-${item.id}"]`);
            if (commentsField) {
                commentsField.value = item.comments;
                commentsField.classList.add('pre-filled');
                // Trigger input event to ensure any listeners are notified
                commentsField.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }

        // Update time spent field
        if (item.time_spent) {
            const timeField = document.querySelector(`input[name="time-${item.id}"]`);
            if (timeField) {
                timeField.value = item.time_spent;
                timeField.classList.add('pre-filled');
                // Trigger input event to ensure any listeners are notified
                timeField.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    });

    duckdbLoadDebugLog(`Populated ${populatedCount} form fields with DuckDB data`);
}

/**
 * Initialize loading data from DuckDB
 * This will be called after the DOM is ready
 */
async function initializeDuckDBDataLoad() {
    duckdbLoadDebugLog('Initializing DuckDB data load...');

    // Wait a moment to ensure other scripts have initialized
    await new Promise(resolve => setTimeout(resolve, 100));

    try {
        const checklistData = await loadChecklistDataFromDuckDB();

        if (checklistData) {
            populateFormWithDuckDBData(checklistData);
            duckdbLoadDebugLog('DuckDB data load completed successfully');
        } else {
            duckdbLoadDebugLog('No data loaded from DuckDB - this might be a fresh session');
        }
    } catch (error) {
        console.error('Error during DuckDB data load initialization:', error);
    }
}

/**
 * Check if we should prioritize DuckDB data over sessionStorage
 * This happens when we have a ticket_number but haven't loaded from DuckDB yet
 */
function shouldLoadFromDuckDB() {
    const ticketNumber = sessionStorage.getItem('ticket_number');
    const hasLoadedFromDuckDB = sessionStorage.getItem('duckdb_loaded');

    // Load if we have a ticket number but haven't loaded from DuckDB yet
    return ticketNumber && !hasLoadedFromDuckDB;
}

/**
 * Mark that we've loaded data from DuckDB to prevent duplicate loads
 */
function markDuckDBLoaded() {
    sessionStorage.setItem('duckdb_loaded', 'true');
}

// Initialize when DOM is ready, but with higher priority than sessionStorage
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', async () => {
        if (shouldLoadFromDuckDB()) {
            await initializeDuckDBDataLoad();
            markDuckDBLoaded();
        }
    });
} else {
    if (shouldLoadFromDuckDB()) {
        initializeDuckDBDataLoad().then(() => {
            markDuckDBLoaded();
        });
    }
}

// Export functions for global access
window.DuckDBLoad = {
    loadData: loadChecklistDataFromDuckDB,
    populateForm: populateFormWithDuckDBData,
    setDebugMode: (enabled) => { DUCKDB_LOAD_CONFIG.debugMode = enabled; },
    forceLoad: async () => {
        await initializeDuckDBDataLoad();
        markDuckDBLoaded();
    }
};