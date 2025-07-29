// 1) Validation helper for form export (global scope):
function validateAllInputs() {
    let hasErrors = false;

    // Time inputs
    document.querySelectorAll('.time-input[required]').forEach(input => {
      const v = input.value.trim();
      if (!v || !/^[0-9]{1,2}:[0-5][0-9]$/.test(v)) {
        alert('Item ' + input.name.replace('time-', '') +
              ': please enter time in MM:SS.');
        input.focus();
        hasErrors = true;
        return;
      }
    });

    // Status selects
    document.querySelectorAll('.status-select[required]').forEach(select => {
      if (!select.value) {
        const id = select.name.replace('status-', '');
        alert('Item ' + id + ': please select a status.');
        select.focus();
        hasErrors = true;
        return;
      }
    });

    return !hasErrors;
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form');
  const calculateBtn = document.querySelector('button.btn-calculate-time');

  // 2) Calculate-only button: first validate time inputs, then sum
  if (calculateBtn) {
    calculateBtn.addEventListener('click', () => {
        const timeInputs = document.querySelectorAll('.time-input[required]');
        const durationRegex = /^[0-9]{1,2}:[0-5][0-9]$/;
        let totalMins = 0;

        // 1) Validate each required time input
        for (let input of timeInputs) {
        const v = input.value.trim();
        const id = input.name.replace('time-', '');

        if (!v) {
            alert(`Item ${id}: Time Spent input is required.`);
            input.focus();
            return;           // stop here if empty
        }

        if (!durationRegex.test(v)) {
            alert(`Item ${id}: enter time in MM:SS format (e.g. 02:30).`);
            input.focus();
            input.select();
            return;           // stop here if wrong format
        }
        }

        // 2) If all valid, sum them up
        timeInputs.forEach(input => {
        const [h, m] = input.value.split(':').map(Number);
        totalMins += h * 60 + m;
        });

        const hours = Math.floor(totalMins / 60);
        const mins  = (totalMins % 60).toString().padStart(2, '0');
        alert(`Total Time Spent: ${hours}:${mins}`);
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