// Form validation for time inputs
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            const timeInputs = document.querySelectorAll('.time-input[required]');
            let hasErrors = false;
            
            timeInputs.forEach(function(input) {
                const value = input.value.trim();
                
                // Check if required field is empty
                if (!value) {
                    alert('Time Spent field is required for item ID: ' + input.name.replace('time-', ''));
                    input.focus();
                    hasErrors = true;
                    return;
                }
                
                // Check format
                const durationRegex = /^[0-9]{1,2}:[0-5][0-9]$/;
                if (!durationRegex.test(value)) {
                    alert('Please enter duration in MM:SS format (e.g., 02:30, 10:45) for item ID: ' + input.name.replace('time-', ''));
                    input.focus();
                    input.select();
                    hasErrors = true;
                    return;
                }
            });
            
            if (hasErrors) {
                e.preventDefault(); // Prevent form submission
            }
        });
    }
});