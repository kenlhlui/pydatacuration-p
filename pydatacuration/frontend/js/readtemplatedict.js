/**
 * Read template dictionary from JSONResponse and populate form fields
 */
async function readTemplateDict(templateDictPath) {
  try {
    console.log('Fetching template dict from:', templateDictPath);
    const response = await fetch(templateDictPath);
    if (!response.ok) {
      throw new Error(`Failed to fetch template dict: ${response.statusText}`);
    }
    
    const templateDict = await response.json();
    console.log('Template Dictionary:', templateDict);
    return templateDict;
  } catch (error) {
    console.error('Error reading template dictionary:', error);
    return null;
  }
}

/**
 * Populate form fields from nested templateDict sections.
 *
 * @param {Object} templateDict - The full JSON with sub-objects.
 */
function populateFieldsFromTemplateDict(templateDict) {
  if (!templateDict) {
    console.log('No templateDict provided');
    return;
  }

  console.log('Starting field population with:', templateDict);

  // Map template dict keys to form field names of template_dict.json
  const sectionMappings = {
    project_info: {
      curator_name:  'curator_name',
      curator_email: 'curator_email',
      ticket_number: 'ticket_number'
    },
    dataset_info: {
      DatasetTitle:        'dataset_title',
      DatasetPersistentId: 'dataset_pid',
      ID:                  'dataset_id',
      DatasetURL:          'dataset_url'
    }
    // add more sections here if needed
  };

  Object.entries(sectionMappings).forEach(([sectionKey, fieldMappings]) => {
    const section = templateDict[sectionKey];
    console.log(`Section ${sectionKey}:`, section);

    if (typeof section !== 'object' || section == null) {
      console.log(`No ${sectionKey} found, skipping`);
      return;
    }

    // For each mapping in that section
    Object.entries(fieldMappings).forEach(([templateKey, fieldName]) => {
      const value = section[templateKey];
      console.log(`Checking ${sectionKey}.${templateKey} -> ${fieldName}:`, value);

      if (value != null) {
        const field = document.querySelector(`[name="${fieldName}"]`);
        console.log(`Field [name="${fieldName}"]`, field, 'current value:', field?.value);

        if (field) {
          field.value = value;
          field.classList.add('pre-filled');
          sessionStorage.setItem(fieldName, value);
          console.log(`Set ${fieldName} to:`, value);
        } else {
          console.log(`Field [name="${fieldName}"] not found`);
        }
      }
    });
  });
}

/**
 * Handle template dictionary loading from setup response
 */
function handleTemplateDict(response) {
  if (response.template_dict_path) {
    readTemplateDict(response.template_dict_path)
      .then(templateDict => {
        if (templateDict) {
          populateFieldsFromTemplateDict(templateDict);
        }
      })
      .catch(error => {
        console.error('Error handling template dict:', error);
      });
  }
}

// Auto-run on page load to check for template dict info
document.addEventListener('DOMContentLoaded', () => {
  // Check if there's template dict info in sessionStorage from the setup process
  const templateDictPath = sessionStorage.getItem('template_dict_path');
  if (templateDictPath) {
    console.log('Found template dict path in sessionStorage:', templateDictPath);
    handleTemplateDict({ template_dict_path: templateDictPath });
    // Clear it after use
    sessionStorage.removeItem('template_dict_path');
  }
});

// Export functions for use in other scripts
window.readTemplateDict = readTemplateDict;
window.populateFieldsFromTemplateDict = populateFieldsFromTemplateDict;
window.handleTemplateDict = handleTemplateDict;