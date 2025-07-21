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
 * Populate form fields with template dictionary data
 */
function populateFieldsFromTemplateDict(templateDict) {
  if (!templateDict) return;

  // Map template dict keys to form field names
  const fieldMappings = {
    'dataset_title': 'dataset_title',
    'dataset_pid': 'dataset_pid', 
    'dataset_id': 'dataset_id',
    'dataset_url': 'dataset_url',
    'log_generated_date': 'log_generated_date',
    'log_updated_date': 'log_updated_date'
  };

  Object.entries(fieldMappings).forEach(([templateKey, fieldName]) => {
    if (templateDict[templateKey]) {
      const field = document.querySelector(`[name="${fieldName}"]`);
      if (field && !field.value) { // Only populate if field is empty
        field.value = templateDict[templateKey];
        field.classList.add('pre-filled');
        // Save to sessionStorage to maintain consistency with readsessionstorage.js
        sessionStorage.setItem(fieldName, templateDict[templateKey]);
      }
    }
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