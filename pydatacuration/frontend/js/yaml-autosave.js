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
    interval: 10000, // 10 seconds
    storageKey: 'curationLog',
    debugMode: false
};

// Debug logging function
function debugLog(message, data = null) {
    if (AUTOSAVE_CONFIG.debugMode) {
        console.log(`[YAML AutoSave] ${message}`, data || '');
    }
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
    const organized = {
        metadata: {},
        checklist_items: {},
        other: {}
    };
    
    for (const [key, value] of formData.entries()) {
        const itemId = extractItemId(key);
        const fieldType = getFieldType(key);
        
        if (itemId) {
            // This is a checklist item field
            if (!organized.checklist_items[itemId]) {
                organized.checklist_items[itemId] = {};
            }
            organized.checklist_items[itemId][fieldType] = value || '';
        } else if (isMetadataField(key)) {
            // This is a metadata field
            organized.metadata[key] = value || '';
        } else {
            // Other fields (like additional comments)
            organized.other[key] = value || '';
        }
    }
    
    return organized;
}

// Check if field is a metadata field
function isMetadataField(fieldName) {
    const metadataFields = [
        'ticket_number', 'curator_name', 'curator_email', 'dataset_title',
        'dataset_pid', 'dataset_id', 'dataset_url', 'log_initial_date', 'log_updated_date'
    ];
    return metadataFields.includes(fieldName);
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

// Set form field value with proper handling for different input types
function setFormFieldValue(fieldName, value) {
    const element = document.querySelector(`[name="${fieldName}"]`);
    if (!element) return;
    
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

// // Manual save function
// function saveFormAsYaml() {
//     try {
//         autoSaveForm();
//         alert('Form data saved successfully in structured YAML format!');
//     } catch (error) {
//         alert('Error saving form data: ' + error.message);
//     }
// }

// // Get current data as YAML string for export
// function exportAsYaml() {
//     try {
//         const form = document.querySelector('form');
//         if (!form) return '';
        
//         const formData = new FormData(form);
//         const organizedData = organizeFormData(formData);
//         return simpleYamlStringify(organizedData);
//     } catch (error) {
//         console.error('Error exporting YAML:', error);
//         return '';
//     }
// }

// Initialize auto-save functionality
function initializeYamlAutoSave() {
    debugLog('Initializing structured YAML auto-save...');
    
    loadSavedData();
    setInterval(autoSaveForm, AUTOSAVE_CONFIG.interval);
    debugLog(`Auto-save interval set to ${AUTOSAVE_CONFIG.interval}ms`);
    
    // Add event listeners for status select changes
    document.querySelectorAll('select[name^="status-"]').forEach(select => {
        select.addEventListener('change', function() {
            updateStatusStyling(this);
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