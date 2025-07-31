/**
 * Read dataset metadata from the backend API endpoint
 */
async function readDsMetadata(dsMetadataPath) {
  try {
    console.log('Fetching ds metadata from:', dsMetadataPath);
    const response = await fetch(dsMetadataPath);
    if (!response.ok) {
      throw new Error(`Failed to fetch ds metadata: ${response.statusText}`);
    }
    
    const dsMetadata = await response.json();
    console.log('Dataset Metadata from API:', dsMetadata);
    return dsMetadata;
  } catch (error) {
    console.error('Error reading dataset metadata:', error);
    return null;
  }
}

/**
 * Populate form fields from the processed ds_metadata structure returned by get_ds_metadata()
 * The backend returns: {dataset_pid, dataset_title, dataset_id, dataset_url}
 *
 * @param {Object} dsMetadata - The processed dataset metadata from backend
 */
function populateFieldsFromDsMetadata(dsMetadata) {
  if (!dsMetadata) {
    console.log('No dsMetadata provided');
    return;
  }

  console.log('Starting field population with processed ds metadata:', dsMetadata);
  
  // Map backend response keys to their corresponding data-key attributes in HTML
  const dataKeys = ['dataset_pid', 'dataset_title', 'dataset_id', 'dataset_url'];
  
  dataKeys.forEach(dataKey => {
    const value = dsMetadata[dataKey];
    
    if (value != null && value !== '') {
      console.log(`Processing ${dataKey}:`, value);
      
      // Find elements with matching data-key attribute
      const elements = document.querySelectorAll(`[data-key="${dataKey}"]`);
      
      elements.forEach(element => {
        console.log(`Found element for ${dataKey}:`, element);
        
        // Set value based on element type
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA' || element.tagName === 'SELECT') {
          element.value = value;
        } else {
          element.textContent = value;
        }
        
        // Add auto-populate class and store in sessionStorage
        element.classList.add('auto-populate');
        sessionStorage.setItem(dataKey, value);
        console.log(`Set ${dataKey} to:`, value);
      });
    }
  });

  // Handle project info from sessionStorage (set during setup)
  const sessionKeys = ['curator_name', 'curator_email', 'ticket_number'];
  
  sessionKeys.forEach(key => {
    const value = sessionStorage.getItem(key);
    if (value) {
      const elements = document.querySelectorAll(`[data-key="${key}"]`);
      elements.forEach(element => {
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA' || element.tagName === 'SELECT') {
          element.value = value;
        } else {
          element.textContent = value;
        }
        element.classList.add('auto-populate');
      });
    }
  });
}

/**
 * Handle dataset metadata loading from session storage or API
 */
function handleDsMetadata() {
  // First try to get ds_metadata directly from sessionStorage (passed from backend during setup)
  const storedDsMetadata = sessionStorage.getItem('ds_metadata');
  
  if (storedDsMetadata) {
    try {
      const dsMetadata = JSON.parse(storedDsMetadata);
      console.log('Loading processed ds metadata from sessionStorage:', dsMetadata);
      populateFieldsFromDsMetadata(dsMetadata);
      return;
    } catch (error) {
      console.error('Error parsing ds_metadata from sessionStorage:', error);
    }
  }
  
  // Fallback to API call if not in sessionStorage
  const parentDir = sessionStorage.getItem('parent_dir') || 'workdir';
  const ticketNumber = sessionStorage.getItem('ticket_number');
  
  if (ticketNumber) {
    const dsMetadataPath = `/ds-metadata/${parentDir}/${ticketNumber}`;
    console.log('Loading ds metadata from API path:', dsMetadataPath);
    
    readDsMetadata(dsMetadataPath)
      .then(dsMetadata => {
        if (dsMetadata) {
          // Store the retrieved metadata in sessionStorage for future use
          sessionStorage.setItem('ds_metadata', JSON.stringify(dsMetadata));
          populateFieldsFromDsMetadata(dsMetadata);
        }
      })
      .catch(error => {
        console.error('Error handling ds metadata:', error);
      });
  } else {
    console.log('No ticket number found in sessionStorage, cannot load dataset metadata');
  }
}

// Auto-run on page load to populate fields from ds_metadata
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM loaded, checking for ds metadata info...');
  handleDsMetadata();
});

// Export functions for use in other scripts
window.readDsMetadata = readDsMetadata;
window.populateFieldsFromDsMetadata = populateFieldsFromDsMetadata;
window.handleDsMetadata = handleDsMetadata;