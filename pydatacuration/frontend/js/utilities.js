/**
 * Utility Functions
 * Combines functionality from today.js and restformbutton.js
 * Provides common utility functions used across the application
 */

/**
 * Generate today's date in YYYY-MM-DD format
 * Originally from today.js
 * @returns {string} - Today's date in YYYY-MM-DD format
 */
function generateTodayDate() {
    const d = new Date();
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
}

/**
 * Reset a form and hide any error/success messages
 * Originally from restformbutton.js
 * @param {string} formId - The ID of the form to reset (defaults to 'setup-form')
 */
function resetForm(formId = 'setup-form') {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();
    }

    // Hide common message elements
    const errorMessage = document.getElementById('error-message');
    const successMessage = document.getElementById('success-message');

    if (errorMessage) {
        errorMessage.style.display = 'none';
    }
    if (successMessage) {
        successMessage.style.display = 'none';
    }
}

/**
 * Format a date object to YYYY-MM-DD string
 * @param {Date} date - The date object to format
 * @returns {string} - Formatted date string
 */
function formatDateToString(date) {
    if (!(date instanceof Date) || isNaN(date)) {
        return generateTodayDate(); // Fallback to today
    }

    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
}

/**
 * Parse a date string (YYYY-MM-DD) to Date object
 * @param {string} dateString - Date string in YYYY-MM-DD format
 * @returns {Date|null} - Date object or null if invalid
 */
function parseDateString(dateString) {
    if (!dateString || typeof dateString !== 'string') {
        return null;
    }

    const date = new Date(dateString + 'T00:00:00'); // Add time to avoid timezone issues
    return isNaN(date) ? null : date;
}

/**
 * Show a message element with optional auto-hide
 * @param {string} elementId - ID of the message element
 * @param {string} message - Message to display
 * @param {string} type - Message type ('error', 'success', 'info')
 * @param {number} autoHideMs - Auto-hide after milliseconds (0 = no auto-hide)
 */
function showMessage(elementId, message, type = 'info', autoHideMs = 0) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.textContent = message;
    element.style.display = 'block';

    // Apply styling based on type
    element.className = `message message-${type}`;

    // Auto-hide if specified
    if (autoHideMs > 0) {
        setTimeout(() => {
            element.style.display = 'none';
        }, autoHideMs);
    }
}

/**
 * Hide a message element
 * @param {string} elementId - ID of the message element
 */
function hideMessage(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

/**
 * Escape HTML characters to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} - HTML-escaped text
 */
function escapeHtml(text) {
    if (typeof text !== 'string') {
        return '';
    }

    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Debounce function - delays execution until after specified time has passed
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} - Debounced function
 */
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

/**
 * Throttle function - limits execution to once per specified time period
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} - Throttled function
 */
function throttle(func, limit) {
    let inThrottle;
    return function (...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions for global access
window.Utilities = {
    generateTodayDate,
    resetForm,
    formatDateToString,
    parseeDateString,
    showMessage,
    hideMessage,
    escapeHtml,
    debounce,
    throttle
};

// Also make individual functions available globally for backward compatibility
window.generateTodayDate = generateTodayDate;
window.resetForm = resetForm;