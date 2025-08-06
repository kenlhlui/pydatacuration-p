/**
 * YAML Auto-save Module for Curation Log
 * Handles automatic saving and loading of form data in YAML format
 * Organizes data by checklist item IDs with sub-items for status, comments, and time
 */

// Simple YAML stringify function with nested structure
function simpleYamlStringify(obj) {
    let yaml = '';
    
    // Sort keys to maintain consistent order
    const sortedKeys = Object.keys(obj).sort();
    
    for (const key of sortedKeys) {
        const value = obj[key];
        
        // Handle nested objects (checklist items)
        if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
            // Check if object has any properties
            const entries = Object.entries(value);
            if (entries.length === 0) {
                yaml += `${key}: {}\n`;
            } else {
                yaml += `${key}:\n`;
                for (const [subKey, subValue] of entries) {
                    const yamlSubValue = formatYamlValue(subValue, 2);
                    yaml += `  ${subKey}: ${yamlSubValue}\n`;
                }
            }
        } else {
            // Handle top-level simple values
            const yamlValue = formatYamlValue(value);
            yaml += `${key}: ${yamlValue}\n`;
        }
    }
    return yaml;
}

// Format value for YAML output
function formatYamlValue(value, indent = 0) {
    // Handle null, undefined, or empty values
    if (value === '' || value === null || value === undefined) {
        return 'null';
    }
    
    // Handle objects that shouldn't be stringified as [object Object]
    if (typeof value === 'object' && value !== null) {
        return JSON.stringify(value);
    }
    
    // Convert to string for processing
    const stringValue = String(value);
    
    const needsQuoting = stringValue.includes('\n') || 
                        stringValue.includes(':') || 
                        stringValue.includes('#') || 
                        stringValue.includes('"') || 
                        stringValue.includes("'") || 
                        stringValue.trim() !== stringValue ||
                        stringValue.includes('|') || 
                        stringValue.includes('>');
    
    if (needsQuoting) {
        if (stringValue.includes('\n')) {
            // Use literal block scalar for multiline
            const indentStr = ' '.repeat(indent);
            const lines = stringValue.split('\n');
            return `|\n${indentStr}  ${lines.join('\n' + indentStr + '  ')}`;
        } else {
            return `"${stringValue.replace(/"/g, '\\"')}"`;
        }
    }
    
    return stringValue;
}

// Simple YAML parse function with nested structure support
function simpleYamlParse(yamlString) {
    const obj = {};
    const lines = yamlString.split('\n');
    let currentKey = null;
    let currentObject = null;
    let inLiteralBlock = false;
    let literalContent = [];
    let literalIndent = 0;
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();
        
        // Skip empty lines and comments
        if (!trimmed || trimmed.startsWith('#')) {
            if (inLiteralBlock) {
                literalContent.push('');
            }
            continue;
        }
        
        // Handle literal block content
        if (inLiteralBlock) {
            const lineIndent = line.length - line.trimStart().length;
            if (lineIndent >= literalIndent && (line.trim() || literalContent.length > 0)) {
                literalContent.push(line.slice(literalIndent));
                continue;
            } else {
                // End of literal block
                if (currentObject && currentKey) {
                    currentObject[currentKey] = literalContent.join('\n').replace(/\n$/, '');
                }
                inLiteralBlock = false;
                literalContent = [];
                currentKey = null;
                // Process current line normally
            }
        }
        
        const colonIndex = line.indexOf(':');
        if (colonIndex === -1) continue;
        
        const fullKey = line.substring(0, colonIndex);
        const keyIndent = fullKey.length - fullKey.trimStart().length;
        const key = fullKey.trim();
        let value = line.substring(colonIndex + 1).trim();
        
        if (keyIndent === 0) {
            // Top-level key
            if (value === '') {
                // This is a parent key for nested object
                obj[key] = {};
                currentObject = obj[key];
            } else {
                // Simple top-level value
                obj[key] = parseYamlValue(value);
                currentObject = null;
            }
        } else if (keyIndent === 2 && currentObject) {
            // Nested key (checklist item property)
            if (value === '|') {
                // Start of literal block
                inLiteralBlock = true;
                currentKey = key;
                literalContent = [];
                literalIndent = keyIndent + 2;
            } else {
                currentObject[key] = parseYamlValue(value);
            }
        }
    }
    
    // Handle case where literal block is at end of file
    if (inLiteralBlock && currentObject && currentKey) {
        currentObject[currentKey] = literalContent.join('\n').replace(/\n$/, '');
    }
    
    return obj;
}

// Parse individual YAML values
function parseYamlValue(value) {
    if (value === 'null') {
        return '';
    }
    
    // Handle quoted strings
    if ((value.startsWith('"') && value.endsWith('"')) || 
        (value.startsWith("'") && value.endsWith("'"))) {
        return value.slice(1, -1).replace(/\\"/g, '"').replace(/\\'/g, "'");
    }
    
    return value;
}

// Extract checklist item ID from form field name
function extractItemId(fieldName) {
    const match = fieldName.match(/^(status|comments|time)-(.+)$/);
    return match ? match[2] : null;
}

// Get field type from form field name
function getFieldType(fieldName) {
    if (fieldName.startsWith('status-')) return 'status';
    if (fieldName.startsWith('comments-')) return 'comments';
    if (fieldName.startsWith('time-')) return 'time';
    return 'other';
}

// Configuration
const AUTOSAVE_CONFIG = {
    interval: 30000, // 30 seconds (backup only)
    debounceDelay: 500, // 0.5 seconds for immediate saves
    storageKey: 'curationLog',
    debugMode: false
};

// Debounce timer
let debounceTimer = null;

// Debug logging function
function debugLog(message, data = null) {
    if (AUTOSAVE_CONFIG.debugMode) {
        console.log(`[YAML AutoSave] ${message}`, data || '');
    }
}

// Debounced auto-save function
function debouncedAutoSave() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        autoSaveForm();
        debugLog('Debounced save triggered');
    }, AUTOSAVE_CONFIG.debounceDelay);
}

// Auto-save function with structured organization
function autoSaveForm() {
    try {
        const form = document.querySelector('form');
        if (!form) {
            debugLog('No form found for auto-save');
            return;
        }
        
        const formData = new FormData(form);
        const organizedData = organizeFormData(formData);
        
        debugLog('Organized data before YAML conversion:', organizedData);
        
        const yamlData = simpleYamlStringify(organizedData);
        
        debugLog('YAML data after conversion:', yamlData);
        
        sessionStorage.setItem(AUTOSAVE_CONFIG.storageKey, yamlData);
        debugLog('Form data auto-saved as structured YAML');
        
    } catch (error) {
        console.error('[YAML AutoSave] Error during auto-save:', error);
    }
}

// Organize form data by checklist item IDs
function organizeFormData(formData) {
  // tmpMap holds per-id objects until we've collected them all
    const tmpMap = {};
    const otherFields = {};
    
    for (const [key, value] of formData.entries()) {
        const rawId = extractItemId(key);
        if (rawId) {
            // This is a checklist item field
            const itemId = String(rawId);
            if (!tmpMap[itemId]) {
                tmpMap[itemId] = { id: itemId };
            }
            tmpMap[itemId][getFieldType(key)] = value || '';
        } else if (isMetadataField(key)) {
            // This is a metadata field - will be handled separately
            continue;
        } else {
            // This is some other field
            otherFields[key] = value || '';
        }
    }

    // now turn that into a sorted array
    const checklist = Object
        .keys(tmpMap)
        .sort()
        .map((id) => tmpMap[id]);

    // Collect metadata from .auto-populate fields
    const metadata = loadMetadataFields();

    return {
        metadata: metadata,
        checklist_items: checklist,
        other: otherFields
    };
}

// Get form field value with proper handling for different input types and display elements
function getFormFieldValue(fieldName) {
    const element = document.querySelector(`[name="${fieldName}"]`);
    if (!element) return '';
    
    // Handle display elements (span, div, etc.) - get text content
    if (element.tagName === 'SPAN' || element.tagName === 'DIV') {
        return element.textContent ? element.textContent.trim() : '';
    }
    
    if (element.type === 'radio') {
        const checkedRadio = document.querySelector(`[name="${fieldName}"]:checked`);
        return checkedRadio ? checkedRadio.value : '';
    } else if (element.type === 'checkbox') {
        return element.checked ? 'on' : '';
    } else {
        return element.value || '';
    }
}

// Check if a field name should be considered metadata
function isMetadataField(fieldName) {
    // Exclude form fields that are part of checklist items
    return !fieldName.match(/^(status|comments|time)-.+$/);
}

// Collect metadata from .auto-populate fields
function loadMetadataFields() {
    const metadata = {};
    const fields = document.querySelectorAll('.auto-populate');
    fields.forEach(field => {
        const fieldName = field.getAttribute('name');
        if (fieldName && isMetadataField(fieldName)) {
            const value = getFormFieldValue(fieldName);
            if (value) {
                metadata[fieldName] = value;
            }
        }
    });
    
    // Also load curator and ticket information from sessionStorage
    const curatorName = sessionStorage.getItem('curator_name');
    const curatorEmail = sessionStorage.getItem('curator_email');
    const ticketNumber = sessionStorage.getItem('ticket_number');
    
    if (curatorName) metadata['curator_name'] = curatorName;
    if (curatorEmail) metadata['curator_email'] = curatorEmail;
    if (ticketNumber) metadata['ticket_number'] = ticketNumber;
    
    return metadata;
}

// Load saved data function with structured format
function loadSavedData() {
    try {
        const savedData = sessionStorage.getItem(AUTOSAVE_CONFIG.storageKey);
        if (!savedData) {
            debugLog('No saved data found');
            return;
        }
        
        let data;
        
        // Try parsing as structured YAML first
        try {
            data = simpleYamlParse(savedData);
            debugLog('Successfully loaded structured YAML data', data);
        } catch (yamlError) {
            // Fallback: try parsing as flat JSON/YAML for backward compatibility
            try {
                const flatData = JSON.parse(savedData);
                data = organizeLegacyData(flatData);
                debugLog('Loaded and converted legacy data', data);
            } catch (jsonError) {
                console.error('[YAML AutoSave] Data is neither valid structured YAML nor legacy JSON');
                return;
            }
        }
        
        // Populate form fields from structured data
        populateFormFromStructuredData(data);
        
    } catch (error) {
        console.error('[YAML AutoSave] Error loading saved data:', error);
    }
}

// Convert legacy flat data to structured format
function organizeLegacyData(flatData) {
    const formData = new FormData();
    Object.entries(flatData).forEach(([key, value]) => {
        formData.append(key, value);
    });
    return organizeFormData(formData);
}

// Populate form from structured data
function populateFormFromStructuredData(data) {
    // Populate metadata fields
    if (data.metadata) {
        Object.entries(data.metadata).forEach(([key, value]) => {
            setFormFieldValue(key, value);
        });
    }

    // Populate checklist items
    if (data.checklist_items) {
        Object.entries(data.checklist_items).forEach(([itemId, itemData]) => {
            if (itemData.status) {
                setFormFieldValue(`status-${itemId}`, itemData.status);
            }
            if (itemData.comments) {
                setFormFieldValue(`comments-${itemId}`, itemData.comments);
            }
            if (itemData.time) {
                setFormFieldValue(`time-${itemId}`, itemData.time);
            }
        });
    }
    
    // Populate other fields
    if (data.other) {
        Object.entries(data.other).forEach(([key, value]) => {
            setFormFieldValue(key, value);
        });
    }
}

// Set form field value with proper handling for different input types and display elements
function setFormFieldValue(fieldName, value) {
    const element = document.querySelector(`[name="${fieldName}"]`);
    if (!element) return;
    
    // Handle display elements (span, div, etc.) - set text content
    if (element.tagName === 'SPAN' || element.tagName === 'DIV') {
        element.textContent = value;
        debugLog(`Set display element ${fieldName} to ${value}`);
        return;
    }
    
    if (element.type === 'radio') {
        const radioElement = document.querySelector(
            `[name="${fieldName}"][value="${value}"]`
        );
        if (radioElement) {
            radioElement.checked = true;
            debugLog(`Set radio ${fieldName} to ${value}`);
        }
    } else if (element.type === 'checkbox') {
        element.checked = value === 'on' || value === true;
        debugLog(`Set checkbox ${fieldName} to ${element.checked}`);
    } else if (element.tagName === 'SELECT') {
        element.value = value;
        updateStatusStyling(element);
        debugLog(`Set select ${fieldName} to ${value}`);
    } else {
        element.value = value;
        debugLog(`Set input ${fieldName} to ${value}`);
    }
}

// Update status-specific styling for select elements
function updateStatusStyling(selectElement) {
    if (selectElement.name && selectElement.name.startsWith('status-')) {
        selectElement.classList.remove('status-P', 'status-F', 'status-TBD', 'status-NA');
        if (selectElement.value) {
            selectElement.classList.add(`status-${selectElement.value}`);
        }
    }
}

// Initialize auto-save functionality
function initializeYamlAutoSave() {
    debugLog('Initializing structured YAML auto-save...');
    
    loadSavedData();
    setInterval(autoSaveForm, AUTOSAVE_CONFIG.interval);
    debugLog(`Auto-save interval set to ${AUTOSAVE_CONFIG.interval}ms`);
    
    // Add event listeners for immediate saving on form changes
    const form = document.querySelector('form');
    if (form) {
        // Listen for input changes on all form inputs
        form.addEventListener('input', debouncedAutoSave);
        form.addEventListener('change', debouncedAutoSave);
        
        // Also listen for blur events to catch any missed changes
        form.addEventListener('blur', debouncedAutoSave, true);
        
        debugLog('Added event listeners for immediate saving');
    }
    
    // Add event listeners for status select changes (styling + save)
    document.querySelectorAll('select[name^="status-"]').forEach(select => {
        select.addEventListener('change', function() {
            updateStatusStyling(this);
            debouncedAutoSave(); // Immediate save on status changes
        });
    });
    
    debugLog('Structured YAML auto-save initialized successfully');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeYamlAutoSave);
} else {
    initializeYamlAutoSave();
}

// Export functions for global access
window.YamlAutoSave = {
    save: saveFormAsYaml,
    load: loadSavedData,
    export: exportAsYaml,
    clear: () => {
        if (confirm('Are you sure you want to clear all saved data?')) {
            sessionStorage.removeItem(AUTOSAVE_CONFIG.storageKey);
            debugLog('Saved data cleared');
            alert('Saved data cleared successfully!');
        }
    },
    setDebugMode: (enabled) => { AUTOSAVE_CONFIG.debugMode = enabled; }
};