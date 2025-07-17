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

// Load saved values from sessionStorage
document.addEventListener('DOMContentLoaded', function() {
    const savedPid = sessionStorage.getItem('pid');
    const savedTicketNumber = sessionStorage.getItem('ticket_number');
    const savedBaseUrl = sessionStorage.getItem('base_url');
    if (savedPid) {
        document.getElementById('pid').value = savedPid;
    }
    if (savedTicketNumber) {
        document.getElementById('ticket_number').value = savedTicketNumber;
    }
    if (savedBaseUrl) {
        document.getElementById('base_url').value = savedBaseUrl;
    }
});