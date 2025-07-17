// sessionstorage.js
document.addEventListener('DOMContentLoaded', () => {
  // pick the fields you want to sync by either id or name
  const fields = Array.from(
    document.querySelectorAll('input[id], textarea[id], select[id]')
  ).filter((el) => el.id !== 'api_token'); // Exclude the API token field

  fields.forEach((el) => {
    // use el.id (or you could use el.name) as the sessionStorage key
    const key = el.id;
    // 1) load from sessionStorage (if present)
    const stored = sessionStorage.getItem(key);
    if (stored !== null) {
      el.value = stored;
      el.classList.add('pre-filled');
    } else if (el.value) {
      // 2) if nothing in storage but the field has a value (prepopulated), seed it
      sessionStorage.setItem(key, el.value);
    }

    // 3) whenever user edits, keep storage up to date
    el.addEventListener('input', () => {
      sessionStorage.setItem(key, el.value);
    });

    // if you have <select> you might also:
    if (el.tagName === 'SELECT') {
      el.addEventListener('change', () => {
        sessionStorage.setItem(key, el.value);
      });
    }
  });
});
