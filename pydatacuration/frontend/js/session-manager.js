/**
 * Unified Session Storage Manager
 * Combines functionality from sessionstorage.js and readsessionstorage.js
 * Handles both ID-based and name-based field synchronization with sessionStorage
 */

// Configuration
const SESSION_CONFIG = {
    excludeFields: ['api_token'], // Fields to exclude from sessionStorage
    debugMode: false
};

// Debug logging function
function sessionDebugLog(message, data = null) {
    if (SESSION_CONFIG.debugMode) {
        console.log(`[Session Manager] ${message}`, data || '');
    }
}

/**
 * Initialize sessionStorage synchronization for ID-based fields
 * Handles fields with ID attributes (legacy sessionstorage.js functionality)
 */
function initializeIdBasedSync() {
    sessionDebugLog('Initializing ID-based session sync...');

    // Pick the fields with ID attributes, excluding specified fields
    const fields = Array.from(
        document.querySelectorAll('input[id], textarea[id], select[id]')
    ).filter((el) => !SESSION_CONFIG.excludeFields.includes(el.id));

    fields.forEach((el) => {
        // Use el.id as the sessionStorage key
        const key = el.id;

        // 1) Load from sessionStorage (if present)
        const stored = sessionStorage.getItem(key);
        if (stored !== null) {
            el.value = stored;
            el.classList.add('pre-filled');
            sessionDebugLog(`Loaded from session: ${key} = ${stored}`);
        } else if (el.value) {
            // 2) If nothing in storage but the field has a value (prepopulated), seed it
            sessionStorage.setItem(key, el.value);
            sessionDebugLog(`Seeded to session: ${key} = ${el.value}`);
        }

        // 3) Whenever user edits, keep storage up to date
        el.addEventListener('input', () => {
            sessionStorage.setItem(key, el.value);
            sessionDebugLog(`Updated session: ${key} = ${el.value}`);
        });

        // Handle SELECT elements
        if (el.tagName === 'SELECT') {
            el.addEventListener('change', () => {
                sessionStorage.setItem(key, el.value);
                sessionDebugLog(`Updated session (select): ${key} = ${el.value}`);
            });
        }
    });

    sessionDebugLog(`Initialized ID-based sync for ${fields.length} fields`);
}

/**
 * Initialize sessionStorage synchronization for name-based fields
 * Handles auto-populate fields with name attributes (readsessionstorage.js functionality)
 */
function initializeNameBasedSync() {
    sessionDebugLog('Initializing name-based session sync...');

    // Find every field with auto-populate class and name attribute
    const autoFields = document.querySelectorAll(
        'input.auto-populate[name], textarea.auto-populate[name], select.auto-populate[name]'
    );

    autoFields.forEach((el) => {
        const key = el.name;

        // 2) Load from sessionStorage (if present)
        const saved = sessionStorage.getItem(key);
        if (saved !== null) {
            el.value = saved;
            el.classList.add('pre-filled');
            sessionDebugLog(`Loaded auto-populate from session: ${key} = ${saved}`);
        }

        // 3) On user edit, write back to sessionStorage
        const save = () => {
            sessionStorage.setItem(key, el.value);
            sessionDebugLog(`Updated auto-populate session: ${key} = ${el.value}`);
        };

        el.addEventListener('input', save);
        if (el.tagName === 'SELECT') {
            el.addEventListener('change', save);
        }
    });

    sessionDebugLog(`Initialized name-based sync for ${autoFields.length} auto-populate fields`);
}

/**
 * Get a value from sessionStorage
 * @param {string} key - The key to retrieve
 * @returns {string|null} - The stored value or null if not found
 */
function getSessionValue(key) {
    const value = sessionStorage.getItem(key);
    sessionDebugLog(`Retrieved from session: ${key} = ${value}`);
    return value;
}

/**
 * Set a value in sessionStorage and update corresponding form fields
 * @param {string} key - The key to store
 * @param {string} value - The value to store
 * @param {boolean} updateFields - Whether to update form fields with this value
 */
function setSessionValue(key, value, updateFields = true) {
    sessionStorage.setItem(key, value);
    sessionDebugLog(`Stored to session: ${key} = ${value}`);

    if (updateFields) {
        // Update fields with matching ID
        const idField = document.getElementById(key);
        if (idField) {
            idField.value = value;
            idField.classList.add('pre-filled');
        }

        // Update fields with matching name
        const nameFields = document.querySelectorAll(`[name="${key}"]`);
        nameFields.forEach(field => {
            if (field.tagName === 'INPUT' || field.tagName === 'TEXTAREA' || field.tagName === 'SELECT') {
                field.value = value;
                field.classList.add('pre-filled');
            } else {
                // Handle display elements (span, div, etc.)
                field.textContent = value;
            }
        });
    }
}

/**
 * Clear a specific value from sessionStorage
 * @param {string} key - The key to remove
 */
function clearSessionValue(key) {
    sessionStorage.removeItem(key);
    sessionDebugLog(`Cleared from session: ${key}`);
}

/**
 * Clear all sessionStorage values
 * @param {boolean} confirm - Whether to show confirmation dialog
 */
function clearAllSessionData(confirm = true) {
    if (confirm && !window.confirm('Are you sure you want to clear all saved data?')) {
        return false;
    }

    sessionStorage.clear();
    sessionDebugLog('Cleared all session data');

    // Clear visual indicators
    document.querySelectorAll('.pre-filled').forEach(el => {
        el.classList.remove('pre-filled');
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT') {
            el.value = '';
        }
    });

    return true;
}

/**
 * Get all sessionStorage data as an object
 * @returns {object} - All sessionStorage key-value pairs
 */
function getAllSessionData() {
    const data = {};
    for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        data[key] = sessionStorage.getItem(key);
    }
    sessionDebugLog('Retrieved all session data', data);
    return data;
}

/**
 * Initialize the unified session manager
 */
function initializeSessionManager() {
    sessionDebugLog('Initializing unified session manager...');

    // Initialize both sync mechanisms
    initializeIdBasedSync();
    initializeNameBasedSync();

    sessionDebugLog('Session manager initialized successfully');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeSessionManager);
} else {
    initializeSessionManager();
}

// Export functions for global access
window.SessionManager = {
    getValue: getSessionValue,
    setValue: setSessionValue,
    clearValue: clearSessionValue,
    clearAll: clearAllSessionData,
    getAllData: getAllSessionData,
    setDebugMode: (enabled) => { SESSION_CONFIG.debugMode = enabled; },
    reinitialize: initializeSessionManager
};