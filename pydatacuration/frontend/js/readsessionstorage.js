document.addEventListener('DOMContentLoaded', () => {
  // select all form fields that have a "name"
  const fields = document.querySelectorAll('input[name], textarea[name], select[name]');
  console.log('Found form fields:', fields);

  fields.forEach((el) => {
    const key = el.name;
    // 1) load saved value (if any)
    const saved = sessionStorage.getItem(key);
    if (saved !== null) {
      el.value = saved;
      el.classList.add('auto-populate');
    }
    // 2) watch for changes and save
    el.addEventListener('input', () => {
      sessionStorage.setItem(key, el.value);
      console.log(`Saved ${key} to sessionStorage:`, el.value);
    });
  });
});
