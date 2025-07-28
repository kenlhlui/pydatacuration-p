// Form validation for time inputs and status selection
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    
    if (form) {
        form.addEventListener('submit', async function(e) {
            let hasErrors = false;
            
            // Validate time inputs
            const timeInputs = document.querySelectorAll('.time-input[required]');
            timeInputs.forEach(function(input) {
                const value = input.value.trim();
                
                if (!value) {
                    alert('Time Spent field is required for item ID: ' + input.name.replace('time-', ''));
                    input.focus();
                    hasErrors = true;
                    return;
                }
                
                const durationRegex = /^[0-9]{1,2}:[0-5][0-9]$/;
                if (!durationRegex.test(value)) {
                    alert('Please enter duration in HH:MM format (e.g., 02:30, 10:45) for item ID: ' + input.name.replace('time-', ''));
                    input.focus();
                    input.select();
                    hasErrors = true;
                    return;
                }
            });
            
            // Validate status selections (FIXED FOR DROPDOWNS)
            const statusSelects = document.querySelectorAll('.status-select[required]');
            statusSelects.forEach(function(select) {
                if (!select.value) {
                    const itemId = select.name.replace('status-', '');
                    alert('Please select a status for item ID: ' + itemId);
                    select.focus();
                    hasErrors = true;
                    return;
                }
            });
            
            // If there are validation errors, prevent form export
            if (hasErrors) {
                e.preventDefault();
            }
            // If no errors, proceed with form export
            else {
                // Prevent immediate submission for delay
                e.preventDefault();
                
                // Show success message and loading state
                const submitButton = document.querySelector('button[type="submit"]');
                const originalText = submitButton.textContent;
                submitButton.textContent = 'Saving...';
                submitButton.disabled = true;
                
                // Add a green bar to indicate successful validation
                const successMessage = document.createElement('div');
                successMessage.style.position = 'fixed';
                successMessage.style.top = '10px';
                successMessage.style.left = '50%';
                successMessage.style.transform = 'translateX(-50%)';
                successMessage.style.backgroundColor = '#d4edda';
                successMessage.style.color = '#155724';
                successMessage.style.padding = '15px 25px';
                successMessage.style.border = '1px solid #c3e6cb';
                successMessage.style.borderRadius = '5px';
                successMessage.style.zIndex = '1000';
                successMessage.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
                successMessage.textContent = 'Checklist input validated successfully! Exporting the checklist to a docx file...';
                document.body.appendChild(successMessage);
                
                // Sleep for 2 seconds
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Remove success message and submit form
                successMessage.remove();
                form.submit();
            }
        });
    }
});

// Color status dropdowns based on selection
document.addEventListener('DOMContentLoaded', function() {
    const statusSelects = document.querySelectorAll('.status-select');
    
    statusSelects.forEach(function(select) {
        // Apply color on change
        select.addEventListener('change', function() {
            // Remove all status classes
            select.classList.remove('status-P', 'status-F', 'status-TBD', 'status-NA');
            
            // Add class for selected value
            if (this.value) {
                select.classList.add('status-' + this.value);
            }
        });
        
        // Apply color if already has a value (for loaded data)
        if (select.value) {
            select.classList.add('status-' + select.value);
        }
    });
});