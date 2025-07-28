// Form validation for time inputs and status selection
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    
    if (form) {
        form.addEventListener('submit', function(e) {
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
            
            // Validate status selections
            const statusGroups = document.querySelectorAll('input[name^="status-"]:first-of-type');
            statusGroups.forEach(function(firstRadio) {
                const groupName = firstRadio.name;
                const selectedStatus = document.querySelector(`input[name="${groupName}"]:checked`);
                
                if (!selectedStatus) {
                    const itemId = groupName.replace('status-', '');
                    alert('Please select a status for item ID: ' + itemId);
                    firstRadio.focus();
                    hasErrors = true;
                    return;
                }
            });
            
            if (hasErrors) {
                e.preventDefault();
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