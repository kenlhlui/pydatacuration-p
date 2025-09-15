/**
 * DuckDB Update Module for Curation Log
 * Handles automatic writing of checklist updates to DuckDB database
 */

// Configuration
const DUCKDB_CONFIG = {
    updateEndpoint: '/update-checklist-item',
    debounceDelay: 1000, // 1 second delay to avoid too many requests
    debugMode: false
};

// Debounce timer for DuckDB updates
let duckdbDebounceTimer = null;

// Debug logging function
function duckdbDebugLog(message, data = null) {
    if (DUCKDB_CONFIG.debugMode) {
        console.log(`[DuckDB Update] ${message}`, data || '');
    }
}

/**
 * Update a single checklist item in DuckDB
 * @param {string} itemId - The checklist item ID
 * @param {string} status - The status value (P, F, TBD, NA)
 * @param {string} comments - The comments value
 * @param {string} timeSpent - The time spent value
 */
async function updateChecklistItemInDuckDB(itemId, status, comments, timeSpent) {
    const ticketNumber = sessionStorage.getItem('ticket_number');
    if (!ticketNumber) {
        duckdbDebugLog('No ticket number found, skipping DuckDB update');
        return;
    }
    
    try {
        duckdbDebugLog(`Updating item ${itemId} in DuckDB`, { status, comments, timeSpent });
        
        const response = await fetch(DUCKDB_CONFIG.updateEndpoint, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json' 
            },
            body: JSON.stringify({
                ticket_number: ticketNumber,
                item_id: itemId,
                status: status || null,
                comments: comments || null,
                time_spent: timeSpent || null
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            duckdbDebugLog(`Successfully updated item ${itemId} in DuckDB`);
        } else {
            console.warn(`Failed to update item ${itemId} in DuckDB:`, result.message);
        }
        
        return result;
    } catch (error) {
        console.error(`Error updating item ${itemId} in DuckDB:`, error);
        return { success: false, error: error.message };
    }
}

/**
 * Extract item ID from form field name
 * @param {string} fieldName - The form field name (e.g., "status-ABC123")
 * @returns {string|null} - The extracted item ID or null
 */
function extractItemIdFromFieldName(fieldName) {
    const match = fieldName.match(/^(status|comments|time)-(.+)$/);
    return match ? match[2] : null;
}

/**
 * Get current values for a checklist item
 * @param {string} itemId - The checklist item ID
 * @returns {object} - Object containing status, comments, and time values
 */
function getChecklistItemValues(itemId) {
    const statusField = document.querySelector(`[name="status-${itemId}"]`);
    const commentsField = document.querySelector(`[name="comments-${itemId}"]`);
    const timeField = document.querySelector(`[name="time-${itemId}"]`);
    
    return {
        status: statusField ? statusField.value : null,
        comments: commentsField ? commentsField.value : null,
        time: timeField ? timeField.value : null
    };
}

/**
 * Debounced update for DuckDB to avoid too many requests
 * @param {string} itemId - The checklist item ID
 */
function debouncedDuckDBUpdate(itemId) {
    clearTimeout(duckdbDebounceTimer);
    duckdbDebounceTimer = setTimeout(() => {
        const values = getChecklistItemValues(itemId);
        updateChecklistItemInDuckDB(itemId, values.status, values.comments, values.time);
        duckdbDebugLog(`Debounced DuckDB update triggered for item ${itemId}`);
    }, DUCKDB_CONFIG.debounceDelay);
}

/**
 * Handle form field changes and trigger DuckDB updates
 * @param {Event} event - The change/input event
 */
function handleFieldChangeForDuckDB(event) {
    const fieldName = event.target.name;
    const itemId = extractItemIdFromFieldName(fieldName);
    
    if (itemId) {
        duckdbDebugLog(`Field ${fieldName} changed, scheduling DuckDB update for item ${itemId}`);
        debouncedDuckDBUpdate(itemId);
    }
}

/**
 * Bulk update all checklist items to DuckDB
 * Useful for initial sync or manual refresh
 */
async function bulkUpdateChecklistToDuckDB() {
    const ticketNumber = sessionStorage.getItem('ticket_number');
    if (!ticketNumber) {
        console.warn('No ticket number found, cannot perform bulk update');
        return;
    }
    
    duckdbDebugLog('Starting bulk update to DuckDB');
    
    // Get all checklist item IDs from status fields
    const statusFields = document.querySelectorAll('[name^="status-"]');
    const updates = [];
    
    for (const field of statusFields) {
        const itemId = extractItemIdFromFieldName(field.name);
        if (itemId) {
            const values = getChecklistItemValues(itemId);
            updates.push(updateChecklistItemInDuckDB(itemId, values.status, values.comments, values.time));
        }
    }
    
    try {
        const results = await Promise.all(updates);
        const successful = results.filter(r => r && r.success).length;
        const failed = results.filter(r => r && !r.success).length;
        
        duckdbDebugLog(`Bulk update completed: ${successful} successful, ${failed} failed`);
        
        if (failed > 0) {
            console.warn(`${failed} DuckDB updates failed during bulk operation`);
        }
        
        return { successful, failed, total: results.length };
    } catch (error) {
        console.error('Error during bulk update to DuckDB:', error);
        return { successful: 0, failed: updates.length, total: updates.length };
    }
}

/**
 * Initialize DuckDB update functionality
 */
function initializeDuckDBUpdates() {
    duckdbDebugLog('Initializing DuckDB update functionality...');
    
    // Add event listeners for form changes
    const form = document.querySelector('form');
    if (form) {
        // Listen for changes on checklist-related fields
        form.addEventListener('change', function(event) {
            if (event.target.name && event.target.name.match(/^(status|comments|time)-.+$/)) {
                handleFieldChangeForDuckDB(event);
            }
        });
        
        // Also listen for input events on textarea and text inputs
        form.addEventListener('input', function(event) {
            if (event.target.name && event.target.name.match(/^(comments|time)-.+$/)) {
                handleFieldChangeForDuckDB(event);
            }
        });
        
        duckdbDebugLog('Added event listeners for DuckDB updates');
    }
    
    duckdbDebugLog('DuckDB update functionality initialized successfully');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDuckDBUpdates);
} else {
    initializeDuckDBUpdates();
}

// Export functions for global access
window.DuckDBUpdate = {
    updateItem: updateChecklistItemInDuckDB,
    bulkUpdate: bulkUpdateChecklistToDuckDB,
    setDebugMode: (enabled) => { DUCKDB_CONFIG.debugMode = enabled; },
    getItemValues: getChecklistItemValues
};