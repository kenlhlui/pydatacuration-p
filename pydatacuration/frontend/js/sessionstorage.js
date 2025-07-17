// sessionstorage.js

// Save the input of PID, ticket number and base URL to sessionStorage
// so that the checklist page can access them
document.getElementById('pid').addEventListener('input', function() {
    sessionStorage.setItem('pid', this.value);
});
document.getElementById('ticket_number').addEventListener('input', function() {
    sessionStorage.setItem('ticket_number', this.value);
});
document.getElementById('base_url').addEventListener('input', function() {
    sessionStorage.setItem('base_url', this.value);
});
document.getElementById('curator_name').addEventListener('input', function() {
    sessionStorage.setItem('curator_name', this.value);
});
document.getElementById('curator_email').addEventListener('input', function() {
    sessionStorage.setItem('curator_email', this.value);
});

// Load saved values from sessionStorage
document.addEventListener('DOMContentLoaded', function() {
    const savedPid = sessionStorage.getItem('pid');
    const savedTicketNumber = sessionStorage.getItem('ticket_number');
    const savedBaseUrl = sessionStorage.getItem('base_url');
    const savedCuratorName = sessionStorage.getItem('curator_name');
    const savedCuratorEmail = sessionStorage.getItem('curator_email');
    if (savedPid) {
        document.getElementById('pid').value = savedPid;
    }
    if (savedTicketNumber) {
        document.getElementById('ticket_number').value = savedTicketNumber;
    }
    if (savedBaseUrl) {
        document.getElementById('base_url').value = savedBaseUrl;
    }
    if (savedCuratorName) {
        document.getElementById('curator_name').value = savedCuratorName;
    }
    if (savedCuratorEmail) {
        document.getElementById('curator_email').value = savedCuratorEmail;
    }
});

// Automatically save form fields to sessionStorage
// document.addEventListener('DOMContentLoaded', () => {
//   // select all form fields that have a "name"
//   const fields = document.querySelectorAll('input[name], textarea[name], select[name]');

//   fields.forEach((el) => {
//     const key = el.name;
//     // 1) load saved value (if any)
//     const saved = sessionStorage.getItem(key);
//     if (saved !== null) {
//       el.value = saved;
//       el.classList.add('pre-filled');
//     }
//     // 2) watch for changes and save
//     el.addEventListener('input', () => {
//       sessionStorage.setItem(key, el.value);
//     });
//   });
// });
